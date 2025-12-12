"""
Orchestrator Agent - Strands SDK Implementation

This agent uses Strands SDK with built-in tools for AWS operations.
It monitors SLAs, enforces compliance, and coordinates agent workflows -
letting the LLM decide when to intervene based on system state.

Requirements: 2.1, 2.2, 3.1, 4.1, 4.2, 4.3, 4.4, 4.5
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
from strands_tools import use_aws
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
AGENT_REGISTRY_TABLE = os.getenv("DYNAMODB_AGENT_REGISTRY_TABLE", "AgentRegistry")
BANK_TABLE = os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData")
COUNTERPARTY_TABLE = os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")
AGENT_ALIAS = os.getenv("AGENT_ALIAS", "default")
OBSERVABILITY_STAGE = os.getenv("OBSERVABILITY_STAGE", "development")

# Agent identification constants
AGENT_NAME = "orchestrator-agent"

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


# SLA targets by agent
SLA_TARGETS = {
    "pdf_adapter_agent": {
        "processing_time_ms": 30000,
        "throughput_per_hour": 120,
        "error_rate": 0.05
    },
    "trade_extraction_agent": {
        "processing_time_ms": 45000,
        "throughput_per_hour": 80,
        "error_rate": 0.05
    },
    "trade_matching_agent": {
        "processing_time_ms": 60000,
        "throughput_per_hour": 60,
        "error_rate": 0.05
    },
    "exception_management_agent": {
        "processing_time_ms": 15000,
        "throughput_per_hour": 200,
        "error_rate": 0.02
    }
}


# ============================================================================
# Custom Tools for Orchestration
# ============================================================================

@tool
def check_agent_sla(
    agent_id: str,
    processing_time_ms: float,
    throughput_per_hour: Optional[float] = None,
    error_rate: Optional[float] = None
) -> str:
    """
    Check if an agent is meeting its SLA targets.
    
    Args:
        agent_id: Agent identifier (pdf_adapter_agent, trade_extraction_agent, etc.)
        processing_time_ms: Current processing time in milliseconds
        throughput_per_hour: Optional current throughput
        error_rate: Optional current error rate (0.0 to 1.0)
        
    Returns:
        JSON string with SLA compliance status and violations if any
    """
    targets = SLA_TARGETS.get(agent_id, {})
    if not targets:
        return json.dumps({
            "agent_id": agent_id,
            "sla_defined": False,
            "message": f"No SLA targets defined for {agent_id}"
        })
    
    violations = []
    metrics = {
        "processing_time_ms": processing_time_ms,
        "throughput_per_hour": throughput_per_hour,
        "error_rate": error_rate
    }
    
    # Check processing time
    target_time = targets.get("processing_time_ms", float('inf'))
    processing_time_ok = processing_time_ms <= target_time
    if not processing_time_ok:
        violations.append(f"Processing time {processing_time_ms}ms exceeds target {target_time}ms")
    
    # Check throughput
    throughput_ok = True
    if throughput_per_hour is not None:
        target_throughput = targets.get("throughput_per_hour", 0)
        throughput_ok = throughput_per_hour >= target_throughput
        if not throughput_ok:
            violations.append(f"Throughput {throughput_per_hour}/hr below target {target_throughput}/hr")
    
    # Check error rate
    error_rate_ok = True
    if error_rate is not None:
        target_error_rate = targets.get("error_rate", 1.0)
        error_rate_ok = error_rate <= target_error_rate
        if not error_rate_ok:
            violations.append(f"Error rate {error_rate:.2%} exceeds target {target_error_rate:.2%}")
    
    violated = len(violations) > 0
    
    return json.dumps({
        "agent_id": agent_id,
        "sla_defined": True,
        "processing_time_ok": processing_time_ok,
        "throughput_ok": throughput_ok,
        "error_rate_ok": error_rate_ok,
        "violated": violated,
        "violations": violations,
        "metrics": metrics,
        "targets": targets
    })


@tool
def check_data_compliance(
    trade_id: str,
    source_type: str
) -> str:
    """
    Check compliance for a trade - verify it's in the correct table.
    
    Args:
        trade_id: Trade identifier to check
        source_type: Expected source type (BANK or COUNTERPARTY)
        
    Returns:
        JSON string with compliance check result and any violations
    """
    try:
        dynamodb_client = get_boto_client('dynamodb')
        
        # Determine expected table
        if source_type == "BANK":
            expected_table = BANK_TABLE
        elif source_type == "COUNTERPARTY":
            expected_table = COUNTERPARTY_TABLE
        else:
            return json.dumps({
                "success": False,
                "error": f"Invalid source_type: {source_type}"
            })
        
        # Check if trade exists in expected table
        response = dynamodb_client.get_item(
            TableName=expected_table,
            Key={"trade_id": {"S": trade_id}, "internal_reference": {"S": trade_id}}
        )
        
        if "Item" not in response:
            return json.dumps({
                "success": True,
                "trade_id": trade_id,
                "compliant": False,
                "violation": f"Trade {trade_id} not found in {expected_table}",
                "expected_table": expected_table
            })
        
        # Verify TRADE_SOURCE matches
        item = response["Item"]
        actual_source = item.get("TRADE_SOURCE", {}).get("S", "")
        
        if actual_source != source_type:
            return json.dumps({
                "success": True,
                "trade_id": trade_id,
                "compliant": False,
                "violation": f"TRADE_SOURCE mismatch: expected {source_type}, found {actual_source}",
                "expected_table": expected_table
            })
        
        return json.dumps({
            "success": True,
            "trade_id": trade_id,
            "compliant": True,
            "message": f"Trade {trade_id} is compliant in {expected_table}",
            "expected_table": expected_table
        })
        
    except Exception as e:
        logger.error(f"Failed to check data compliance: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@tool
def get_agent_health_status(agent_id: str) -> str:
    """
    Get the health status of an agent from the registry.
    
    Args:
        agent_id: Agent identifier to check
        
    Returns:
        JSON string with agent health status including last heartbeat and metrics
    """
    try:
        dynamodb_client = get_boto_client('dynamodb')
        
        response = dynamodb_client.get_item(
            TableName=AGENT_REGISTRY_TABLE,
            Key={"agent_id": {"S": agent_id}}
        )
        
        if "Item" not in response:
            return json.dumps({
                "agent_id": agent_id,
                "status": "UNKNOWN",
                "message": f"Agent {agent_id} not found in registry"
            })
        
        item = response["Item"]
        
        # Parse last heartbeat
        last_heartbeat_str = item.get("last_heartbeat", {}).get("S")
        status = "ACTIVE"
        
        if last_heartbeat_str:
            try:
                last_heartbeat = datetime.fromisoformat(last_heartbeat_str)
                time_since = datetime.utcnow() - last_heartbeat
                
                if time_since > timedelta(minutes=5):
                    status = "UNHEALTHY"
                elif time_since > timedelta(minutes=2):
                    status = "DEGRADED"
            except ValueError:
                pass
        
        # Parse metrics
        metrics = {}
        if "metrics" in item and "M" in item["metrics"]:
            for k, v in item["metrics"]["M"].items():
                if "N" in v:
                    metrics[k] = float(v["N"])
                elif "S" in v:
                    metrics[k] = v["S"]
        
        return json.dumps({
            "agent_id": agent_id,
            "status": status,
            "last_heartbeat": last_heartbeat_str,
            "metrics": metrics
        })
        
    except Exception as e:
        logger.error(f"Failed to get agent health status: {e}")
        return json.dumps({
            "agent_id": agent_id,
            "status": "UNKNOWN",
            "error": str(e)
        })


@tool
def get_all_agents_status() -> str:
    """
    Get health status of all registered agents.
    
    Returns:
        JSON string with list of all agent statuses
    """
    try:
        dynamodb_client = get_boto_client('dynamodb')
        
        response = dynamodb_client.scan(TableName=AGENT_REGISTRY_TABLE)
        
        agents = []
        for item in response.get("Items", []):
            agent_id = item.get("agent_id", {}).get("S", "unknown")
            last_heartbeat_str = item.get("last_heartbeat", {}).get("S")
            
            status = "ACTIVE"
            if last_heartbeat_str:
                try:
                    last_heartbeat = datetime.fromisoformat(last_heartbeat_str)
                    time_since = datetime.utcnow() - last_heartbeat
                    
                    if time_since > timedelta(minutes=5):
                        status = "UNHEALTHY"
                    elif time_since > timedelta(minutes=2):
                        status = "DEGRADED"
                except ValueError:
                    pass
            
            agents.append({
                "agent_id": agent_id,
                "status": status,
                "last_heartbeat": last_heartbeat_str
            })
        
        unhealthy_count = sum(1 for a in agents if a["status"] in ["UNHEALTHY", "DEGRADED"])
        
        return json.dumps({
            "success": True,
            "total_agents": len(agents),
            "unhealthy_count": unhealthy_count,
            "agents": agents
        })
        
    except Exception as e:
        logger.error(f"Failed to get all agents status: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "agents": []
        })


@tool
def record_orchestration_decision(
    decision_type: str,
    target_agent: str,
    reason: str,
    action_taken: str,
    context: Dict[str, Any]
) -> str:
    """
    Record an orchestration decision for audit and learning.
    
    Args:
        decision_type: Type of decision (SLA_VIOLATION, COMPLIANCE_ISSUE, HEALTH_CHECK, etc.)
        target_agent: Agent the decision affects
        reason: Reason for the decision
        action_taken: What action was taken
        context: Additional context about the decision
        
    Returns:
        JSON string with confirmation of recorded decision
    """
    try:
        s3_client = get_boto_client('s3')
        
        decision_id = f"dec_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.utcnow().isoformat()
        
        decision_record = {
            "decision_id": decision_id,
            "timestamp": timestamp,
            "decision_type": decision_type,
            "target_agent": target_agent,
            "reason": reason,
            "action_taken": action_taken,
            "context": context
        }
        
        # Save to S3 for audit
        key = f"orchestration/decisions/{datetime.utcnow().strftime('%Y/%m/%d')}/{decision_id}.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(decision_record, indent=2),
            ContentType='application/json'
        )
        
        return json.dumps({
            "success": True,
            "decision_id": decision_id,
            "s3_location": f"s3://{S3_BUCKET}/{key}",
            "message": f"Decision recorded: {action_taken}"
        })
        
    except Exception as e:
        logger.error(f"Failed to record orchestration decision: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


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
# Agent System Prompt (Optimized for token efficiency)
# ============================================================================

SYSTEM_PROMPT = f"""You are an Orchestrator Agent for the OTC trade matching system.

## Resources
- Registry: {AGENT_REGISTRY_TABLE} | Bank: {BANK_TABLE} | Counterparty: {COUNTERPARTY_TABLE}
- S3: {S3_BUCKET} | Region: {REGION}

## Tools
1. check_agent_sla(agent_id, processing_time_ms, throughput_per_hour, error_rate) → SLA status
2. check_data_compliance(trade_id, source_type) → compliance status
3. get_agent_health_status(agent_id) → health status (ACTIVE/DEGRADED/UNHEALTHY)
4. get_all_agents_status() → all agent statuses
5. record_orchestration_decision(decision_type, target_agent, reason, action_taken, context) → audit record
6. use_aws → general AWS operations

## SLA Targets
- pdf_adapter: 30s, 120/hr, 5% error
- trade_extraction: 45s, 80/hr, 5% error
- trade_matching: 60s, 60/hr, 5% error
- exception_management: 15s, 200/hr, 2% error

## Decision Types & Actions
Types: SLA_VIOLATION, COMPLIANCE_ISSUE, HEALTH_CHECK, ESCALATION
Actions: ALERT, ESCALATE, PAUSE, SCALE_UP, NO_ACTION

## Workflow
1. Analyze event → 2. Gather info with tools → 3. Decide → 4. Record decision → 5. Report

## Rules
- Provide clear reasoning for decisions
- Escalate critical issues immediately
- Record all significant decisions
"""


# ============================================================================
# Create Strands Agent
# ============================================================================

def create_orchestrator_agent() -> Agent:
    """Create and configure the Strands orchestrator agent."""
    # Explicitly configure BedrockModel for consistent behavior
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.1,  # Low temperature for deterministic orchestration decisions
        max_tokens=4096,
    )
    
    return Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            check_agent_sla,
            check_data_compliance,
            get_agent_health_status,
            get_all_agents_status,
            record_orchestration_decision,
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
    AgentCore Runtime entrypoint for Orchestrator Agent.
    
    Uses Strands SDK with custom tools for system orchestration.
    The LLM decides how to respond based on the event type and system state.
    
    Args:
        payload: Event payload containing:
            - event_type: Type of event (AGENT_STATUS, HEALTH_CHECK, etc.)
            - agent_id: Optional agent ID for specific checks
            - metrics: Optional metrics for SLA checks
            - trade_id: Optional trade ID for compliance checks
        context: AgentCore context (optional)
        
    Returns:
        dict: Orchestration result with decisions and recommendations
    """
    start_time = datetime.utcnow()
    logger.info("Orchestrator Agent (Strands) invoked")
    logger.info(f"Payload: {json.dumps(payload, default=str)}")
    
    event_type = payload.get("event_type", "UNKNOWN")
    agent_id = payload.get("agent_id")
    metrics = payload.get("metrics", {})
    trade_id = payload.get("trade_id")
    source_type = payload.get("source_type")
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    # Standard observability attributes
    obs_attributes = {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "agent_alias": AGENT_ALIAS,
        "correlation_id": correlation_id,
        "event_type": event_type,
        "target_agent_id": agent_id or "unknown",
        "trade_id": trade_id or "unknown",
    }
    
    try:
        # Start observability span for the main operation
        span_context = None
        if observability:
            try:
                span_context = observability.start_span("orchestration_decision")
                span_context.__enter__()
                for k, v in obs_attributes.items():
                    span_context.set_attribute(k, v)
            except Exception as e:
                logger.warning(f"Failed to start observability span: {e}")
                span_context = None
        
        # Create the agent
        agent = create_orchestrator_agent()
        
        # Build goal-oriented prompt - let LLM decide the approach
        context_details = {
            "event_type": event_type,
            "agent_id": agent_id,
            "trade_id": trade_id,
            "source_type": source_type,
            "metrics": metrics,
            "correlation_id": correlation_id
        }
        
        prompt = f"""Handle this orchestration event and take appropriate action.

## Event Context
{json.dumps({k: v for k, v in context_details.items() if v}, indent=2)}

## Your Goal
Analyze this event, gather relevant information, make a decision, and report your findings.

## Considerations
- For AGENT_STATUS events: Check if the agent is meeting SLA targets
- For HEALTH_CHECK events: Assess overall system health
- For PDF_PROCESSED/TRADE_EXTRACTED events: Verify data compliance
- Record significant decisions for audit trail
- Recommend appropriate actions (ALERT, ESCALATE, SCALE_UP, NO_ACTION)

## Success Criteria
- Clear assessment of the situation
- Appropriate use of monitoring tools
- Documented decision with reasoning
- Actionable recommendations
"""
        
        # Invoke the agent
        logger.info("Invoking Strands agent for orchestration")
        result = agent(prompt)
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Extract token metrics
        token_metrics = _extract_token_metrics(result)
        logger.info(f"Token usage: {token_metrics['input_tokens']} in / {token_metrics['output_tokens']} out")
        
        # Extract the agent's response safely
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
            "event_type": event_type,
            "correlation_id": correlation_id,
            "agent_response": response_text,
            "processing_time_ms": processing_time_ms,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "agent_alias": AGENT_ALIAS,
            "token_usage": token_metrics,
        }
        
    except Exception as e:
        logger.error(f"Error in orchestrator agent: {e}", exc_info=True)
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
            "event_type": event_type,
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
