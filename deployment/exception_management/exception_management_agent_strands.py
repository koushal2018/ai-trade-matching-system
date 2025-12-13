"""
Exception Management Agent - Strands SDK Implementation

This agent uses Strands SDK with built-in tools for AWS operations.
It handles exceptions with intelligent triage, delegation, and routing -
letting the LLM decide the best course of action based on the exception context.

Requirements: 2.1, 2.2, 3.5, 8.1, 8.2, 8.3, 8.4, 8.5
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

# Strands SDK imports
from strands import Agent, tool
from strands.models import BedrockModel
from strands_agents_tools import use_aws
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

# AgentCore Observability
try:
    from bedrock_agentcore.observability import Observability
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Configuration
REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
EXCEPTIONS_TABLE = os.getenv("DYNAMODB_EXCEPTIONS_TABLE", "ExceptionsTable")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")
AGENT_ALIAS = os.getenv("AGENT_ALIAS", "default")
OBSERVABILITY_STAGE = os.getenv("OBSERVABILITY_STAGE", "development")

# Agent identification constants
AGENT_NAME = "exception-management-agent"

# Initialize Observability
observability = None
if OBSERVABILITY_AVAILABLE:
    try:
        observability = Observability(
            service_name=AGENT_NAME,
            stage=OBSERVABILITY_STAGE,
            verbosity="high" if OBSERVABILITY_STAGE == "development" else "low"
        )
        logger.info(f"Observability initialized for {AGENT_NAME}")
    except Exception as e:
        logger.warning(f"Failed to initialize observability: {e}")

# Lazy-initialized boto3 clients for efficiency
_boto_clients: Dict[str, Any] = {}


def get_boto_client(service: str):
    """Get or create a boto3 client for the specified service."""
    import boto3
    if service not in _boto_clients:
        _boto_clients[service] = boto3.client(service, region_name=REGION)
    return _boto_clients[service]


# ============================================================================
# Custom Tools for Exception Management
# ============================================================================

@tool
def analyze_exception_severity(
    event_type: str,
    reason_codes: List[str],
    match_score: Optional[float] = None,
    error_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze an exception and compute its severity score and classification.
    
    Args:
        event_type: Type of exception (PDF_PROCESSING_ERROR, EXTRACTION_FAILED, MATCHING_EXCEPTION, etc.)
        reason_codes: List of reason codes (NOTIONAL_MISMATCH, DATE_MISMATCH, COUNTERPARTY_MISMATCH, etc.)
        match_score: Optional match confidence score (0.0 to 1.0)
        error_message: Optional error message for context
        
    Returns:
        dict: Contains severity_score, classification, and recommended_severity
    """
    # Base severity scores for reason codes
    base_scores = {
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
    
    # Compute base score from reason codes
    if reason_codes:
        scores = [base_scores.get(code, 0.5) for code in reason_codes]
        severity_score = max(scores)
    else:
        severity_score = 0.5
    
    # Adjust based on match score
    if match_score is not None:
        severity_score = severity_score * (1 - match_score * 0.3)
    
    severity_score = round(min(1.0, max(0.0, severity_score)), 2)
    
    # Classify exception
    if event_type == "PDF_PROCESSING_ERROR":
        classification = "PROCESSING_ERROR"
    elif event_type == "EXTRACTION_FAILED":
        classification = "EXTRACTION_ERROR"
    elif event_type == "MATCHING_EXCEPTION":
        if "COUNTERPARTY_MISMATCH" in reason_codes:
            classification = "COUNTERPARTY_ERROR"
        elif "NOTIONAL_MISMATCH" in reason_codes:
            classification = "NOTIONAL_ERROR"
        elif "DATE_MISMATCH" in reason_codes:
            classification = "DATE_ERROR"
        else:
            classification = "MATCHING_ERROR"
    else:
        classification = "UNKNOWN_ERROR"
    
    # Determine severity level
    if severity_score >= 0.9:
        recommended_severity = "CRITICAL"
    elif severity_score >= 0.7:
        recommended_severity = "HIGH"
    elif severity_score >= 0.5:
        recommended_severity = "MEDIUM"
    else:
        recommended_severity = "LOW"
    
    return {
        "severity_score": severity_score,
        "classification": classification,
        "recommended_severity": recommended_severity,
        "reason_codes_analyzed": reason_codes,
        "event_type": event_type
    }


@tool
def determine_routing(
    severity: str,
    classification: str,
    reason_codes: List[str]
) -> Dict[str, Any]:
    """
    Determine where to route an exception based on severity and classification.
    
    Args:
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
        classification: Exception classification
        reason_codes: List of reason codes
        
    Returns:
        dict: Contains routing decision, priority, SLA hours, and assigned team
    """
    # SLA hours by severity
    sla_hours_map = {
        "CRITICAL": 2,
        "HIGH": 4,
        "MEDIUM": 8,
        "LOW": 24
    }
    
    # Determine routing based on severity and reason codes
    if severity == "CRITICAL" or "COUNTERPARTY_MISMATCH" in reason_codes:
        routing = "SENIOR_OPS"
        assigned_to = "senior_ops_team"
        priority = 1
    elif severity == "HIGH" or "NOTIONAL_MISMATCH" in reason_codes:
        routing = "OPS_DESK"
        assigned_to = "ops_desk_team"
        priority = 2
    elif severity == "MEDIUM":
        routing = "OPS_DESK"
        assigned_to = "ops_desk_team"
        priority = 3
    elif severity == "LOW":
        routing = "AUTO_RESOLVE"
        assigned_to = "system_auto_resolver"
        priority = 4
    else:
        routing = "OPS_DESK"
        assigned_to = "ops_desk_team"
        priority = 3
    
    sla_hours = sla_hours_map.get(severity, 8)
    sla_deadline = (datetime.utcnow() + timedelta(hours=sla_hours)).isoformat()
    
    return {
        "routing": routing,
        "assigned_to": assigned_to,
        "priority": priority,
        "sla_hours": sla_hours,
        "sla_deadline": sla_deadline,
        "tracking_id": f"trk_{uuid.uuid4().hex[:12]}"
    }


@tool
def store_exception_record(
    exception_id: str,
    trade_id: str,
    event_type: str,
    classification: str,
    severity_score: float,
    severity: str,
    routing: str,
    priority: int,
    sla_hours: int,
    assigned_to: str,
    tracking_id: str,
    sla_deadline: str,
    reason_codes: List[str]
) -> Dict[str, Any]:
    """
    Store an exception record in DynamoDB for tracking and audit.
    
    Args:
        exception_id: Unique exception identifier
        trade_id: Associated trade ID
        event_type: Type of exception event
        classification: Exception classification
        severity_score: Computed severity score
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
        routing: Routing decision
        priority: Priority level (1-5)
        sla_hours: SLA hours for resolution
        assigned_to: Team assigned to handle
        tracking_id: Tracking ID for the exception
        sla_deadline: SLA deadline timestamp
        reason_codes: List of reason codes
        
    Returns:
        dict: Contains success status and stored record details
    """
    try:
        dynamodb_client = get_boto_client('dynamodb')
        
        item = {
            "exception_id": {"S": exception_id},
            "timestamp": {"S": datetime.utcnow().isoformat()},
            "trade_id": {"S": trade_id},
            "event_type": {"S": event_type},
            "classification": {"S": classification},
            "severity_score": {"N": str(severity_score)},
            "severity": {"S": severity},
            "routing": {"S": routing},
            "priority": {"N": str(priority)},
            "sla_hours": {"N": str(sla_hours)},
            "assigned_to": {"S": assigned_to},
            "tracking_id": {"S": tracking_id},
            "sla_deadline": {"S": sla_deadline},
            "resolution_status": {"S": "PENDING"}
        }
        
        # Add reason codes if present
        if reason_codes:
            item["reason_codes"] = {"SS": reason_codes}
        else:
            item["reason_codes"] = {"SS": ["NONE"]}
        
        dynamodb_client.put_item(
            TableName=EXCEPTIONS_TABLE,
            Item=item
        )
        
        return {
            "success": True,
            "exception_id": exception_id,
            "table_name": EXCEPTIONS_TABLE,
            "message": f"Exception record stored successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_similar_exceptions(trade_id: str, classification: str) -> Dict[str, Any]:
    """
    Query for similar past exceptions to help with resolution.
    
    Args:
        trade_id: Trade ID to search for related exceptions
        classification: Exception classification to find similar cases
        
    Returns:
        dict: Contains list of similar exceptions and resolution patterns
    """
    try:
        dynamodb_client = get_boto_client('dynamodb')
        
        # Scan for similar exceptions (in production, use GSI for efficiency)
        response = dynamodb_client.scan(
            TableName=EXCEPTIONS_TABLE,
            FilterExpression="classification = :class AND resolution_status = :status",
            ExpressionAttributeValues={
                ":class": {"S": classification},
                ":status": {"S": "RESOLVED"}
            },
            Limit=5
        )
        
        similar_exceptions = []
        for item in response.get("Items", []):
            similar_exceptions.append({
                "exception_id": item.get("exception_id", {}).get("S"),
                "trade_id": item.get("trade_id", {}).get("S"),
                "resolution_notes": item.get("resolution_notes", {}).get("S", "No notes"),
                "resolved_by": item.get("resolved_by", {}).get("S", "Unknown")
            })
        
        return {
            "success": True,
            "similar_count": len(similar_exceptions),
            "similar_exceptions": similar_exceptions,
            "message": f"Found {len(similar_exceptions)} similar resolved exceptions"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "similar_exceptions": []
        }


# ============================================================================
# Health Check Handler
# ============================================================================

@app.ping
def health_check() -> PingStatus:
    """Custom health check for AgentCore Runtime."""
    try:
        # Verify DynamoDB client can be created
        get_boto_client('dynamodb')
        return PingStatus.HEALTHY
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return PingStatus.HEALTHY  # Return healthy to avoid restart loops


# ============================================================================
# Agent System Prompt
# ============================================================================

SYSTEM_PROMPT = f"""You are an expert Exception Management Agent for OTC derivative trade processing.

Your job is to intelligently triage, classify, and route exceptions that occur during trade processing.
You make decisions based on the exception context, severity, and historical patterns.

## Available AWS Resources
- Exceptions Table: {EXCEPTIONS_TABLE}
- Region: {REGION}

## Available Tools

1. **analyze_exception_severity**: Analyze an exception and compute severity score
   - Takes event_type, reason_codes, match_score, error_message
   - Returns severity_score, classification, recommended_severity

2. **determine_routing**: Decide where to route the exception
   - Takes severity, classification, reason_codes
   - Returns routing decision, priority, SLA, assigned team

3. **store_exception_record**: Store the exception in DynamoDB for tracking
   - Stores all exception details for audit and tracking

4. **get_similar_exceptions**: Find similar past exceptions
   - Helps identify patterns and resolution strategies

5. **use_aws**: General AWS operations for any additional needs

## Exception Types
- PDF_PROCESSING_ERROR: Issues with PDF conversion or reading
- EXTRACTION_FAILED: Failed to extract trade data from document
- MATCHING_EXCEPTION: Trade matching found discrepancies

## Reason Codes (severity indicators)
- COUNTERPARTY_MISMATCH (Critical): Different counterparty names
- NOTIONAL_MISMATCH (High): Notional amount differs beyond tolerance
- DATE_MISMATCH (Medium): Trade dates don't align
- CURRENCY_MISMATCH (Medium): Currency codes differ
- MISSING_FIELD (Medium): Required field not found
- PROCESSING_ERROR (Low): General processing issue

## Routing Destinations
- SENIOR_OPS: Critical issues requiring senior review
- OPS_DESK: Standard operations team handling
- COMPLIANCE: Regulatory or compliance concerns
- ENGINEERING: Technical/system issues
- AUTO_RESOLVE: Low severity, can be auto-resolved

## Your Workflow
1. Analyze the exception using analyze_exception_severity
2. Consider the context and any patterns from similar exceptions
3. Determine routing using determine_routing
4. Store the exception record for tracking
5. Report your triage decision with clear reasoning

## Important Notes
- Always provide clear reasoning for your triage decisions
- Consider the business impact when determining severity
- Look for patterns in similar exceptions to improve routing
- Critical exceptions (counterparty mismatches) always go to SENIOR_OPS
"""


# ============================================================================
# Create Strands Agent
# ============================================================================

def create_exception_agent() -> Agent:
    """Create and configure the Strands exception management agent."""
    # Explicitly configure BedrockModel for consistent behavior
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.1,  # Low temperature for deterministic triage decisions
        max_tokens=4096,
    )
    
    return Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            analyze_exception_severity,
            determine_routing,
            store_exception_record,
            get_similar_exceptions,
            use_aws
        ]
    )


# ============================================================================
# AgentCore Entrypoint
# ============================================================================

def _extract_token_metrics(result) -> Dict[str, int]:
    """Extract token usage metrics from Strands agent result."""
    metrics = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    try:
        if hasattr(result, 'metrics'):
            metrics["input_tokens"] = getattr(result.metrics, 'input_tokens', 0) or 0
            metrics["output_tokens"] = getattr(result.metrics, 'output_tokens', 0) or 0
        elif hasattr(result, 'usage'):
            metrics["input_tokens"] = getattr(result.usage, 'input_tokens', 0) or 0
            metrics["output_tokens"] = getattr(result.usage, 'output_tokens', 0) or 0
        metrics["total_tokens"] = metrics["input_tokens"] + metrics["output_tokens"]
    except Exception:
        pass
    return metrics


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for Exception Management Agent.
    
    Uses Strands SDK with custom tools for exception handling.
    The LLM decides how to triage and route based on the exception context.
    
    Args:
        payload: Event payload containing:
            - event_type: Type of exception event
            - trade_id: Trade identifier
            - match_score: Optional match score
            - reason_codes: List of reason codes
            - error_message: Optional error message
        context: AgentCore context (optional)
        
    Returns:
        dict: Triage and delegation result
    """
    start_time = datetime.utcnow()
    logger.info("Exception Management Agent (Strands) invoked")
    logger.info(f"Payload: {json.dumps(payload, default=str)}")
    
    # Extract payload fields (handle nested structure)
    event_type = payload.get("event_type", "UNKNOWN")
    trade_id = payload.get("trade_id", "unknown")
    match_score = payload.get("match_score")
    reason_codes = payload.get("reason_codes", [])
    error_message = payload.get("error_message")
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    # Handle nested payload structure
    if "payload" in payload:
        nested = payload["payload"]
        trade_id = nested.get("trade_id", trade_id)
        match_score = nested.get("match_score", match_score)
        reason_codes = nested.get("reason_codes", reason_codes)
        error_message = nested.get("error_message", error_message)
    
    exception_id = payload.get("exception_id", f"exc_{uuid.uuid4().hex[:12]}")
    
    # Standard observability attributes
    obs_attributes = {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "agent_alias": AGENT_ALIAS,
        "correlation_id": correlation_id,
        "exception_id": exception_id,
        "trade_id": trade_id,
        "event_type": event_type,
        "reason_codes_count": len(reason_codes) if reason_codes else 0,
    }
    
    try:
        # Start observability span for the main operation
        span_context = None
        if observability:
            try:
                span_context = observability.start_span("exception_triage")
                span_context.__enter__()
                for k, v in obs_attributes.items():
                    span_context.set_attribute(k, v)
                if match_score is not None:
                    span_context.set_attribute("match_score", match_score)
            except Exception as e:
                logger.warning(f"Failed to start observability span: {e}")
                span_context = None
        
        # Create the agent
        agent = create_exception_agent()
        
        # Build context for the agent
        reason_codes_str = ", ".join(reason_codes) if reason_codes else "None"
        match_score_str = f"{match_score:.2f}" if match_score is not None else "N/A"
        
        # Build goal-oriented prompt - let LLM decide the triage approach
        prompt = f"""Triage and route this trade processing exception.

## Exception Context
- Exception ID: {exception_id}
- Trade ID: {trade_id}
- Event Type: {event_type}
- Reason Codes: {reason_codes_str}
- Match Score: {match_score_str}
- Error Message: {error_message or "None provided"}
- Correlation ID: {correlation_id}

## Your Goal
Analyze this exception, determine its severity and classification, route it appropriately, and store it for tracking.

## Considerations
- Assess severity based on reason codes and business impact
- Check for similar past exceptions to identify patterns
- Route critical issues (e.g., counterparty mismatches) to senior ops
- Ensure the exception is recorded for audit and tracking

## Success Criteria
- Clear classification and severity assessment
- Appropriate routing decision with reasoning
- Exception stored with all relevant metadata
- SLA deadline assigned based on severity
"""
        
        # Invoke the agent
        logger.info("Invoking Strands agent for exception handling")
        result = agent(prompt)
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Extract token metrics
        token_metrics = _extract_token_metrics(result)
        logger.info(f"Token usage: {token_metrics['input_tokens']} in / {token_metrics['output_tokens']} out")
        
        # Extract the agent's response safely (consistent with other agents)
        if hasattr(result, 'message') and result.message:
            if hasattr(result.message, 'content') and result.message.content:
                content = result.message.content
                if isinstance(content, list) and len(content) > 0:
                    first_block = content[0]
                    response_text = first_block.get('text', str(result.message)) if isinstance(first_block, dict) else str(first_block)
                else:
                    response_text = str(content)
            else:
                response_text = str(result.message)
        else:
            response_text = str(result)
        
        # Record success metrics in observability span
        if span_context:
            try:
                span_context.set_attribute("success", True)
                span_context.set_attribute("processing_time_ms", processing_time_ms)
                span_context.set_attribute("input_tokens", token_metrics["input_tokens"])
                span_context.set_attribute("output_tokens", token_metrics["output_tokens"])
                span_context.set_attribute("total_tokens", token_metrics["total_tokens"])
            except Exception as e:
                logger.warning(f"Failed to set span attributes: {e}")
        
        return {
            "success": True,
            "exception_id": exception_id,
            "trade_id": trade_id,
            "correlation_id": correlation_id,
            "agent_response": response_text,
            "processing_time_ms": processing_time_ms,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "agent_alias": AGENT_ALIAS,
            "token_usage": token_metrics,
        }
        
    except Exception as e:
        logger.error(f"Error in exception management agent: {e}", exc_info=True)
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Record error in observability span
        if span_context:
            try:
                span_context.set_attribute("success", False)
                span_context.set_attribute("error_type", type(e).__name__)
                span_context.set_attribute("error_message", str(e))
                span_context.set_attribute("processing_time_ms", processing_time_ms)
            except Exception:
                pass
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "exception_id": exception_id,
            "trade_id": trade_id,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "processing_time_ms": processing_time_ms,
        }
    finally:
        # Close observability span
        if span_context:
            try:
                span_context.__exit__(None, None, None)
            except Exception:
                pass


if __name__ == "__main__":
    """Let AgentCore Runtime control the agent execution."""
    app.run()
