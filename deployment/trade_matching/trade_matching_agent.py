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

# Field weights for scoring
FIELD_WEIGHTS = {
    "Trade_ID": 0.30,
    "trade_date": 0.20,
    "notional": 0.25,
    "counterparty": 0.15,
    "currency": 0.10
}

# Tolerances
DATE_TOLERANCE_DAYS = 1
NOTIONAL_TOLERANCE_PCT = 0.0001  # 0.01%


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
    Perform fuzzy matching between bank and counterparty trades.
    
    Args:
        bank_trade: Bank trade data
        cp_trade: Counterparty trade data
        
    Returns:
        dict: Match result with field scores and differences
    """
    field_scores = {}
    differences = {}
    reason_codes = []
    
    # Trade ID comparison (exact match required)
    bank_id = bank_trade.get("Trade_ID", "")
    cp_id = cp_trade.get("Trade_ID", "")
    if bank_id == cp_id:
        field_scores["Trade_ID"] = 1.0
    else:
        field_scores["Trade_ID"] = 0.0
        differences["Trade_ID"] = {"bank": bank_id, "counterparty": cp_id}
        reason_codes.append("TRADE_ID_MISMATCH")
    
    # Trade date comparison (±1 day tolerance)
    bank_date = bank_trade.get("trade_date", "")
    cp_date = cp_trade.get("trade_date", "")
    field_scores["trade_date"] = _compute_date_score(bank_date, cp_date)
    if field_scores["trade_date"] < 1.0:
        differences["trade_date"] = {"bank": bank_date, "counterparty": cp_date}
        if field_scores["trade_date"] < 0.9:
            reason_codes.append("DATE_MISMATCH")
    
    # Notional comparison (±0.01% tolerance)
    bank_notional = float(bank_trade.get("notional", 0))
    cp_notional = float(cp_trade.get("notional", 0))
    field_scores["notional"] = _compute_notional_score(bank_notional, cp_notional)
    if field_scores["notional"] < 1.0:
        differences["notional"] = {"bank": bank_notional, "counterparty": cp_notional}
        if field_scores["notional"] < 0.9:
            reason_codes.append("NOTIONAL_MISMATCH")
    
    # Counterparty comparison (fuzzy match)
    bank_cp = bank_trade.get("counterparty", "")
    cp_cp = cp_trade.get("counterparty", "")
    field_scores["counterparty"] = _compute_fuzzy_score(bank_cp, cp_cp)
    if field_scores["counterparty"] < 1.0:
        differences["counterparty"] = {"bank": bank_cp, "counterparty": cp_cp}
        if field_scores["counterparty"] < 0.8:
            reason_codes.append("COUNTERPARTY_MISMATCH")
    
    # Currency comparison (exact match)
    bank_ccy = bank_trade.get("currency", "")
    cp_ccy = cp_trade.get("currency", "")
    if bank_ccy == cp_ccy:
        field_scores["currency"] = 1.0
    else:
        field_scores["currency"] = 0.0
        differences["currency"] = {"bank": bank_ccy, "counterparty": cp_ccy}
        reason_codes.append("CURRENCY_MISMATCH")
    
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
    elif "TRADE_ID_MISMATCH" in reason_codes:
        return MatchClassification.DATA_ERROR
    elif match_score >= 0.5:
        return MatchClassification.REVIEW_REQUIRED
    else:
        return MatchClassification.BREAK


def generate_report(result: MatchingResult, s3_client, s3_bucket: str) -> str:
    """Generate and save matching report to S3."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_key = f"reports/matching_report_{result.trade_id}_{timestamp}.md"
    
    report = f"""# Trade Matching Report

## Summary
- **Trade ID**: {result.trade_id}
- **Classification**: {result.classification}
- **Match Score**: {result.match_score:.2%}
- **Decision Status**: {result.decision_status}
- **Generated**: {datetime.utcnow().isoformat()}

## Reason Codes
{chr(10).join(f"- {code}" for code in result.reason_codes) if result.reason_codes else "- None"}

## Differences
"""
    
    if result.differences:
        for field, diff in result.differences.items():
            report += f"""
### {field}
- Bank: {diff.get('bank', 'N/A')}
- Counterparty: {diff.get('counterparty', 'N/A')}
"""
    else:
        report += "\nNo differences found.\n"
    
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
    
    Args:
        payload: Event payload containing:
            - trade_id: Trade identifier to match
            - source_type: BANK or COUNTERPARTY (which trade was just extracted)
        context: AgentCore context (optional)
        
    Returns:
        dict: Matching result with classification and score
        
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
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    if not trade_id:
        return {
            "success": False,
            "error": "Missing required field: trade_id"
        }
    
    try:
        logger.info(f"Matching trade: {trade_id}")
        
        # Step 1: Retrieve trades from both DynamoDB tables
        logger.info("Step 1: Retrieving trades from DynamoDB")
        
        bank_trade = None
        cp_trade = None
        
        try:
            bank_response = dynamodb_client.get_item(
                TableName=bank_table,
                Key={"Trade_ID": {"S": trade_id}}
            )
            if "Item" in bank_response:
                bank_trade = _parse_dynamodb_item(bank_response["Item"])
                logger.info(f"Bank trade found: {trade_id}")
        except ClientError as e:
            logger.warning(f"Error retrieving bank trade: {e}")
        
        try:
            cp_response = dynamodb_client.get_item(
                TableName=counterparty_table,
                Key={"Trade_ID": {"S": trade_id}}
            )
            if "Item" in cp_response:
                cp_trade = _parse_dynamodb_item(cp_response["Item"])
                logger.info(f"Counterparty trade found: {trade_id}")
        except ClientError as e:
            logger.warning(f"Error retrieving counterparty trade: {e}")
        
        # Step 2: Check if both trades exist
        if not bank_trade and not cp_trade:
            logger.warning(f"No trades found for {trade_id}")
            return {
                "success": False,
                "error": f"No trades found for {trade_id}",
                "trade_id": trade_id
            }
        
        if not bank_trade or not cp_trade:
            # Only one side exists - wait for the other
            missing_side = "BANK" if not bank_trade else "COUNTERPARTY"
            logger.info(f"Waiting for {missing_side} trade for {trade_id}")
            return {
                "success": True,
                "status": "WAITING",
                "trade_id": trade_id,
                "message": f"Waiting for {missing_side} trade"
            }
        
        # Step 3: Perform fuzzy matching
        logger.info("Step 2: Performing fuzzy matching")
        match_result = fuzzy_match(bank_trade, cp_trade)
        
        # Step 4: Compute match score
        logger.info("Step 3: Computing match score")
        match_score = compute_match_score(match_result)
        
        # Step 5: Classify result
        classification = classify_match(match_score, match_result["reason_codes"])
        
        # Determine decision status
        if match_score >= AUTO_MATCH_THRESHOLD:
            decision_status = "AUTO_MATCH"
        elif match_score >= ESCALATE_THRESHOLD:
            decision_status = "ESCALATE"
        else:
            decision_status = "EXCEPTION"
        
        logger.info(f"Match result: score={match_score}, classification={classification}, decision={decision_status}")
        
        # Step 6: Create matching result
        result = MatchingResult(
            trade_id=trade_id,
            classification=classification,
            match_score=match_score,
            decision_status=decision_status,
            reason_codes=match_result["reason_codes"],
            differences=match_result["differences"],
            bank_trade=bank_trade,
            counterparty_trade=cp_trade
        )
        
        # Step 7: Generate and save report
        logger.info("Step 4: Generating report")
        report_path = generate_report(result, s3_client, s3_bucket)
        
        # Step 8: Publish events based on decision status
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        if decision_status == "EXCEPTION":
            _publish_exception_event(
                sqs_client=sqs_client,
                trade_id=trade_id,
                match_score=match_score,
                reason_codes=match_result["reason_codes"],
                report_path=report_path,
                correlation_id=correlation_id
            )
        elif decision_status == "ESCALATE":
            _publish_hitl_event(
                sqs_client=sqs_client,
                trade_id=trade_id,
                match_score=match_score,
                report_path=report_path,
                correlation_id=correlation_id
            )
        
        return {
            "success": True,
            "trade_id": trade_id,
            "classification": classification,
            "match_score": match_score,
            "decision_status": decision_status,
            "reason_codes": match_result["reason_codes"],
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
