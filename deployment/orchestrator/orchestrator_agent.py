"""
Orchestrator Agent - AgentCore Runtime Entry Point (Standalone)

This is a self-contained entry point for the Orchestrator Agent deployed to AgentCore Runtime.
It monitors SLAs, enforces compliance, and coordinates agent workflows.

Requirements: 2.1, 2.2, 3.1, 4.1, 4.2, 4.3, 4.4, 4.5
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

CONTROL_COMMANDS_QUEUE_NAME = "trade-matching-system-control-commands-queue-production"
ALERT_QUEUE_NAME = "trade-matching-system-alert-queue-production"

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
# Data Models
# ============================================================================

class SLAStatus(BaseModel):
    """SLA monitoring status for an agent."""
    agent_id: str
    processing_time_ok: bool = True
    throughput_ok: bool = True
    error_rate_ok: bool = True
    violated: bool = False
    violations: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ComplianceStatus(BaseModel):
    """Compliance check status."""
    passed: bool = True
    failed: bool = False
    checks: List[Dict[str, Any]] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list)


class ControlCommand(BaseModel):
    """Control command for agent management."""
    command_id: str
    command_type: Literal["PAUSE", "RESUME", "SCALE_UP", "SCALE_DOWN", "ESCALATE", "ALERT"]
    target_agent: str
    reason: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentHealthStatus(BaseModel):
    """Health status of an agent."""
    agent_id: str
    status: Literal["ACTIVE", "DEGRADED", "UNHEALTHY", "UNKNOWN"]
    last_heartbeat: Optional[datetime] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    sla_status: Optional[SLAStatus] = None


# ============================================================================
# SLA Monitoring Functions
# ============================================================================

def check_sla(agent_id: str, metrics: Dict[str, Any]) -> SLAStatus:
    """
    Check SLA compliance for an agent.
    
    Args:
        agent_id: Agent identifier
        metrics: Current agent metrics
        
    Returns:
        SLAStatus: SLA compliance status
    """
    targets = SLA_TARGETS.get(agent_id, {})
    if not targets:
        return SLAStatus(agent_id=agent_id, metrics=metrics)
    
    violations = []
    
    # Check processing time
    processing_time = metrics.get("processing_time_ms", 0)
    processing_time_ok = processing_time <= targets.get("processing_time_ms", float('inf'))
    if not processing_time_ok:
        violations.append(f"Processing time {processing_time}ms exceeds target {targets['processing_time_ms']}ms")
    
    # Check throughput
    throughput = metrics.get("throughput_per_hour", float('inf'))
    throughput_ok = throughput >= targets.get("throughput_per_hour", 0)
    if not throughput_ok:
        violations.append(f"Throughput {throughput}/hr below target {targets['throughput_per_hour']}/hr")
    
    # Check error rate
    error_rate = metrics.get("error_rate", 0)
    error_rate_ok = error_rate <= targets.get("error_rate", 1.0)
    if not error_rate_ok:
        violations.append(f"Error rate {error_rate:.2%} exceeds target {targets['error_rate']:.2%}")
    
    violated = len(violations) > 0
    
    return SLAStatus(
        agent_id=agent_id,
        processing_time_ok=processing_time_ok,
        throughput_ok=throughput_ok,
        error_rate_ok=error_rate_ok,
        violated=violated,
        violations=violations,
        metrics=metrics
    )


# ============================================================================
# Compliance Checking Functions
# ============================================================================

def check_compliance(event: Dict[str, Any], dynamodb_client) -> ComplianceStatus:
    """
    Check compliance for an event.
    
    Args:
        event: Event to check
        dynamodb_client: DynamoDB client
        
    Returns:
        ComplianceStatus: Compliance check result
    """
    checks = []
    violations = []
    
    event_type = event.get("event_type", "")
    trade_id = event.get("trade_id") or event.get("payload", {}).get("trade_id")
    source_type = event.get("source_type") or event.get("payload", {}).get("source_type")
    
    # Check 1: Trade source in correct table
    if trade_id and source_type:
        check_result = {
            "check": "trade_source_table_match",
            "trade_id": trade_id,
            "source_type": source_type,
            "passed": True
        }
        
        # Verify trade is in correct table
        try:
            if source_type == "BANK":
                table_name = os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData")
            else:
                table_name = os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData")
            
            response = dynamodb_client.get_item(
                TableName=table_name,
                Key={"Trade_ID": {"S": trade_id}}
            )
            
            if "Item" in response:
                item_source = response["Item"].get("TRADE_SOURCE", {}).get("S", "")
                if item_source != source_type:
                    check_result["passed"] = False
                    violations.append(f"Trade {trade_id} has mismatched source: expected {source_type}, found {item_source}")
        except ClientError as e:
            logger.warning(f"Could not verify trade source: {e}")
        
        checks.append(check_result)
    
    # Check 2: Required fields present
    if event_type in ["TRADE_EXTRACTED", "PDF_PROCESSED"]:
        required_fields = ["trade_id", "source_type"] if event_type == "TRADE_EXTRACTED" else ["document_id"]
        payload = event.get("payload", event)
        
        missing_fields = [f for f in required_fields if not payload.get(f)]
        check_result = {
            "check": "required_fields",
            "event_type": event_type,
            "passed": len(missing_fields) == 0,
            "missing_fields": missing_fields
        }
        
        if missing_fields:
            violations.append(f"Missing required fields: {missing_fields}")
        
        checks.append(check_result)
    
    failed = len(violations) > 0
    
    return ComplianceStatus(
        passed=not failed,
        failed=failed,
        checks=checks,
        violations=violations
    )


# ============================================================================
# Control Command Functions
# ============================================================================

def issue_control_command(
    sqs_client,
    command_type: str,
    target_agent: str,
    reason: str,
    parameters: Dict[str, Any] = None
) -> ControlCommand:
    """
    Issue a control command to an agent.
    
    Args:
        sqs_client: SQS client
        command_type: Type of command
        target_agent: Target agent ID
        reason: Reason for command
        parameters: Additional parameters
        
    Returns:
        ControlCommand: Issued command
    """
    command = ControlCommand(
        command_id=f"cmd_{uuid.uuid4().hex[:12]}",
        command_type=command_type,
        target_agent=target_agent,
        reason=reason,
        parameters=parameters or {},
        timestamp=datetime.utcnow()
    )
    
    # Publish to control commands queue
    try:
        queue_url = sqs_client.get_queue_url(QueueName=CONTROL_COMMANDS_QUEUE_NAME)['QueueUrl']
        
        message = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "event_type": "CONTROL_COMMAND_ISSUED",
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": "orchestrator_agent",
            "payload": command.model_dump(mode='json')
        }
        
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message, default=str)
        )
        logger.info(f"Control command issued: {command.command_type} -> {target_agent}")
    except ClientError as e:
        logger.warning(f"Could not publish control command: {e}")
    
    return command


def publish_alert(
    sqs_client,
    alert_type: str,
    severity: str,
    message: str,
    context: Dict[str, Any] = None
) -> None:
    """
    Publish an alert to the alert queue.
    
    Args:
        sqs_client: SQS client
        alert_type: Type of alert
        severity: Alert severity
        message: Alert message
        context: Additional context
    """
    try:
        queue_url = sqs_client.get_queue_url(QueueName=ALERT_QUEUE_NAME)['QueueUrl']
        
        alert = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "event_type": "ALERT",
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": "orchestrator_agent",
            "payload": {
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "context": context or {}
            }
        }
        
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(alert, default=str)
        )
        logger.info(f"Alert published: {alert_type} ({severity})")
    except ClientError as e:
        logger.warning(f"Could not publish alert: {e}")


# ============================================================================
# Agent Registry Functions
# ============================================================================

def get_agent_status(dynamodb_client, agent_id: str) -> AgentHealthStatus:
    """
    Get health status of an agent from registry.
    
    Args:
        dynamodb_client: DynamoDB client
        agent_id: Agent identifier
        
    Returns:
        AgentHealthStatus: Agent health status
    """
    registry_table = os.getenv("DYNAMODB_AGENT_REGISTRY_TABLE", "AgentRegistry")
    
    try:
        response = dynamodb_client.get_item(
            TableName=registry_table,
            Key={"agent_id": {"S": agent_id}}
        )
        
        if "Item" not in response:
            return AgentHealthStatus(agent_id=agent_id, status="UNKNOWN")
        
        item = response["Item"]
        
        # Parse metrics
        metrics = {}
        if "metrics" in item and "M" in item["metrics"]:
            for k, v in item["metrics"]["M"].items():
                if "N" in v:
                    metrics[k] = float(v["N"])
                elif "S" in v:
                    metrics[k] = v["S"]
        
        # Parse last heartbeat
        last_heartbeat = None
        if "last_heartbeat" in item and "S" in item["last_heartbeat"]:
            try:
                last_heartbeat = datetime.fromisoformat(item["last_heartbeat"]["S"])
            except ValueError:
                pass
        
        # Determine status based on heartbeat
        status = "ACTIVE"
        if last_heartbeat:
            time_since_heartbeat = datetime.utcnow() - last_heartbeat
            if time_since_heartbeat > timedelta(minutes=5):
                status = "UNHEALTHY"
            elif time_since_heartbeat > timedelta(minutes=2):
                status = "DEGRADED"
        
        return AgentHealthStatus(
            agent_id=agent_id,
            status=status,
            last_heartbeat=last_heartbeat,
            metrics=metrics
        )
        
    except ClientError as e:
        logger.warning(f"Could not get agent status: {e}")
        return AgentHealthStatus(agent_id=agent_id, status="UNKNOWN")


def get_all_agent_statuses(dynamodb_client) -> List[AgentHealthStatus]:
    """
    Get health status of all registered agents.
    
    Args:
        dynamodb_client: DynamoDB client
        
    Returns:
        List[AgentHealthStatus]: List of agent health statuses
    """
    registry_table = os.getenv("DYNAMODB_AGENT_REGISTRY_TABLE", "AgentRegistry")
    statuses = []
    
    try:
        response = dynamodb_client.scan(TableName=registry_table)
        
        for item in response.get("Items", []):
            agent_id = item.get("agent_id", {}).get("S", "unknown")
            status = get_agent_status(dynamodb_client, agent_id)
            statuses.append(status)
            
    except ClientError as e:
        logger.warning(f"Could not scan agent registry: {e}")
    
    return statuses


# ============================================================================
# Main Agent Logic
# ============================================================================

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for Orchestrator Agent.
    
    Args:
        payload: Event payload containing:
            - event_type: Type of event to process
            - agent_id: Optional agent ID for status checks
            - metrics: Optional metrics for SLA checks
        context: AgentCore context (optional)
        
    Returns:
        dict: Orchestration result with SLA and compliance status
        
    Validates: Requirements 2.1, 2.2, 3.1, 4.1, 4.2, 4.3, 4.4, 4.5
    """
    start_time = datetime.utcnow()
    logger.info("Orchestrator Agent invoked via AgentCore Runtime")
    logger.info(f"Payload: {json.dumps(payload, default=str)}")
    
    # Get configuration from environment
    region_name = os.getenv("AWS_REGION", "us-east-1")
    
    # Initialize AWS clients
    dynamodb_client = boto3.client('dynamodb', region_name=region_name)
    sqs_client = boto3.client('sqs', region_name=region_name)
    
    try:
        event_type = payload.get("event_type", "UNKNOWN")
        agent_id = payload.get("agent_id")
        
        result = {
            "success": True,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Handle different event types
        if event_type == "AGENT_STATUS":
            # Check SLA for specific agent
            if agent_id:
                metrics = payload.get("metrics", {})
                sla_status = check_sla(agent_id, metrics)
                result["sla_status"] = sla_status.model_dump()
                
                # Issue control commands if SLA violated
                if sla_status.violated:
                    logger.warning(f"SLA violated for {agent_id}: {sla_status.violations}")
                    
                    # Publish alert
                    publish_alert(
                        sqs_client=sqs_client,
                        alert_type="SLA_VIOLATION",
                        severity="HIGH",
                        message=f"SLA violated for {agent_id}",
                        context={"violations": sla_status.violations}
                    )
                    
                    # Issue escalation command
                    command = issue_control_command(
                        sqs_client=sqs_client,
                        command_type="ESCALATE",
                        target_agent=agent_id,
                        reason=f"SLA violations: {', '.join(sla_status.violations)}"
                    )
                    result["control_command"] = command.model_dump(mode='json')
        
        elif event_type == "HEALTH_CHECK":
            # Get status of all agents
            statuses = get_all_agent_statuses(dynamodb_client)
            result["agent_statuses"] = [s.model_dump(mode='json') for s in statuses]
            
            # Check for unhealthy agents
            unhealthy = [s for s in statuses if s.status in ["UNHEALTHY", "DEGRADED"]]
            if unhealthy:
                for status in unhealthy:
                    publish_alert(
                        sqs_client=sqs_client,
                        alert_type="AGENT_UNHEALTHY",
                        severity="CRITICAL" if status.status == "UNHEALTHY" else "HIGH",
                        message=f"Agent {status.agent_id} is {status.status}",
                        context={"agent_id": status.agent_id, "status": status.status}
                    )
        
        elif event_type in ["PDF_PROCESSED", "TRADE_EXTRACTED", "MATCHING_EXCEPTION"]:
            # Check compliance for processing events
            compliance_status = check_compliance(payload, dynamodb_client)
            result["compliance_status"] = compliance_status.model_dump()
            
            # Issue commands if compliance failed
            if compliance_status.failed:
                logger.warning(f"Compliance check failed: {compliance_status.violations}")
                
                publish_alert(
                    sqs_client=sqs_client,
                    alert_type="COMPLIANCE_VIOLATION",
                    severity="HIGH",
                    message=f"Compliance violation detected",
                    context={"violations": compliance_status.violations}
                )
        
        elif event_type == "CONTROL_COMMAND":
            # Process control command request
            command_type = payload.get("command_type", "ALERT")
            target_agent = payload.get("target_agent", "all")
            reason = payload.get("reason", "Manual command")
            parameters = payload.get("parameters", {})
            
            command = issue_control_command(
                sqs_client=sqs_client,
                command_type=command_type,
                target_agent=target_agent,
                reason=reason,
                parameters=parameters
            )
            result["control_command"] = command.model_dump(mode='json')
        
        else:
            # Default: just acknowledge the event
            result["message"] = f"Event {event_type} acknowledged"
        
        # Calculate processing time
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        result["processing_time_ms"] = processing_time_ms
        
        logger.info(f"Orchestration result: {json.dumps(result, default=str)}")
        return result
        
    except Exception as e:
        logger.error(f"Error in orchestration: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "event_type": payload.get("event_type", "UNKNOWN")
        }


if __name__ == "__main__":
    """
    REQUIRED: Let AgentCore Runtime control the agent execution.
    """
    app.run()
