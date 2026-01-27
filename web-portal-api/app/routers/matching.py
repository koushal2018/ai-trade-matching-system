from typing import Optional, List, Dict, Any, Tuple
from fastapi import APIRouter, Depends, Query, HTTPException
from boto3.dynamodb.conditions import Attr
from pydantic import BaseModel
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import boto3
from ..models import MatchingResult, MatchClassification, DecisionStatus, Trade
from ..services.dynamodb import db_service
from ..config import settings
from ..auth import get_current_user, optional_auth_or_dev, User

router = APIRouter(prefix="/matching", tags=["matching"])

# DynamoDB client for writing to TradeMatches table
dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)


# Helper function to transform DynamoDB trade to Trade model
def transform_dynamodb_trade_to_model(trade_data: Dict[str, Any]) -> Trade:
    """Transform DynamoDB trade data to Trade model format."""
    return Trade(
        Trade_ID=trade_data.get("trade_id", "UNKNOWN"),
        TRADE_SOURCE=trade_data.get("source", "UNKNOWN"),
        trade_date=trade_data.get("trade_date", ""),
        notional=float(trade_data.get("notional", 0)),
        currency=trade_data.get("currency", ""),
        counterparty=trade_data.get("counterparty", ""),
        product_type=trade_data.get("product", ""),
        effective_date=trade_data.get("effective_date"),
        maturity_date=trade_data.get("settlement_date")  # Map settlement_date to maturity_date
    )


# Matching algorithm helper functions
def calculate_field_match_score(bank_value: Any, cp_value: Any, field_name: str) -> float:
    """Calculate match score for a specific field (0.0 to 1.0)."""
    if bank_value is None or cp_value is None:
        return 0.0 if bank_value != cp_value else 1.0

    # Convert Decimal to float for comparison
    if isinstance(bank_value, Decimal):
        bank_value = float(bank_value)
    if isinstance(cp_value, Decimal):
        cp_value = float(cp_value)

    # Exact match
    if bank_value == cp_value:
        return 1.0

    # Numeric fields - calculate percentage difference
    if isinstance(bank_value, (int, float)) and isinstance(cp_value, (int, float)):
        if bank_value == 0 and cp_value == 0:
            return 1.0
        max_val = max(abs(bank_value), abs(cp_value))
        if max_val == 0:
            return 1.0
        difference = abs(bank_value - cp_value)
        tolerance = max_val * 0.01  # 1% tolerance
        if difference <= tolerance:
            return 1.0
        # Score decreases as difference increases
        return max(0.0, 1.0 - (difference / max_val))

    # String fields - case-insensitive comparison
    if isinstance(bank_value, str) and isinstance(cp_value, str):
        if bank_value.strip().lower() == cp_value.strip().lower():
            return 0.95  # Slightly penalize case differences
        return 0.0

    return 0.0


def compare_trades(bank_trade: Dict[str, Any], cp_trade: Dict[str, Any]) -> Tuple[float, Dict[str, Any], List[str]]:
    """
    Compare bank and counterparty trades.

    Returns:
        Tuple of (match_score, differences_dict, reason_codes)
    """
    # Fields to compare with weights
    field_weights = {
        'notional': 0.35,  # Most important
        'currency': 0.15,
        'trade_date': 0.15,
        'settlement_date': 0.15,
        'product': 0.10,
        'counterparty': 0.10,
    }

    field_scores = {}
    differences = {}

    for field, weight in field_weights.items():
        bank_val = bank_trade.get(field)
        cp_val = cp_trade.get(field)

        score = calculate_field_match_score(bank_val, cp_val, field)
        field_scores[field] = score

        # Record difference if not a perfect match
        if score < 1.0:
            differences[field] = {
                'bank': str(bank_val) if bank_val is not None else None,
                'counterparty': str(cp_val) if cp_val is not None else None,
                'score': round(score, 3)
            }

    # Calculate weighted average
    total_score = sum(score * field_weights[field] for field, score in field_scores.items())

    # Generate reason codes based on differences
    reason_codes = []
    if 'notional' in differences and field_scores['notional'] < 0.99:
        reason_codes.append('NOTIONAL_MISMATCH')
    if 'trade_date' in differences:
        reason_codes.append('DATE_MISMATCH')
    if 'settlement_date' in differences:
        reason_codes.append('SETTLEMENT_DATE_MISMATCH')
    if 'currency' in differences:
        reason_codes.append('CURRENCY_MISMATCH')
    if 'product' in differences:
        reason_codes.append('PRODUCT_TYPE_MISMATCH')
    if 'counterparty' in differences:
        reason_codes.append('COUNTERPARTY_NAME_MISMATCH')

    if not reason_codes:
        reason_codes = ['PERFECT_MATCH']

    return round(total_score, 3), differences, reason_codes


def persist_match_result(result: MatchingResult) -> str:
    """
    Persist matching result to TradeMatches table.

    Args:
        result: MatchingResult to persist

    Returns:
        match_id of the persisted record
    """
    matches_table = dynamodb.Table(settings.dynamodb_matched_table)
    match_id = f"match-{uuid.uuid4()}"

    # Prepare item for DynamoDB (convert to dict and handle types)
    item = {
        'match_id': match_id,
        'trade_id': result.tradeId,
        'classification': result.classification.value,
        'match_score': Decimal(str(result.matchScore)),
        'decision_status': result.decisionStatus.value,
        'reason_codes': result.reasonCodes,
        'differences': result.differences,
        'created_at': result.createdAt,
        'updated_at': datetime.now(timezone.utc).isoformat() + 'Z',
    }

    # Add trade objects if present
    if result.bankTrade:
        item['bank_trade'] = {
            'Trade_ID': result.bankTrade.Trade_ID,
            'TRADE_SOURCE': result.bankTrade.TRADE_SOURCE,
            'trade_date': result.bankTrade.trade_date,
            'notional': Decimal(str(result.bankTrade.notional)),
            'currency': result.bankTrade.currency,
            'counterparty': result.bankTrade.counterparty,
            'product_type': result.bankTrade.product_type,
        }

    if result.counterpartyTrade:
        item['counterparty_trade'] = {
            'Trade_ID': result.counterpartyTrade.Trade_ID,
            'TRADE_SOURCE': result.counterpartyTrade.TRADE_SOURCE,
            'trade_date': result.counterpartyTrade.trade_date,
            'notional': Decimal(str(result.counterpartyTrade.notional)),
            'currency': result.counterpartyTrade.currency,
            'counterparty': result.counterpartyTrade.counterparty,
            'product_type': result.counterpartyTrade.product_type,
        }

    matches_table.put_item(Item=item)
    return match_id


class QueueItem(BaseModel):
    """Queue item for matching processing."""
    queueId: str
    sessionId: str
    tradeId: str
    counterpartyId: str
    status: str  # PENDING, PROCESSING, WAITING, COMPLETED, FAILED
    priority: str  # HIGH, MEDIUM, LOW
    queuedAt: str
    estimatedProcessingTime: int
    sourceType: str
    documentCount: int


@router.get("/results", response_model=list[MatchingResult])
async def get_matching_results(
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    user: Optional[User] = Depends(optional_auth_or_dev)
):
    """Get matching results with optional filtering."""
    try:
        # Try to get data from TradeMatches table
        items = db_service.scan_table(settings.dynamodb_matched_table, limit=100)

        if not items:
            # If TradeMatches is empty, build results from Bank and Counterparty data
            bank_items = db_service.scan_table(settings.dynamodb_bank_table, limit=50)
            cp_items = db_service.scan_table(settings.dynamodb_counterparty_table, limit=50)

            results = []
            # Create matched results from existing trade data
            for bank_trade in bank_items:
                trade_id = bank_trade.get("trade_id", "UNKNOWN")
                internal_ref = bank_trade.get("internal_reference", "")

                # Look for matching counterparty trade (by trade_id and internal_reference)
                matched_cp = next((
                    cp for cp in cp_items
                    if cp.get("trade_id") == trade_id and cp.get("internal_reference") == internal_ref
                ), None)

                if matched_cp:
                    # Found a match - perform detailed comparison
                    match_score, differences, reason_codes = compare_trades(bank_trade, matched_cp)

                    # Determine classification based on match score
                    if match_score >= 0.95:
                        classification = MatchClassification.MATCHED
                        decision_status = DecisionStatus.AUTO_MATCH
                    elif match_score >= 0.80:
                        classification = MatchClassification.REVIEW_REQUIRED
                        decision_status = DecisionStatus.PENDING_REVIEW
                    else:
                        classification = MatchClassification.BREAK
                        decision_status = DecisionStatus.EXCEPTION

                    results.append(MatchingResult(
                        tradeId=trade_id,
                        classification=classification,
                        matchScore=match_score,
                        decisionStatus=decision_status,
                        reasonCodes=reason_codes,
                        differences=differences,
                        createdAt=bank_trade.get("created_at", bank_trade.get("extraction_timestamp", "2025-01-24T00:00:00Z")),
                        bankTrade=transform_dynamodb_trade_to_model(bank_trade),
                        counterpartyTrade=transform_dynamodb_trade_to_model(matched_cp)
                    ))
                else:
                    # Unmatched trade - create a break
                    results.append(MatchingResult(
                        tradeId=trade_id,
                        classification=MatchClassification.BREAK,
                        matchScore=0.0,
                        decisionStatus=DecisionStatus.EXCEPTION,
                        reasonCodes=["NO_COUNTERPARTY_MATCH"],
                        differences={},
                        createdAt=bank_trade.get("created_at", bank_trade.get("extraction_timestamp", "2025-01-24T00:00:00Z")),
                        bankTrade=transform_dynamodb_trade_to_model(bank_trade),
                        counterpartyTrade=None
                    ))

            return results

        # Parse TradeMatches data
        results = []
        for item in items:
            results.append(MatchingResult(
                tradeId=item.get("trade_id", ""),
                classification=MatchClassification(item.get("classification", "MATCHED")),
                matchScore=float(item.get("match_score", 0)),
                decisionStatus=DecisionStatus(item.get("decision_status", "AUTO_MATCH")),
                reasonCodes=item.get("reason_codes", []),
                differences=item.get("differences", {}),
                createdAt=item.get("created_at", ""),
                bankTrade=item.get("bank_trade"),
                counterpartyTrade=item.get("counterparty_trade")
            ))

        return results

    except Exception as e:
        print(f"Error fetching matching results: {e}")
        # Return empty list instead of mock data on error
        return []


@router.get("/queue", response_model=List[QueueItem])
async def get_matching_queue(
    user: Optional[User] = Depends(optional_auth_or_dev)
):
    """Get matching queue items showing pending and in-progress matching requests."""
    try:
        # Query processing status table for active sessions
        import boto3
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        processing_status_table = dynamodb.Table(settings.dynamodb_processing_status_table)

        # Scan processing status table for recent items
        response = processing_status_table.scan(
            Limit=50
        )

        queue_items = []
        for item in response.get('Items', []):
            processing_id = item.get('processing_id', '')
            overall_status = item.get('overallStatus', 'pending')

            # Map processing status to queue status
            if overall_status == 'initializing':
                queue_status = 'PENDING'
            elif overall_status == 'processing':
                queue_status = 'PROCESSING'
            elif overall_status == 'completed':
                queue_status = 'COMPLETED'
            elif overall_status == 'failed':
                queue_status = 'FAILED'
            else:
                queue_status = 'WAITING'

            # Determine priority based on processing time
            created_at = item.get('created_at', item.get('lastUpdated', ''))
            if created_at:
                try:
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    age_minutes = (datetime.now(timezone.utc) - created_time).total_seconds() / 60
                    if age_minutes > 30:
                        priority = 'HIGH'
                    elif age_minutes > 10:
                        priority = 'MEDIUM'
                    else:
                        priority = 'LOW'
                except:
                    priority = 'MEDIUM'
            else:
                priority = 'MEDIUM'

            # Extract trade ID from processing_id (format: session-{uuid}-{filename})
            trade_id = processing_id.split('-')[-1] if '-' in processing_id else 'UNKNOWN'

            # Count documents (bank + counterparty = 2)
            doc_count = 2 if queue_status in ['PROCESSING', 'COMPLETED'] else 1

            queue_items.append(QueueItem(
                queueId=f"queue-{processing_id}",
                sessionId=processing_id,
                tradeId=trade_id,
                counterpartyId='Unknown',
                status=queue_status,
                priority=priority,
                queuedAt=item.get('created_at', item.get('lastUpdated', datetime.now(timezone.utc).isoformat() + 'Z')),
                estimatedProcessingTime=65,  # 65 seconds average
                sourceType='BANK',
                documentCount=doc_count
            ))

        # Sort by priority (HIGH first) then by queued time
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        queue_items.sort(key=lambda x: (priority_order.get(x.priority, 3), x.queuedAt))

        return queue_items

    except Exception as e:
        print(f"Error fetching matching queue: {e}")
        # Return empty list on error
        return []


class BatchMatchResponse(BaseModel):
    """Response model for batch matching operation."""
    success: bool
    message: str
    matchedCount: int
    unmatchedCount: int
    persistedCount: int
    errors: List[str] = []


@router.post("/batch-match", response_model=BatchMatchResponse)
async def batch_match_trades(
    persist: bool = Query(True, description="Whether to persist results to TradeMatches table"),
    user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Perform batch matching of all bank and counterparty trades.

    Calculates match scores for all trade pairs and optionally persists
    results to the TradeMatches table for faster subsequent queries.

    Args:
        persist: Whether to persist results to TradeMatches table (default: True)

    Returns:
        BatchMatchResponse with match statistics
    """
    try:
        # Scan bank and counterparty tables
        bank_items = db_service.scan_table(settings.dynamodb_bank_table, limit=100)
        cp_items = db_service.scan_table(settings.dynamodb_counterparty_table, limit=100)

        matched_count = 0
        unmatched_count = 0
        persisted_count = 0
        errors = []

        # Process each bank trade
        for bank_trade in bank_items:
            try:
                trade_id = bank_trade.get("trade_id", "UNKNOWN")
                internal_ref = bank_trade.get("internal_reference", "")

                # Find matching counterparty trade
                matched_cp = next((
                    cp for cp in cp_items
                    if cp.get("trade_id") == trade_id and cp.get("internal_reference") == internal_ref
                ), None)

                if matched_cp:
                    # Perform comparison
                    match_score, differences, reason_codes = compare_trades(bank_trade, matched_cp)

                    # Determine classification
                    if match_score >= 0.95:
                        classification = MatchClassification.MATCHED
                        decision_status = DecisionStatus.AUTO_MATCH
                    elif match_score >= 0.80:
                        classification = MatchClassification.REVIEW_REQUIRED
                        decision_status = DecisionStatus.PENDING_REVIEW
                    else:
                        classification = MatchClassification.BREAK
                        decision_status = DecisionStatus.EXCEPTION

                    # Create MatchingResult object
                    result = MatchingResult(
                        tradeId=trade_id,
                        classification=classification,
                        matchScore=match_score,
                        decisionStatus=decision_status,
                        reasonCodes=reason_codes,
                        differences=differences,
                        createdAt=bank_trade.get("created_at", bank_trade.get("extraction_timestamp", datetime.now(timezone.utc).isoformat() + "Z")),
                        bankTrade=transform_dynamodb_trade_to_model(bank_trade),
                        counterpartyTrade=transform_dynamodb_trade_to_model(matched_cp)
                    )

                    matched_count += 1

                    # Persist if requested
                    if persist:
                        persist_match_result(result)
                        persisted_count += 1

                else:
                    # Unmatched trade
                    result = MatchingResult(
                        tradeId=trade_id,
                        classification=MatchClassification.BREAK,
                        matchScore=0.0,
                        decisionStatus=DecisionStatus.EXCEPTION,
                        reasonCodes=["NO_COUNTERPARTY_MATCH"],
                        differences={},
                        createdAt=bank_trade.get("created_at", bank_trade.get("extraction_timestamp", datetime.now(timezone.utc).isoformat() + "Z")),
                        bankTrade=transform_dynamodb_trade_to_model(bank_trade),
                        counterpartyTrade=None
                    )

                    unmatched_count += 1

                    # Persist unmatched results too if requested
                    if persist:
                        persist_match_result(result)
                        persisted_count += 1

            except Exception as e:
                errors.append(f"Error processing trade {trade_id}: {str(e)}")
                continue

        message = f"Batch matching complete: {matched_count} matched, {unmatched_count} unmatched"
        if persist:
            message += f", {persisted_count} persisted to TradeMatches table"

        return BatchMatchResponse(
            success=True,
            message=message,
            matchedCount=matched_count,
            unmatchedCount=unmatched_count,
            persistedCount=persisted_count,
            errors=errors
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch matching failed: {str(e)}"
        )
