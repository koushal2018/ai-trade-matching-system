"""
Orchestrator Agent

This agent provides lightweight governance through SLA monitoring,
compliance checking, and control command issuance. It subscribes to
all agent events for monitoring and does NOT directly invoke agents.

Requirements: 3.1, 4.1, 4.2, 4.3, 4.4, 4.5
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import boto3
import logging

# Import models
from ..models.events import (
    EventTaxonomy,
    StandardEventMessage
)
from ..models.registry import AgentRegistry, AgentRegistryEntry, ScalingConfig

# Import orchestrator tools
from ..orchestrator import (
    SLAMonitorTool,
    SLAStatus,
    ComplianceCheckerTool,
    ComplianceStatus,
    ControlCommandTool,
    CommandType
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Orchestrator Agent for lightweight governance and monitoring.
    
    This agent:
    1. Subscribes to orchestrator-monitoring-queue (fanout from all queues)
    2. Monitors SLAs for all agents
    3. Enforces compliance checkpoints
    4. Issues control commands when needed
    5. Aggregates metrics from all agents
    6. Registers itself in AgentRegistry
    
    Key Principles:
    - Lightweight governance (monitoring and control, not direct invocation)
    - Event-driven monitoring (subscribes to all agent events)
    - Reactive control (issues commands based on violations)
    
    Validates: Requirements 3.1, 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    def __init__(
        self,
        agent_id: str = "orchestrator_agent",
        region_name: str = "us-east-1",
        monitoring_queue: str = "trade-matching-system-orchestrator-monitoring-production",
        sla_check_interval_minutes: int = 5,
        compliance_check_interval_minutes: int = 15
    ):
        """
        Initialize Orchestrator Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            region_name: AWS region
            monitoring_queue: SQS queue for monitoring events (fanout from all queues)
            sla_check_interval_minutes: How often to check SLAs
            compliance_check_interval_minutes: How often to check compliance
        """
        self.agent_id = agent_id
        self.region_name = region_name
        self.monitoring_queue = monitoring_queue
        self.sla_check_interval_minutes = sla_check_interval_minutes
        self.compliance_check_interval_minutes = compliance_check_interval_minutes
        
        # Initialize AWS clients
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        
        # Initialize registry
        self.registry = AgentRegistry(region_name=region_name)
        
        # Initialize tools
        self.sla_monitor = SLAMonitorTool(region_name=region_name)
        self.compliance_checker = ComplianceCheckerTool(region_name=region_name)
        self.control_command = ControlCommandTool(region_name=region_name)
        
        # Get queue URL
        self.monitoring_queue_url = self._get_queue_url(monitoring_queue)
        
        # Track last check times
        self.last_sla_check = datetime.utcnow()
        self.last_compliance_check = datetime.utcnow()
        
        # Metrics
        self.events_processed = 0
        self.sla_violations_detected = 0
        self.compliance_violations_detected = 0
        self.control_commands_issued = 0
        
        logger.info(f"Orchestrator Agent initialized: {agent_id}")
    
    def _get_queue_url(self, queue_name: str) -> str:
        """Get SQS queue URL from queue name."""
        try:
            response = self.sqs.get_queue_url(QueueName=queue_name)
            return response['QueueUrl']
        except Exception as e:
            logger.error(f"Error getting queue URL for {queue_name}: {e}")
            return ""
    
    def register(self) -> dict:
        """
        Register this agent in the AgentRegistry.
        
        Returns:
            dict: Registration result
            
        Validates: Requirements 4.1
        """
        entry = AgentRegistryEntry(
            agent_id=self.agent_id,
            agent_name="Orchestrator Agent",
            agent_type="ORCHESTRATOR",
            version="1.0.0",
            capabilities=[
                "sla_monitoring",
                "compliance_checking",
                "control_commands",
                "metrics_aggregation",
                "agent_coordination"
            ],
            event_subscriptions=[self.monitoring_queue],
            event_publications=[],  # Orchestrator doesn't publish events, it issues commands
            sla_targets={
                "monitoring_latency_ms": 1000.0,  # 1 second monitoring latency
                "throughput_per_hour": 3600.0,    # Process 3600 events per hour
                "error_rate": 0.01                # 1% error rate
            },
            scaling_config=ScalingConfig(
                min_instances=1,
                max_instances=3,
                target_queue_depth=1000,
                scale_up_threshold=0.8,
                scale_down_threshold=0.2
            ),
            deployment_status="ACTIVE"
        )
        
        result = self.registry.register_agent(entry)
        logger.info(f"Agent registration result: {result}")
        return result
    
    def process_event(self, event_message) -> Dict[str, Any]:
        """
        Process a monitoring event.
        
        This method:
        1. Receives events from all agents (fanout)
        2. Updates agent metrics
        3. Checks if periodic SLA/compliance checks are needed
        4. Issues control commands if violations detected
        
        Args:
            event_message: StandardEventMessage from SQS or dict payload
            
        Returns:
            dict: Processing result
            
        Validates: Requirements 4.1, 4.2, 4.3, 4.4
        """
        start_time = datetime.utcnow()
        
        # Handle both StandardEventMessage objects and dict payloads
        if isinstance(event_message, StandardEventMessage):
            correlation_id = event_message.correlation_id
            event_type = event_message.event_type
            source_agent = event_message.source_agent
            payload = event_message.payload
        elif isinstance(event_message, dict):
            correlation_id = event_message.get("correlation_id", str(uuid.uuid4()))
            event_type = event_message.get("event_type", "UNKNOWN")
            source_agent = event_message.get("source_agent", "unknown")
            payload = event_message.get("payload", {})
        else:
            raise ValueError(f"Invalid event_message type: {type(event_message)}")
        
        try:
            logger.info(f"Processing event: {event_type} from {source_agent}")
            
            # Update event counter
            self.events_processed += 1
            
            # Extract metrics from event
            processing_time_ms = payload.get("processing_time_ms", 0.0)
            
            # Update agent metrics in registry
            if source_agent and source_agent != "unknown":
                self.registry.update_agent_status(
                    agent_id=source_agent,
                    metrics={
                        "last_event_time": datetime.utcnow().timestamp(),
                        "last_processing_time_ms": processing_time_ms
                    },
                    last_heartbeat=datetime.utcnow()
                )
            
            # Check if it's time for periodic SLA check
            time_since_sla_check = (datetime.utcnow() - self.last_sla_check).total_seconds() / 60
            if time_since_sla_check >= self.sla_check_interval_minutes:
                logger.info("Performing periodic SLA check")
                self._perform_sla_check()
                self.last_sla_check = datetime.utcnow()
            
            # Check if it's time for periodic compliance check
            time_since_compliance_check = (datetime.utcnow() - self.last_compliance_check).total_seconds() / 60
            if time_since_compliance_check >= self.compliance_check_interval_minutes:
                logger.info("Performing periodic compliance check")
                self._perform_compliance_check()
                self.last_compliance_check = datetime.utcnow()
            
            # Check for specific event types that require immediate action
            if event_type == EventTaxonomy.SLA_VIOLATED:
                logger.warning(f"SLA violation event received from {source_agent}")
                self._handle_sla_violation(payload)
            
            elif event_type == EventTaxonomy.COMPLIANCE_CHECK_FAILED:
                logger.warning(f"Compliance violation event received from {source_agent}")
                self._handle_compliance_violation(payload)
            
            # Emit metrics to CloudWatch
            self._emit_metrics()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "event_type": event_type,
                "source_agent": source_agent,
                "processing_time_ms": processing_time,
                "events_processed": self.events_processed
            }
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return {
                "success": False,
                "error": str(e),
                "event_type": event_type if 'event_type' in locals() else "unknown"
            }
    
    def _perform_sla_check(self) -> None:
        """
        Perform periodic SLA check for all agents.
        
        Validates: Requirements 4.1, 4.2, 4.3
        """
        try:
            logger.info("Checking SLA compliance for all agents")
            
            # Get system-wide SLA status
            sla_status = self.sla_monitor.get_system_wide_sla_status(
                time_window_minutes=self.sla_check_interval_minutes
            )
            
            logger.info(
                f"SLA Status: {sla_status.status}, "
                f"Compliance: {sla_status.compliance_percentage:.1f}%, "
                f"Violations: {len(sla_status.violations)}"
            )
            
            # Handle violations
            if sla_status.violations:
                self.sla_violations_detected += len(sla_status.violations)
                
                for violation in sla_status.violations:
                    logger.warning(f"SLA Violation: {violation.description}")
                    
                    # Issue control commands based on severity
                    if violation.severity in ["HIGH", "CRITICAL"]:
                        self._handle_sla_violation({
                            "agent_id": violation.agent_id,
                            "metric_type": violation.metric_type.value,
                            "severity": violation.severity,
                            "violation_percentage": violation.violation_percentage
                        })
            
            # Emit SLA metrics to CloudWatch
            self.cloudwatch.put_metric_data(
                Namespace='TradeMatchingSystem/Orchestrator',
                MetricData=[
                    {
                        'MetricName': 'SystemSLACompliance',
                        'Value': sla_status.compliance_percentage,
                        'Unit': 'Percent',
                        'Timestamp': datetime.utcnow()
                    },
                    {
                        'MetricName': 'SLAViolations',
                        'Value': len(sla_status.violations),
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Error performing SLA check: {e}")
    
    def _perform_compliance_check(self) -> None:
        """
        Perform periodic compliance check.
        
        Validates: Requirements 4.1, 4.2
        """
        try:
            logger.info("Checking compliance")
            
            # Check all compliance
            compliance_status = self.compliance_checker.check_all_compliance(sample_size=50)
            
            logger.info(
                f"Compliance Status: {compliance_status.status}, "
                f"Compliance: {compliance_status.compliance_percentage:.1f}%, "
                f"Violations: {len(compliance_status.violations)}"
            )
            
            # Handle violations
            if compliance_status.violations:
                self.compliance_violations_detected += len(compliance_status.violations)
                
                for violation in compliance_status.violations:
                    logger.warning(f"Compliance Violation: {violation.description}")
                    
                    # Issue control commands based on severity
                    if violation.severity in ["HIGH", "CRITICAL"]:
                        self._handle_compliance_violation({
                            "check_type": violation.check_type.value,
                            "resource_id": violation.resource_id,
                            "severity": violation.severity,
                            "description": violation.description,
                            "remediation": violation.remediation
                        })
            
            # Emit compliance metrics to CloudWatch
            self.cloudwatch.put_metric_data(
                Namespace='TradeMatchingSystem/Orchestrator',
                MetricData=[
                    {
                        'MetricName': 'SystemCompliancePercentage',
                        'Value': compliance_status.compliance_percentage,
                        'Unit': 'Percent',
                        'Timestamp': datetime.utcnow()
                    },
                    {
                        'MetricName': 'ComplianceViolations',
                        'Value': len(compliance_status.violations),
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Error performing compliance check: {e}")
    
    def _handle_sla_violation(self, violation_data: Dict[str, Any]) -> None:
        """
        Handle an SLA violation by issuing appropriate control commands.
        
        Args:
            violation_data: Violation details
            
        Validates: Requirements 4.2
        """
        try:
            agent_id = violation_data.get("agent_id")
            metric_type = violation_data.get("metric_type")
            severity = violation_data.get("severity")
            
            logger.warning(f"Handling SLA violation for {agent_id}: {metric_type} ({severity})")
            
            # Determine appropriate action based on metric type and severity
            if metric_type == "error_rate" and severity in ["HIGH", "CRITICAL"]:
                # High error rate - pause agent for investigation
                logger.info(f"Pausing {agent_id} due to high error rate")
                result = self.control_command.pause_processing(
                    agent_id=agent_id,
                    reason=f"SLA violation: High error rate ({severity})"
                )
                self.control_commands_issued += 1
                logger.info(f"Pause command result: {result.message}")
                
            elif metric_type == "processing_time_ms" and severity == "CRITICAL":
                # Critical processing time - trigger escalation
                logger.info(f"Escalating {agent_id} due to critical processing time")
                result = self.control_command.trigger_escalation(
                    resource_id=agent_id,
                    resource_type="agent",
                    escalation_level="ENGINEERING",
                    reason=f"SLA violation: Critical processing time"
                )
                self.control_commands_issued += 1
                logger.info(f"Escalation result: {result.message}")
                
            elif metric_type == "throughput_per_hour" and severity in ["HIGH", "CRITICAL"]:
                # Low throughput - could indicate scaling issue
                logger.info(f"Agent {agent_id} has low throughput - monitoring for scaling")
                # In a real implementation, this would trigger auto-scaling
                
        except Exception as e:
            logger.error(f"Error handling SLA violation: {e}")
    
    def _handle_compliance_violation(self, violation_data: Dict[str, Any]) -> None:
        """
        Handle a compliance violation by issuing appropriate control commands.
        
        Args:
            violation_data: Violation details
            
        Validates: Requirements 4.2
        """
        try:
            check_type = violation_data.get("check_type")
            resource_id = violation_data.get("resource_id")
            severity = violation_data.get("severity")
            
            logger.warning(f"Handling compliance violation: {check_type} for {resource_id} ({severity})")
            
            # Determine appropriate action based on check type and severity
            if check_type == "data_integrity" and severity in ["HIGH", "CRITICAL"]:
                # Data integrity issue - escalate to compliance
                logger.info(f"Escalating data integrity issue for {resource_id}")
                result = self.control_command.trigger_escalation(
                    resource_id=resource_id,
                    resource_type="trade",
                    escalation_level="COMPLIANCE",
                    reason=f"Compliance violation: Data integrity issue ({severity})",
                    details=violation_data
                )
                self.control_commands_issued += 1
                logger.info(f"Escalation result: {result.message}")
                
            elif check_type == "trade_source_routing" and severity in ["HIGH", "CRITICAL"]:
                # Routing issue - escalate to ops desk
                logger.info(f"Escalating routing issue for {resource_id}")
                result = self.control_command.trigger_escalation(
                    resource_id=resource_id,
                    resource_type="trade",
                    escalation_level="OPS_DESK",
                    reason=f"Compliance violation: Trade routing issue ({severity})",
                    details=violation_data
                )
                self.control_commands_issued += 1
                logger.info(f"Escalation result: {result.message}")
                
        except Exception as e:
            logger.error(f"Error handling compliance violation: {e}")
    
    def _emit_metrics(self) -> None:
        """Emit orchestrator metrics to CloudWatch."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='TradeMatchingSystem/Orchestrator',
                MetricData=[
                    {
                        'MetricName': 'EventsProcessed',
                        'Value': self.events_processed,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    },
                    {
                        'MetricName': 'SLAViolationsDetected',
                        'Value': self.sla_violations_detected,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    },
                    {
                        'MetricName': 'ComplianceViolationsDetected',
                        'Value': self.compliance_violations_detected,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    },
                    {
                        'MetricName': 'ControlCommandsIssued',
                        'Value': self.control_commands_issued,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
        except Exception as e:
            logger.debug(f"Error emitting metrics: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status including all agents.
        
        Returns:
            dict: System status summary
            
        Validates: Requirements 4.3, 4.5
        """
        try:
            # Get all active agents
            active_agents = self.registry.list_active_agents()
            
            # Get SLA status
            sla_status = self.sla_monitor.get_system_wide_sla_status()
            
            # Get compliance status
            compliance_status = self.compliance_checker.check_all_compliance(sample_size=20)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "total_agents": len(active_agents),
                "active_agents": [
                    {
                        "agent_id": agent.agent_id,
                        "agent_name": agent.agent_name,
                        "status": agent.deployment_status,
                        "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
                    }
                    for agent in active_agents
                ],
                "sla_status": {
                    "status": sla_status.status,
                    "compliance_percentage": sla_status.compliance_percentage,
                    "violations_count": len(sla_status.violations)
                },
                "compliance_status": {
                    "status": compliance_status.status,
                    "compliance_percentage": compliance_status.compliance_percentage,
                    "violations_count": len(compliance_status.violations)
                },
                "orchestrator_metrics": {
                    "events_processed": self.events_processed,
                    "sla_violations_detected": self.sla_violations_detected,
                    "compliance_violations_detected": self.compliance_violations_detected,
                    "control_commands_issued": self.control_commands_issued
                }
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "error": str(e),
                "message": "Failed to get system status"
            }
    
    def poll_and_process(self, max_messages: int = 10, wait_time_seconds: int = 20) -> None:
        """
        Poll SQS queue and process messages.
        
        Args:
            max_messages: Maximum number of messages to retrieve
            wait_time_seconds: Long polling wait time
            
        Validates: Requirements 3.1
        """
        logger.info(f"Polling queue: {self.monitoring_queue}")
        
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.monitoring_queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time_seconds,
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            
            if not messages:
                logger.debug("No messages received")
                return
            
            logger.info(f"Received {len(messages)} messages")
            
            for message in messages:
                try:
                    # Parse event message
                    event_message = StandardEventMessage.from_sqs_message(message['Body'])
                    
                    # Process event
                    result = self.process_event(event_message)
                    
                    if result['success']:
                        # Delete message from queue
                        self.sqs.delete_message(
                            QueueUrl=self.monitoring_queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        logger.debug(f"Message processed and deleted")
                    else:
                        logger.error(f"Message processing failed: {result.get('error')}")
                        # Message will be retried or sent to DLQ
                        
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Message will be retried or sent to DLQ
                    
        except Exception as e:
            logger.error(f"Error polling queue: {e}")
    
    def run(self, continuous: bool = True, poll_interval: int = 20) -> None:
        """
        Run the agent continuously or process once.
        
        Args:
            continuous: Run continuously if True, process once if False
            poll_interval: Polling interval in seconds
        """
        logger.info(f"Starting Orchestrator Agent (continuous={continuous})")
        
        # Register agent
        self.register()
        
        if continuous:
            import time
            while True:
                self.poll_and_process(wait_time_seconds=poll_interval)
                time.sleep(1)  # Small delay between polls
        else:
            self.poll_and_process(wait_time_seconds=poll_interval)


def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for Orchestrator Agent.
    
    This function is called by AgentCore Runtime when the agent is invoked.
    
    Args:
        payload: Event payload from SQS or direct invocation
        context: AgentCore context (optional)
        
    Returns:
        dict: Processing result
        
    Validates: Requirements 2.1, 2.2, 3.1
    """
    logger.info("Orchestrator Agent invoked via AgentCore Runtime")
    
    # Initialize agent
    agent = OrchestratorAgent()
    
    # Check if this is a status request
    if payload.get("action") == "get_status":
        return agent.get_system_status()
    
    # Check if payload is an SQS event or direct invocation
    if 'event_type' in payload:
        # Direct invocation with StandardEventMessage
        event_message = StandardEventMessage(**payload)
        result = agent.process_event(event_message)
    else:
        # Assume it's a monitoring event payload
        # Create a StandardEventMessage
        event_message = StandardEventMessage(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=payload.get("event_type", "MONITORING_EVENT"),
            source_agent=payload.get("source_agent", "unknown"),
            correlation_id=payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}"),
            payload=payload
        )
        result = agent.process_event(event_message)
    
    return result


if __name__ == "__main__":
    """
    Run Orchestrator Agent locally for testing.
    """
    import sys
    
    # Initialize agent
    agent = OrchestratorAgent()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "register":
        # Just register the agent
        result = agent.register()
        print(json.dumps(result, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        # Get system status
        status = agent.get_system_status()
        print(json.dumps(status, indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test with a sample event
        test_event = StandardEventMessage(
            event_id="evt_test_orch_001",
            event_type=EventTaxonomy.TRADE_EXTRACTED,
            source_agent="trade_extraction_agent",
            correlation_id="corr_test_orch_001",
            payload={
                "trade_id": "TEST123",
                "processing_time_ms": 15000
            },
            metadata={}
        )
        
        result = agent.process_event(test_event)
        print(json.dumps(result, indent=2, default=str))
    else:
        # Run continuously
        agent.run(continuous=True)
