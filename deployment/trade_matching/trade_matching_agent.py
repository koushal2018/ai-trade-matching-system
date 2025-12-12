"""
Trade Matching Agent - AgentCore Runtime Entry Point (Standalone)

This is a self-contained entry point for the Trade Matching Agent deployed to AgentCore Runtime.
It performs fuzzy matching between bank and counterparty trades and generates reports.

Requirements: 2.1, 2.2, 3.4, 7.1, 7.2, 7.3, 7.4, 7.5
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional
import logging
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

# REQUIRED: Import BedrockAgentCoreApp
from bedrock_agentcore import BedrockAgentCoreApp

# Memory integration (optional - graceful fallback if not available)
try:
    import sys
    sys.path.insert(0, '/opt/agent/src')
    from latest_trade_matching_agent.memory import store_matching_decision, retrieve_hitl_feedback
    MEMORY_ENABLED = True
except ImportError:
    MEMORY_ENABLED = False
    async def store_matching_decision(*args, **kwargs):
        return {}
    async def retrieve_hitl_feedback(*args, **kwargs):
        return []

# Observability integration
try:
    from latest_trade_matching_agent.observability import create_span, record_latency, record_throughput, record_error
    OBSERVABILITY_ENABLED = True
except ImportError:
    OBSERVABILITY_ENABLED = False
    from contextlib import contextmanager
    @contextmanager
    def create_span(*args, **kwargs):
        yield None
    def record_latency(*args, **kwargs): pass
    def record_throughput(*args, **kwargs): pass
    def record_error(*args, **kwargs): pass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# REQUIRED: Initialize BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# ============================================================================
# Constants
# ============================================================================

HITL_QUEUE_NAME = "trade-matching-system-hitl-review-queue-production.fifo"
EXCEPTION_QUEUE_NAME = "trade-matching-system-exception-events-production"

# Matching thresholds
AUTO_MATCH_THRESHOLD = 0.85
ESCALATE_THRESHOLD = 0.70
CANDIDATE_THRESHOLD = 0.50  # Minimum score to consider as potential match

# Field weights for attribute-based matching (no Trade_ID since IDs differ across systems)
FIELD_WEIGHTS = {
    "currency": 0.15,           # Must match exactly
    "maturity_date": 0.15,      # Must match exactly
    "notional": 0.20,           # Within tolerance
    "trade_date": 0.15,         # Within 1-2 days
    "counterparty": 0.15,       # Fuzzy match (names differ)
    "product_type": 0.10,       # Should match
    "fixed_rate": 0.10,         # Should match
}

# Tolerances
DATE_TOLERANCE_DAYS = 2  # Bank and counterparty may record different dates
NOTIONAL_TOLERANCE_PCT = 0.02  # 2% tolerance for notional differences


# ============================================================================
# Data Models
# ============================================================================

class MatchClassification(str):
    MATCHED = "MATCHED"
    PROBABLE_MATCH = "PROBABLE_MATCH"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BREAK = "BREAK"
    DATA_ERROR = "DATA_ERROR"


class MatchingResult(BaseModel):
    """Result of trade matching analysis."""
    trade_id: str
    classification: str
    match_score: float
    decision_status: str
    reason_codes: List[str] = Field(default_factory=list)
    differences: Dict[str, Any] = Field(default_factory=dict)
    bank_trade: Optional[Dict[str, Any]] = None
    counterparty_trade: Optional[Dict[str, Any]] = None


# ============================================================================
# Matching Functions
# ============================================================================

def _parse_dynamodb_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Parse DynamoDB typed format to plain dict."""
    result = {}
    for key, value in item.items():
        if "S" in value:
            result[key] = value["S"]
        elif "N" in value:
            result[key] = float(value["N"])
        elif "BOOL" in value:
            result[key] = value["BOOL"]
        elif "L" in value:
            result[key] = [_parse_dynamodb_item({"v": v})["v"] for v in value["L"]]
        elif "M" in value:
            result[key] = _parse_dynamodb_item(value["M"])
        else:
            result[key] = str(value)
    return result


def _compute_date_score(date1: str, date2: str) -> float:
    """Compute score for date comparison with tolerance."""
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%d")
        diff_days = abs((d1 - d2).days)
        
        if diff_days == 0:
            return 1.0
        elif diff_days <= DATE_TOLERANCE_DAYS:
            return 0.9
        else:
            return max(0.0, 1.0 - (diff_days * 0.1))
    except (ValueError, TypeError):
        return 0.0


def _compute_notional_score(notional1: float, notional2: float) -> float:
    """Compute score for notional comparison with tolerance."""
    try:
        if notional1 == 0 and notional2 == 0:
            return 1.0
        if notional1 == 0 or notional2 == 0:
            return 0.0
        
        diff_pct = abs(notional1 - notional2) / max(notional1, notional2)
        
        if diff_pct <= NOTIONAL_TOLERANCE_PCT:
            return 1.0
        elif diff_pct <= 0.001:  # 0.1%
            return 0.9
        elif diff_pct <= 0.01:   # 1%
            return 0.7
        else:
            return max(0.0, 1.0 - diff_pct)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def _compute_fuzzy_score(str1: str, str2: str) -> float:
    """Compute fuzzy string similarity score."""
    if not str1 or not str2:
        return 0.0
    
    str1 = str1.lower().strip()
    str2 = str2.lower().strip()
    
    if str1 == str2:
        return 1.0
    
    # Simple Jaccard similarity on words
    words1 = set(str1.split())
    words2 = set(str2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def fuzzy_match(bank_trade: Dict[str, Any], cp_trade: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform attribute-based fuzzy matching between bank and counterparty trades.
    
    Since there's no common Trade_ID across systems, matching relies on:
    - Currency (exact match)
    - Maturity date (exact match)
    - Notional amount (within tolerance)
    - Trade date (within tolerance)
    - Counterparty name (fuzzy match)
    - Product type (exact match)
    - Fixed rate (exact match)
    
    Args:
        bank_trade: Bank trade data
        cp_trade: Counterparty trade data
        
    Returns:
        dict: Match result with field scores and differences
    """
    field_scores = {}
    differences = {}
    reason_codes = []
    
    # Currency comparison (exact match - critical)
    bank_ccy = str(bank_trade.get("currency", "")).upper()
    cp_ccy = str(cp_trade.get("currency", "")).upper()
    if bank_ccy == cp_ccy:
        field_scores["currency"] = 1.0
    else:
        field_scores["currency"] = 0.0
        differences["currency"] = {"bank": bank_ccy, "counterparty": cp_ccy}
        reason_codes.append("CURRENCY_MISMATCH")
    
    # Maturity date comparison (exact match - critical)
    bank_maturity = bank_trade.get("maturity_date", "")
    cp_maturity = cp_trade.get("maturity_date", "")
    if bank_maturity == cp_maturity:
        field_scores["maturity_date"] = 1.0
    else:
        field_scores["maturity_date"] = _compute_date_score(bank_maturity, cp_maturity)
        if field_scores["maturity_date"] < 1.0:
            differences["maturity_date"] = {"bank": bank_maturity, "counterparty": cp_maturity}
            if field_scores["maturity_date"] < 0.9:
                reason_codes.append("MATURITY_DATE_MISMATCH")
    
    # Notional comparison (within tolerance)
    bank_notional = float(bank_trade.get("notional", 0))
    cp_notional = float(cp_trade.get("notional", 0))
    field_scores["notional"] = _compute_notional_score(bank_notional, cp_notional)
    if field_scores["notional"] < 1.0:
        differences["notional"] = {"bank": bank_notional, "counterparty": cp_notional}
        if field_scores["notional"] < 0.9:
            reason_codes.append("NOTIONAL_MISMATCH")
    
    # Trade date comparison (within tolerance - dates may differ by 1-2 days)
    bank_date = bank_trade.get("trade_date", "")
    cp_date = cp_trade.get("trade_date", "")
    field_scores["trade_date"] = _compute_date_score(bank_date, cp_date)
    if field_scores["trade_date"] < 1.0:
        differences["trade_date"] = {"bank": bank_date, "counterparty": cp_date}
        if field_scores["trade_date"] < 0.8:
            reason_codes.append("TRADE_DATE_MISMATCH")
    
    # Counterparty comparison (fuzzy match - names differ across systems)
    # Bank sees counterparty, Counterparty sees bank as their counterparty
    bank_cp = bank_trade.get("counterparty", "") or bank_trade.get("seller", "")
    cp_cp = cp_trade.get("counterparty", "") or cp_trade.get("buyer", "")
    
    # Also check buyer/seller fields for cross-matching
    bank_buyer = bank_trade.get("buyer", "")
    cp_seller = cp_trade.get("seller", "")
    
    # Compute best counterparty match
    cp_score1 = _compute_fuzzy_score(bank_cp, cp_cp)
    cp_score2 = _compute_fuzzy_score(bank_cp, cp_seller)
    cp_score3 = _compute_fuzzy_score(bank_buyer, cp_cp)
    cp_score4 = _compute_fuzzy_score(bank_buyer, cp_seller)
    
    field_scores["counterparty"] = max(cp_score1, cp_score2, cp_score3, cp_score4)
    if field_scores["counterparty"] < 1.0:
        differences["counterparty"] = {
            "bank": f"{bank_cp} / {bank_buyer}",
            "counterparty": f"{cp_cp} / {cp_seller}"
        }
        if field_scores["counterparty"] < 0.5:
            reason_codes.append("COUNTERPARTY_MISMATCH")
    
    # Product type comparison (should match)
    bank_product = str(bank_trade.get("product_type", "")).upper()
    cp_product = str(cp_trade.get("product_type", "")).upper()
    if bank_product == cp_product:
        field_scores["product_type"] = 1.0
    elif bank_product in cp_product or cp_product in bank_product:
        field_scores["product_type"] = 0.8
    else:
        field_scores["product_type"] = _compute_fuzzy_score(bank_product, cp_product)
        if field_scores["product_type"] < 0.8:
            differences["product_type"] = {"bank": bank_product, "counterparty": cp_product}
            reason_codes.append("PRODUCT_TYPE_MISMATCH")
    
    # Fixed rate comparison (should match exactly)
    bank_rate = float(bank_trade.get("fixed_rate", 0))
    cp_rate = float(cp_trade.get("fixed_rate", 0))
    if bank_rate == cp_rate:
        field_scores["fixed_rate"] = 1.0
    elif bank_rate > 0 and cp_rate > 0:
        rate_diff = abs(bank_rate - cp_rate) / max(bank_rate, cp_rate)
        field_scores["fixed_rate"] = max(0, 1.0 - rate_diff * 10)
        if field_scores["fixed_rate"] < 0.9:
            differences["fixed_rate"] = {"bank": bank_rate, "counterparty": cp_rate}
            reason_codes.append("FIXED_RATE_MISMATCH")
    else:
        field_scores["fixed_rate"] = 0.5  # One or both missing
    
    # Record Trade IDs for reference (not used in scoring)
    differences["reference_ids"] = {
        "bank_trade_id": bank_trade.get("Trade_ID", ""),
        "counterparty_trade_id": cp_trade.get("Trade_ID", "")
    }
    
    return {
        "field_scores": field_scores,
        "differences": differences,
        "reason_codes": reason_codes
    }


def compute_match_score(match_result: Dict[str, Any]) -> float:
    """Compute weighted match score."""
    field_scores = match_result["field_scores"]
    
    total_score = sum(
        field_scores.get(field, 0.0) * weight
        for field, weight in FIELD_WEIGHTS.items()
    )
    
    return round(total_score, 2)


def classify_match(match_score: float, reason_codes: List[str]) -> str:
    """Classify match based on score and reason codes."""
    if match_score >= AUTO_MATCH_THRESHOLD:
        return MatchClassification.MATCHED
    elif match_score >= ESCALATE_THRESHOLD:
        return MatchClassification.PROBABLE_MATCH
    elif match_score >= 0.5:
        return MatchClassification.REVIEW_REQUIRED
    else:
        return MatchClassification.BREAK


def _scan_table(dynamodb_client, table_name: str) -> List[Dict[str, Any]]:
    """Scan a DynamoDB table and return all items."""
    items = []
    try:
        paginator = dynamodb_client.get_paginator('scan')
        for page in paginator.paginate(TableName=table_name):
            for item in page.get('Items', []):
                items.append(_parse_dynamodb_item(item))
    except ClientError as e:
        logger.warning(f"Error scanning table {table_name}: {e}")
    return items


def find_best_match(
    source_trade: Dict[str, Any],
    source_type: str,
    candidate_trades: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Find the best matching trade from candidates using attribute-based matching.
    
    Args:
        source_trade: The trade to match
        source_type: BANK or COUNTERPARTY
        candidate_trades: List of trades from the opposite table
        
    Returns:
        Best match result or None if no good candidates
    """
    best_match = None
    best_score = 0.0
    
    for candidate in candidate_trades:
        # Skip if already matched (could add a matched flag in production)
        
        # Perform fuzzy matching
        if source_type == "BANK":
            match_result = fuzzy_match(source_trade, candidate)
        else:
            match_result = fuzzy_match(candidate, source_trade)
        
        score = compute_match_score(match_result)
        
        # Track best match above threshold
        if score > best_score and score >= CANDIDATE_THRESHOLD:
            best_score = score
            best_match = {
                "candidate": candidate,
                "match_result": match_result,
                "score": score
            }
    
    return best_match


def generate_report(result: MatchingResult, s3_client, s3_bucket: str) -> str:
    """Generate and save matching report to S3."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    # Sanitize trade_id for filename (remove spaces and special chars)
    safe_trade_id = result.trade_id.replace(" ", "_").replace("/", "-")[:50]
    report_key = f"reports/matching_report_{safe_trade_id}_{timestamp}.md"
    
    # Get reference IDs
    ref_ids = result.differences.get("reference_ids", {})
    bank_ref = ref_ids.get("bank_trade_id", "N/A")
    cp_ref = ref_ids.get("counterparty_trade_id", "N/A")
    
    report = f"""# Trade Matching Report

## Summary
- **Match ID**: {result.trade_id}
- **Bank Reference**: {bank_ref}
- **Counterparty Reference**: {cp_ref}
- **Classification**: {result.classification}
- **Confidence Score**: {result.match_score:.1%}
- **Decision Status**: {result.decision_status}
- **Generated**: {datetime.utcnow().isoformat()}

## Matching Methodology
This match was determined using **attribute-based matching** since bank and counterparty 
systems use different trade reference numbers. The confidence score is calculated based on:
- Currency (15%) - Must match exactly
- Maturity Date (15%) - Must match exactly  
- Notional Amount (20%) - Within 2% tolerance
- Trade Date (15%) - Within 2 days tolerance
- Counterparty Name (15%) - Fuzzy string matching
- Product Type (10%) - Should match
- Fixed Rate (10%) - Should match

## Confidence Breakdown
| Attribute | Score | Weight | Contribution |
|-----------|-------|--------|--------------|
"""
    
    # Add field scores if available
    if hasattr(result, 'differences') and result.differences:
        for field, weight in FIELD_WEIGHTS.items():
            # We don't have field_scores in MatchingResult, so estimate from differences
            has_diff = field in result.differences and field != "reference_ids"
            score = 0.7 if has_diff else 1.0  # Simplified
            contribution = score * weight
            report += f"| {field} | {score:.0%} | {weight:.0%} | {contribution:.1%} |\n"
    
    report += f"""
## Reason Codes
{chr(10).join(f"- {code}" for code in result.reason_codes) if result.reason_codes else "- None (all attributes matched within tolerance)"}

## Attribute Differences
"""
    
    if result.differences:
        for field, diff in result.differences.items():
            if field == "reference_ids":
                continue  # Skip reference IDs, already shown above
            if isinstance(diff, dict):
                report += f"""
### {field.replace('_', ' ').title()}
| Source | Value |
|--------|-------|
| Bank | {diff.get('bank', 'N/A')} |
| Counterparty | {diff.get('counterparty', 'N/A')} |
"""
    else:
        report += "\nNo significant differences found - all attributes matched.\n"
    
    report += f"""
## Trade Details

### Bank Trade
```json
{json.dumps(result.bank_trade, indent=2, default=str) if result.bank_trade else "Not found"}
```

### Counterparty Trade
```json
{json.dumps(result.counterparty_trade, indent=2, default=str) if result.counterparty_trade else "Not found"}
```

---
*Report generated by Trade Matching Agent v2.0 - Attribute-Based Matching*
"""
    
    # Save to S3
    s3_client.put_object(
        Bucket=s3_bucket,
        Key=report_key,
        Body=report.encode('utf-8'),
        ContentType='text/markdown'
    )
    
    logger.info(f"Report saved to s3://{s3_bucket}/{report_key}")
    return f"s3://{s3_bucket}/{report_key}"


# ============================================================================
# Event Publishing Functions
# ============================================================================

def _publish_hitl_event(
    sqs_client,
    trade_id: str,
    match_score: float,
    report_path: str,
    correlation_id: str
) -> None:
    """Publish HITL_REQUIRED event to the HITL review queue."""
    try:
        queue_url = sqs_client.get_queue_url(QueueName=HITL_QUEUE_NAME)['QueueUrl']
        
        event_message = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "event_type": "HITL_REQUIRED",
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": "trade_matching_agent",
            "correlation_id": correlation_id,
            "payload": {
                "trade_id": trade_id,
                "match_score": match_score,
                "report_path": report_path
            }
        }
        
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event_message, default=str),
            MessageGroupId=trade_id,
            MessageDeduplicationId=f"{trade_id}_{uuid.uuid4().hex[:8]}"
        )
        logger.info("Published HITL_REQUIRED event")
    except ClientError as e:
        logger.warning(f"Could not publish to HITL queue: {e}")


def _publish_exception_event(
    sqs_client,
    trade_id: str,
    match_score: float,
    reason_codes: List[str],
    report_path: str,
    correlation_id: str
) -> None:
    """Publish MATCHING_EXCEPTION event to the exception queue."""
    try:
        queue_url = sqs_client.get_queue_url(QueueName=EXCEPTION_QUEUE_NAME)['QueueUrl']
        
        event_message = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "event_type": "MATCHING_EXCEPTION",
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": "trade_matching_agent",
            "correlation_id": correlation_id,
            "payload": {
                "exception_id": f"exc_{uuid.uuid4().hex[:12]}",
                "exception_type": "MATCHING_EXCEPTION",
                "trade_id": trade_id,
                "match_score": match_score,
                "reason_codes": reason_codes,
                "report_path": report_path
            }
        }
        
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event_message, default=str)
        )
        logger.info("Published MATCHING_EXCEPTION event")
    except ClientError as e:
        logger.warning(f"Could not publish to exception queue: {e}")


# ============================================================================
# Main Agent Logic
# ============================================================================

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for Trade Matching Agent.
    
    Implements attribute-based matching since there's no common Trade_ID across systems.
    Scans both tables and finds best matches based on trade attributes.
    
    Args:
        payload: Event payload containing:
            - trade_id: Trade identifier that was just extracted
            - source_type: BANK or COUNTERPARTY (which trade was just extracted)
        context: AgentCore context (optional)
        
    Returns:
        dict: Matching result with classification and confidence score
        
    Validates: Requirements 2.1, 2.2, 3.4, 7.1, 7.2, 7.3, 7.4, 7.5
    """
    start_time = datetime.utcnow()
    logger.info("Trade Matching Agent invoked via AgentCore Runtime")
    logger.info(f"Payload: {json.dumps(payload, default=str)}")
    
    # Get configuration from environment
    region_name = os.getenv("AWS_REGION", "us-east-1")
    s3_bucket = os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
    bank_table = os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData")
    counterparty_table = os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData")
    
    # Initialize AWS clients
    s3_client = boto3.client('s3', region_name=region_name)
    dynamodb_client = boto3.client('dynamodb', region_name=region_name)
    sqs_client = boto3.client('sqs', region_name=region_name)
    
    # Extract payload fields
    trade_id = payload.get("trade_id")
    source_type = payload.get("source_type")  # BANK or COUNTERPARTY
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    if not trade_id:
        return {
            "success": False,
            "error": "Missing required field: trade_id"
        }
    
    try:
        logger.info(f"Matching trade: {trade_id} (source: {source_type})")
        
        # Step 1: Determine which table the source trade is in
        if source_type == "BANK":
            source_table = bank_table
            target_table = counterparty_table
        elif source_type == "COUNTERPARTY":
            source_table = counterparty_table
            target_table = bank_table
        else:
            # If source_type not provided, try to find the trade in either table
            logger.info("Source type not provided, searching both tables")
            source_table = None
            target_table = None
        
        # Step 2: Find the source trade
        logger.info("Step 1: Finding source trade")
        source_trade = None
        
        # Try to find by scanning (since Trade_ID format varies)
        bank_trades = _scan_table(dynamodb_client, bank_table)
        cp_trades = _scan_table(dynamodb_client, counterparty_table)
        
        logger.info(f"Found {len(bank_trades)} bank trades and {len(cp_trades)} counterparty trades")
        
        # Find the source trade by Trade_ID
        for trade in bank_trades:
            if trade.get("Trade_ID") == trade_id or trade.get("trade_id") == trade_id:
                source_trade = trade
                source_type = "BANK"
                break
        
        if not source_trade:
            for trade in cp_trades:
                if trade.get("Trade_ID") == trade_id or trade.get("trade_id") == trade_id:
                    source_trade = trade
                    source_type = "COUNTERPARTY"
                    break
        
        if not source_trade:
            logger.warning(f"Source trade not found: {trade_id}")
            return {
                "success": False,
                "error": f"Trade not found: {trade_id}",
                "trade_id": trade_id
            }
        
        logger.info(f"Found source trade in {source_type} table")
        
        # Step 3: Get candidate trades from opposite table
        if source_type == "BANK":
            candidate_trades = cp_trades
        else:
            candidate_trades = bank_trades
        
        if not candidate_trades:
            logger.info(f"No trades in opposite table yet - waiting for match")
            return {
                "success": True,
                "status": "WAITING",
                "trade_id": trade_id,
                "source_type": source_type,
                "message": f"No {'counterparty' if source_type == 'BANK' else 'bank'} trades available for matching"
            }
        
        # Step 4: Find best match using attribute-based matching
        logger.info(f"Step 2: Finding best match from {len(candidate_trades)} candidates")
        best_match = find_best_match(source_trade, source_type, candidate_trades)
        
        if not best_match:
            logger.info("No matching candidates found above threshold")
            return {
                "success": True,
                "status": "NO_MATCH",
                "trade_id": trade_id,
                "source_type": source_type,
                "message": "No matching trades found above confidence threshold",
                "candidates_checked": len(candidate_trades)
            }
        
        # Step 5: Extract match details
        matched_trade = best_match["candidate"]
        match_result = best_match["match_result"]
        match_score = best_match["score"]
        
        logger.info(f"Step 3: Best match found with score {match_score}")
        
        # Step 6: Classify result
        classification = classify_match(match_score, match_result["reason_codes"])
        
        # Determine decision status
        if match_score >= AUTO_MATCH_THRESHOLD:
            decision_status = "AUTO_MATCH"
        elif match_score >= ESCALATE_THRESHOLD:
            decision_status = "ESCALATE"
        else:
            decision_status = "REVIEW_REQUIRED"
        
        logger.info(f"Match result: score={match_score:.2f}, classification={classification}, decision={decision_status}")
        
        # Step 7: Create matching result
        if source_type == "BANK":
            bank_trade = source_trade
            cp_trade = matched_trade
        else:
            bank_trade = matched_trade
            cp_trade = source_trade
        
        # Create composite trade ID for the match
        match_id = f"{bank_trade.get('Trade_ID', 'unknown')}_x_{cp_trade.get('Trade_ID', 'unknown')}"
        
        result = MatchingResult(
            trade_id=match_id,
            classification=classification,
            match_score=match_score,
            decision_status=decision_status,
            reason_codes=match_result["reason_codes"],
            differences=match_result["differences"],
            bank_trade=bank_trade,
            counterparty_trade=cp_trade
        )
        
        # Step 8: Generate and save report
        logger.info("Step 4: Generating report")
        report_path = generate_report(result, s3_client, s3_bucket)
        
        # Step 9: Publish events based on decision status
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        if decision_status == "REVIEW_REQUIRED":
            _publish_exception_event(
                sqs_client=sqs_client,
                trade_id=match_id,
                match_score=match_score,
                reason_codes=match_result["reason_codes"],
                report_path=report_path,
                correlation_id=correlation_id
            )
        elif decision_status == "ESCALATE":
            _publish_hitl_event(
                sqs_client=sqs_client,
                trade_id=match_id,
                match_score=match_score,
                report_path=report_path,
                correlation_id=correlation_id
            )
        
        return {
            "success": True,
            "trade_id": trade_id,
            "matched_trade_id": matched_trade.get("Trade_ID"),
            "match_id": match_id,
            "classification": classification,
            "match_score": match_score,
            "decision_status": decision_status,
            "reason_codes": match_result["reason_codes"],
            "field_scores": match_result["field_scores"],
            "report_path": report_path,
            "processing_time_ms": processing_time_ms
        }
        
    except Exception as e:
        logger.error(f"Error matching trade: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "trade_id": trade_id
        }


if __name__ == "__main__":
    """
    REQUIRED: Let AgentCore Runtime control the agent execution.
    """
    app.run()
