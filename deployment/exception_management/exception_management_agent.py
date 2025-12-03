"""
Exception Management Agent - AgentCore Runtime Entry Point (Standalone)

This is a self-contained entry point for the Exception Management Agent deployed to AgentCore Runtime.
It handles errors with intelligent triage, delegation, and RL-based routing.

Requirements: 2.1, 2.2, 3.5, 8.1, 8.2, 8.3, 8.4, 8.5
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

OPS_DESK_QUEUE_NAME = "trade-matching-system-ops-desk-queue-production"
SENIOR_OPS_QUEUE_NAME = "trade-matching-system-senior-ops-queue-production"
COMPLIANCE_QUEUE_NAME = "trade-matching-system-compliance-queue-production"
ENGINEERING_QUEUE_NAME = "trade-matching-system-engineering-queue-production"

# Base severity scores for reason codes
BASE_SEVERITY_SCORES = {
    "NOTIONAL_MISMATCH": 0.8,
    "DATE_MISMATCH": 0.5,
    "COUNTERPARTY_MISMATCH": 0.9,
    "CURRENCY_MISMATCH": 0.6,
    "TRADE_ID_MISMATCH": 0.7,
    "MISSING_FIELD": 0.6,
    "PROCESSING_ERROR": 0.4,
    "PDF_PROCESSING_ERROR": 0.5,
    "EXTRACTION_FAILED": 0.6,
    "MATCHING_EXCEPTION": 0.7
}

# SLA hours by severity
SLA_HOURS = {
    "CRITICAL": 2,
    "HIGH": 4,
    "MEDIUM": 8,
    "LOW": 24
}


# ============================================================================
# Data Models
# ============================================================================

class ExceptionRecord(BaseModel):
    """Record of an exception event."""
    exception_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    trade_id: str
    match_score: Optional[float] = None
    reason_codes: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class TriageResult(BaseModel):
    """Result of exception triage."""
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    routing: Literal["AUTO_RESOLVE", "OPS_DESK", "SENIOR_OPS", "COMPLIANCE", "ENGINEERING"]
    priority: int  # 1 (highest) to 5 (lowest)
    sla_hours: int
    reason: str


class DelegationResult(BaseModel):
    """Result of exception delegation."""
    status: str
    assigned_to: str
    tracking_id: str
    sla_deadline: datetime


# ============================================================================
# Exception Handling Functions
# ============================================================================

def classify_exception(exception: ExceptionRecord) -> str:
    """
    Classify exception based on event type and reason codes.
    
    Args:
        exception: Exception record
        
    Returns:
        str: Exception classification
    """
    event_type = exception.event_type
    reason_codes = exception.reason_codes
    
    if event_type == "PDF_PROCESSING_ERROR":
        return "PROCESSING_ERROR"
    elif event_type == "EXTRACTION_FAILED":
        return "EXTRACTION_ERROR"
    elif event_type == "MATCHING_EXCEPTION":
        if "COUNTERPARTY_MISMATCH" in reason_codes:
            return "COUNTERPARTY_ERROR"
        elif "NOTIONAL_MISMATCH" in reason_codes:
            return "NOTIONAL_ERROR"
        elif "DATE_MISMATCH" in reason_codes:
            return "DATE_ERROR"
        else:
            return "MATCHING_ERROR"
    else:
        return "UNKNOWN_ERROR"


def compute_severity_score(exception: ExceptionRecord) -> float:
    """
    Compute severity score (0.0 to 1.0) based on multiple factors.
    
    Args:
        exception: Exception record
        
    Returns:
        float: Severity score
    """
    # Start with base score from reason codes
    if exception.reason_codes:
        base_scores = [
            BASE_SEVERITY_SCORES.get(code, 0.5)
            for code in exception.reason_codes
        ]
        score = max(base_scores)
    else:
        score = 0.5
    
    # Adjust based on match score (if available)
    if exception.match_score is not None:
        # Lower match score = higher severity
        score = score * (1 - exception.match_score * 0.3)
    
    # Ensure score is in valid range
    return round(min(1.0, max(0.0, score)), 2)


def triage_exception(exception: ExceptionRecord, severity_score: float) -> TriageResult:
    """
    Triage exception based on severity score and reason codes.
    
    Args:
        exception: Exception record
        severity_score: Computed severity score
        
    Returns:
        TriageResult: Triage decision
    """
    reason_codes = exception.reason_codes
    
    # Critical: Counterparty mismatch or very high severity
    if "COUNTERPARTY_MISMATCH" in reason_codes or severity_score >= 0.9:
        return TriageResult(
            severity="CRITICAL",
            routing="SENIOR_OPS",
            priority=1,
            sla_hours=SLA_HOURS["CRITICAL"],
            reason="Critical exception requiring senior operations review"
        )
    
    # High: Notional mismatch or high severity
    if "NOTIONAL_MISMATCH" in reason_codes or severity_score >= 0.7:
        return TriageResult(
            severity="HIGH",
            routing="OPS_DESK",
            priority=2,
            sla_hours=SLA_HOURS["HIGH"],
            reason="High priority exception for operations desk"
        )
    
    # Medium: Date mismatch or moderate severity
    if "DATE_MISMATCH" in reason_codes or severity_score >= 0.5:
        return TriageResult(
            severity="MEDIUM",
            routing="OPS_DESK",
            priority=3,
            sla_hours=SLA_HOURS["MEDIUM"],
            reason="Medium priority exception for operations desk"
        )
    
    # Low: Minor issues or low severity
    if severity_score < 0.3:
        return TriageResult(
            severity="LOW",
            routing="AUTO_RESOLVE",
            priority=4,
            sla_hours=SLA_HOURS["LOW"],
            reason="Low priority exception - auto-resolve candidate"
        )
    
    # Default: Medium priority to ops desk
    return TriageResult(
        severity="MEDIUM",
        routing="OPS_DESK",
        priority=3,
        sla_hours=SLA_HOURS["MEDIUM"],
        reason="Standard exception for operations desk review"
    )


def delegate_exception(
    exception: ExceptionRecord,
    triage_result: TriageResult
) -> DelegationResult:
    """
    Delegate exception to appropriate handler.
    
    Args:
        exception: Exception record
        triage_result: Triage decision
        
    Returns:
        DelegationResult: Delegation details
    """
    tracking_id = f"trk_{uuid.uuid4().hex[:12]}"
    sla_deadline = datetime.utcnow() + timedelta(hours=triage_result.sla_hours)
    
    # Determine assignment based on routing
    if triage_result.routing == "AUTO_RESOLVE":
        assigned_to = "system_auto_resolver"
    elif triage_result.routing == "OPS_DESK":
        assigned_to = "ops_desk_team"
    elif triage_result.routing == "SENIOR_OPS":
        assigned_to = "senior_ops_team"
    elif triage_result.routing == "COMPLIANCE":
        assigned_to = "compliance_team"
    elif triage_result.routing == "ENGINEERING":
        assigned_to = "engineering_team"
    else:
        assigned_to = "ops_desk_team"
    
    return DelegationResult(
        status="DELEGATED",
        assigned_to=assigned_to,
        tracking_id=tracking_id,
        sla_deadline=sla_deadline
    )


# ============================================================================
# Queue Publishing Functions
# ============================================================================

def _get_queue_url_for_routing(sqs_client, routing: str) -> Optional[str]:
    """Get SQS queue URL based on routing decision."""
    queue_name_map = {
        "OPS_DESK": OPS_DESK_QUEUE_NAME,
        "SENIOR_OPS": SENIOR_OPS_QUEUE_NAME,
        "COMPLIANCE": COMPLIANCE_QUEUE_NAME,
        "ENGINEERING": ENGINEERING_QUEUE_NAME
    }
    
    queue_name = queue_name_map.get(routing)
    if not queue_name:
        return None
    
    try:
        response = sqs_client.get_queue_url(QueueName=queue_name)
        return response['QueueUrl']
    except ClientError as e:
        logger.warning(f"Could not get queue URL for {queue_name}: {e}")
        return None


def _publish_to_handler_queue(
    sqs_client,
    exception: ExceptionRecord,
    triage_result: TriageResult,
    delegation: DelegationResult
) -> None:
    """Publish exception to appropriate handler queue."""
    if triage_result.routing == "AUTO_RESOLVE":
        logger.info("Exception marked for auto-resolve, no queue publication needed")
        return
    
    queue_url = _get_queue_url_for_routing(sqs_client, triage_result.routing)
    if not queue_url:
        logger.warning(f"No queue URL found for routing: {triage_result.routing}")
        return
    
    message = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": "EXCEPTION_TRIAGED",
        "timestamp": datetime.utcnow().isoformat(),
        "source_agent": "exception_management_agent",
        "payload": {
            "exception_id": exception.exception_id,
            "trade_id": exception.trade_id,
            "classification": classify_exception(exception),
            "severity": triage_result.severity,
            "priority": triage_result.priority,
            "sla_hours": triage_result.sla_hours,
            "reason_codes": exception.reason_codes,
            "error_message": exception.error_message
        },
        "delegation": {
            "tracking_id": delegation.tracking_id,
            "assigned_to": delegation.assigned_to,
            "sla_deadline": delegation.sla_deadline.isoformat()
        }
    }
    
    try:
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message, default=str)
        )
        logger.info(f"Published exception to {triage_result.routing} queue")
    except ClientError as e:
        logger.error(f"Failed to publish to handler queue: {e}")


# ============================================================================
# Main Agent Logic
# ============================================================================

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for Exception Management Agent.
    
    Args:
        payload: Event payload containing exception details:
            - event_type: Type of exception event
            - trade_id: Trade identifier
            - match_score: Optional match score
            - reason_codes: List of reason codes
            - error_message: Optional error message
        context: AgentCore context (optional)
        
    Returns:
        dict: Triage and delegation result
        
    Validates: Requirements 2.1, 2.2, 3.5, 8.1, 8.2, 8.3, 8.4, 8.5
    """
    start_time = datetime.utcnow()
    logger.info("Exception Management Agent invoked via AgentCore Runtime")
    logger.info(f"Payload: {json.dumps(payload, default=str)}")
    
    # Get configuration from environment
    region_name = os.getenv("AWS_REGION", "us-east-1")
    exceptions_table = os.getenv("DYNAMODB_EXCEPTIONS_TABLE", "ExceptionsTable")
    
    # Initialize AWS clients
    dynamodb_client = boto3.client('dynamodb', region_name=region_name)
    sqs_client = boto3.client('sqs', region_name=region_name)
    
    try:
        # Extract payload fields
        event_type = payload.get("event_type", "UNKNOWN")
        trade_id = payload.get("trade_id", "unknown")
        match_score = payload.get("match_score")
        reason_codes = payload.get("reason_codes", [])
        error_message = payload.get("error_message")
        
        # Handle nested payload structure
        if "payload" in payload:
            nested = payload["payload"]
            trade_id = nested.get("trade_id", trade_id)
            match_score = nested.get("match_score", match_score)
            reason_codes = nested.get("reason_codes", reason_codes)
            error_message = nested.get("error_message", error_message)
        
        # Create exception record
        exception = ExceptionRecord(
            exception_id=payload.get("exception_id", f"exc_{uuid.uuid4().hex[:12]}"),
            timestamp=datetime.utcnow(),
            event_type=event_type,
            trade_id=trade_id,
            match_score=match_score,
            reason_codes=reason_codes,
            error_message=error_message,
            context=payload
        )
        
        logger.info(f"Processing exception: {exception.exception_id} for trade: {trade_id}")
        
        # Step 1: Classify exception
        classification = classify_exception(exception)
        logger.info(f"Step 1: Classification = {classification}")
        
        # Step 2: Compute severity score
        severity_score = compute_severity_score(exception)
        logger.info(f"Step 2: Severity score = {severity_score}")
        
        # Step 3: Triage exception
        triage_result = triage_exception(exception, severity_score)
        logger.info(f"Step 3: Triage = {triage_result.severity} -> {triage_result.routing}")
        
        # Step 4: Delegate exception
        delegation = delegate_exception(exception, triage_result)
        logger.info(f"Step 4: Delegated to {delegation.assigned_to}")
        
        # Step 5: Store exception in DynamoDB
        try:
            dynamodb_client.put_item(
                TableName=exceptions_table,
                Item={
                    "exception_id": {"S": exception.exception_id},
                    "timestamp": {"S": exception.timestamp.isoformat()},
                    "trade_id": {"S": trade_id},
                    "event_type": {"S": event_type},
                    "classification": {"S": classification},
                    "severity_score": {"N": str(severity_score)},
                    "severity": {"S": triage_result.severity},
                    "routing": {"S": triage_result.routing},
                    "priority": {"N": str(triage_result.priority)},
                    "sla_hours": {"N": str(triage_result.sla_hours)},
                    "assigned_to": {"S": delegation.assigned_to},
                    "tracking_id": {"S": delegation.tracking_id},
                    "sla_deadline": {"S": delegation.sla_deadline.isoformat()},
                    "resolution_status": {"S": "PENDING"},
                    "reason_codes": {"SS": reason_codes} if reason_codes else {"SS": ["NONE"]}
                }
            )
            logger.info(f"Exception stored in DynamoDB: {exception.exception_id}")
        except ClientError as e:
            logger.warning(f"Could not store exception in DynamoDB: {e}")
        
        # Step 6: Publish to handler queue
        _publish_to_handler_queue(sqs_client, exception, triage_result, delegation)
        
        # Calculate processing time
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        result = {
            "success": True,
            "exception_id": exception.exception_id,
            "trade_id": trade_id,
            "classification": classification,
            "severity_score": severity_score,
            "triage": {
                "severity": triage_result.severity,
                "routing": triage_result.routing,
                "priority": triage_result.priority,
                "sla_hours": triage_result.sla_hours
            },
            "delegation": {
                "status": delegation.status,
                "assigned_to": delegation.assigned_to,
                "tracking_id": delegation.tracking_id,
                "sla_deadline": delegation.sla_deadline.isoformat()
            },
            "processing_time_ms": processing_time_ms
        }
        
        logger.info(f"Exception processed: {json.dumps(result, default=str)}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing exception: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "trade_id": payload.get("trade_id", "unknown")
        }


if __name__ == "__main__":
    """
    REQUIRED: Let AgentCore Runtime control the agent execution.
    """
    app.run()
