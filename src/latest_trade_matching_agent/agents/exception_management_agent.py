"""
Exception Management Agent

This agent handles exception classification, scoring, triage, delegation,
and reinforcement learning for continuous improvement.

Requirements: 3.5, 8.1, 8.2, 8.3, 8.4, 8.5
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import boto3

from ..models.exception import (
    ExceptionRecord,
    ExceptionType,
    ResolutionOutcome,
    ResolutionStatus
)
from ..models.registry import AgentRegistryEntry
from ..models.audit import AuditRecord, ActionType, ActionOutcome
from ..exception_handling.classifier import classify_exception
from ..exception_handling.scorer import compute_severity_score, compute_severity_breakdown
from ..exception_handling.triage import triage_exception, get_triage_summary
from ..exception_handling.delegation import delegate_exception, ExceptionDelegator, update_exception_status
from ..exception_handling.rl_handler import RLExceptionHandler, create_default_rl_handler


class ExceptionManagementAgent:
    """
    Exception Management Agent with event-driven architecture.
    
    This agent:
    1. Subscribes to exception-events SQS queue
    2. Classifies and scores exceptions
    3. Triages and delegates to appropriate queues
    4. Tracks exception lifecycle in ExceptionsTable
    5. Updates RL model with resolution outcomes
    6. Registers in AgentRegistry
    
    Requirements:
        - 3.5: Event-driven architecture with SQS
        - 8.1: Classify exceptions with reason codes
        - 8.2: Score and triage exceptions
        - 8.3: Delegate to appropriate handlers
        - 8.4: Track exception lifecycle
        - 8.5: Learn from resolution patterns with RL
    """
    
    def __init__(
        self,
        region_name: str = "us-east-1",
        exception_queue_name: str = "exception-events",
        rl_model_path: Optional[str] = None
    ):
        """
        Initialize the Exception Management Agent.
        
        Args:
            region_name: AWS region name
            exception_queue_name: Name of the exception events queue
            rl_model_path: Optional path to load RL model from
        """
        self.region_name = region_name
        self.exception_queue_name = exception_queue_name
        self.agent_id = f"exception_mgmt_agent_{uuid.uuid4().hex[:8]}"
        
        # AWS clients
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        
        # Get queue URL
        self.exception_queue_url = self._get_queue_url(exception_queue_name)
        
        # Initialize delegator
        self.delegator = ExceptionDelegator(region_name=region_name)
        
        # Initialize RL handler
        self.rl_handler = create_default_rl_handler()
        if rl_model_path:
            try:
                self.rl_handler.load_model(rl_model_path)
                print(f"Loaded RL model from {rl_model_path}")
            except Exception as e:
                print(f"Warning: Could not load RL model: {e}")
        
        # Statistics
        self.stats = {
            "exceptions_processed": 0,
            "exceptions_triaged": 0,
            "exceptions_delegated": 0,
            "rl_updates": 0,
            "errors": 0,
        }
        
        print(f"Initialized Exception Management Agent: {self.agent_id}")
    
    def _get_queue_url(self, queue_name: str) -> str:
        """Get SQS queue URL by name."""
        try:
            response = self.sqs.get_queue_url(QueueName=queue_name)
            return response['QueueUrl']
        except Exception as e:
            print(f"Error getting queue URL for {queue_name}: {e}")
            raise
    
    def register_agent(self) -> bool:
        """
        Register agent in AgentRegistry.
        
        Returns:
            bool: True if registered successfully
            
        Requirements:
            - 3.5: Register agent in AgentRegistry
        """
        try:
            registry_table = self.dynamodb.Table("AgentRegistry")
            
            entry = AgentRegistryEntry(
                agent_id=self.agent_id,
                agent_name="Exception Management Agent",
                agent_type="EXCEPTION_HANDLER",
                version="1.0.0",
                capabilities=[
                    "exception_classification",
                    "severity_scoring",
                    "triage",
                    "delegation",
                    "rl_learning"
                ],
                event_subscriptions=["exception-events", "matching-exception-events", "processing-error-events"],
                event_publications=["ops-desk-queue", "senior-ops-queue", "compliance-queue", "engineering-queue"],
                sla_targets={
                    "triage_time_seconds": 60,
                    "delegation_time_seconds": 30,
                },
                deployment_status="ACTIVE"
            )
            
            registry_table.put_item(Item=entry.to_dynamodb_format())
            
            print(f"Registered agent {self.agent_id} in AgentRegistry")
            return True
            
        except Exception as e:
            print(f"Error registering agent: {e}")
            return False
    
    def process_exception_event(self, event_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single exception event.
        
        This is the main processing function that:
        1. Parses the event message
        2. Creates ExceptionRecord
        3. Classifies the exception
        4. Scores severity
        5. Triages the exception
        6. Delegates to appropriate handler
        7. Records in RL for learning
        
        Args:
            event_message: SQS event message
        
        Returns:
            dict: Processing result
            
        Requirements:
            - 8.1: Classify and score exceptions
            - 8.2: Triage exceptions
            - 8.3: Delegate to appropriate queues
            - 8.4: Track exception lifecycle
            - 8.5: Record for RL learning
        """
        try:
            self.stats["exceptions_processed"] += 1
            
            # Parse event message
            exception_data = self._parse_event_message(event_message)
            
            # Create ExceptionRecord
            exception = self._create_exception_record(exception_data)
            
            # Log exception with full context (Requirement 8.1)
            self._log_exception(exception)
            
            # Classify exception
            classification = classify_exception(exception)
            print(f"Classified exception {exception.exception_id} as {classification.value}")
            
            # Compute severity score (with RL adjustment)
            rl_adjustment = self.rl_handler.get_severity_adjustment(exception)
            severity_score = compute_severity_score(exception, rl_adjustment=rl_adjustment)
            print(f"Severity score for {exception.exception_id}: {severity_score}")
            
            # Get detailed severity breakdown
            severity_breakdown = compute_severity_breakdown(exception)
            
            # Triage exception (with RL policy)
            triage_result = triage_exception(
                exception=exception,
                severity_score=severity_score,
                rl_policy=self.rl_handler
            )
            self.stats["exceptions_triaged"] += 1
            print(f"Triaged exception {exception.exception_id}: {triage_result.routing.value}")
            
            # Get triage summary
            triage_summary = get_triage_summary(triage_result)
            
            # Delegate to appropriate handler
            delegation_result = delegate_exception(
                exception=exception,
                triage_result=triage_result,
                delegator=self.delegator
            )
            self.stats["exceptions_delegated"] += 1
            print(f"Delegated exception {exception.exception_id} to {delegation_result.assigned_to}")
            
            # Record episode for RL learning
            self.rl_handler.record_episode(
                exception_id=exception.exception_id,
                state=exception.to_state_vector(),
                action=triage_result.routing.value,
                context=exception_data
            )
            
            # Create audit record
            self._create_audit_record(
                exception=exception,
                triage_result=triage_result,
                delegation_result=delegation_result
            )
            
            return {
                "status": "success",
                "exception_id": exception.exception_id,
                "classification": classification.value,
                "severity_score": severity_score,
                "severity_breakdown": severity_breakdown,
                "triage": triage_summary,
                "delegation": {
                    "status": delegation_result.status,
                    "assigned_to": delegation_result.assigned_to,
                    "tracking_id": delegation_result.tracking_id,
                    "queue_name": delegation_result.queue_name,
                },
            }
            
        except Exception as e:
            self.stats["errors"] += 1
            print(f"Error processing exception event: {e}")
            return {
                "status": "error",
                "error": str(e),
            }
    
    def _parse_event_message(self, event_message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse SQS event message."""
        # Handle both direct dict and SQS message format
        if "Body" in event_message:
            body = json.loads(event_message["Body"])
        else:
            body = event_message
        
        return body
    
    def _create_exception_record(self, exception_data: Dict[str, Any]) -> ExceptionRecord:
        """Create ExceptionRecord from event data."""
        # Generate exception ID if not provided
        exception_id = exception_data.get("exception_id", f"exc_{uuid.uuid4().hex[:12]}")
        
        # Parse exception type
        exception_type_str = exception_data.get("exception_type", "PROCESSING_ERROR")
        try:
            exception_type = ExceptionType(exception_type_str)
        except ValueError:
            exception_type = ExceptionType.PROCESSING_ERROR
        
        # Create exception record
        return ExceptionRecord(
            exception_id=exception_id,
            timestamp=datetime.fromisoformat(exception_data.get("timestamp", datetime.utcnow().isoformat())),
            exception_type=exception_type,
            event_type=exception_data.get("event_type", "EXCEPTION_RAISED"),
            trade_id=exception_data.get("trade_id"),
            agent_id=exception_data.get("agent_id", "unknown"),
            match_score=exception_data.get("match_score"),
            reason_codes=exception_data.get("reason_codes", []),
            context=exception_data.get("context", {}),
            error_message=exception_data.get("error_message", "Unknown error"),
            stack_trace=exception_data.get("stack_trace"),
            retry_count=exception_data.get("retry_count", 0),
            correlation_id=exception_data.get("correlation_id"),
        )
    
    def _log_exception(self, exception: ExceptionRecord) -> None:
        """
        Log exception with full context.
        
        Requirements:
            - 8.1: Log all errors with full context
        """
        log_entry = {
            "timestamp": exception.timestamp.isoformat(),
            "exception_id": exception.exception_id,
            "exception_type": exception.exception_type.value,
            "event_type": exception.event_type,
            "trade_id": exception.trade_id,
            "agent_id": exception.agent_id,
            "error_message": exception.error_message,
            "reason_codes": exception.reason_codes,
            "match_score": exception.match_score,
            "retry_count": exception.retry_count,
            "correlation_id": exception.correlation_id,
            "context": exception.context,
        }
        
        print(f"EXCEPTION LOG: {json.dumps(log_entry, indent=2)}")
    
    def _create_audit_record(
        self,
        exception: ExceptionRecord,
        triage_result: Any,
        delegation_result: Any
    ) -> None:
        """
        Create audit record for exception handling.
        
        Requirements:
            - 8.4: Update audit trail
        """
        try:
            audit_table = self.dynamodb.Table("AuditTrail")
            
            audit_record = AuditRecord(
                record_id=f"audit_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.utcnow(),
                agent_id=self.agent_id,
                action_type=ActionType.EXCEPTION_HANDLED,
                resource_id=exception.exception_id,
                outcome=ActionOutcome.SUCCESS if delegation_result.status == "DELEGATED" else ActionOutcome.FAILURE,
                user_id=None,
                details={
                    "exception_type": exception.exception_type.value,
                    "severity": triage_result.severity.value,
                    "severity_score": triage_result.severity_score,
                    "routing": triage_result.routing.value,
                    "assigned_to": delegation_result.assigned_to,
                    "tracking_id": delegation_result.tracking_id,
                }
            )
            
            audit_table.put_item(Item=audit_record.to_dynamodb_format())
            
        except Exception as e:
            print(f"Error creating audit record: {e}")
    
    def update_with_resolution(
        self,
        exception_id: str,
        resolution_outcome: ResolutionOutcome
    ) -> bool:
        """
        Update RL model with resolution outcome.
        
        This should be called when an exception is resolved to provide
        feedback to the RL model for learning.
        
        Args:
            exception_id: Exception identifier
            resolution_outcome: Resolution outcome
        
        Returns:
            bool: True if updated successfully
            
        Requirements:
            - 8.5: Update RL model with resolution outcomes
        """
        try:
            # Update RL model
            self.rl_handler.update_with_resolution(exception_id, resolution_outcome)
            self.stats["rl_updates"] += 1
            
            # Update exception status in DynamoDB
            update_exception_status(
                exception_id=exception_id,
                status=ResolutionStatus.RESOLVED,
                resolution_notes=resolution_outcome.resolution_notes,
                region_name=self.region_name
            )
            
            print(f"Updated RL model with resolution for exception {exception_id}")
            return True
            
        except Exception as e:
            print(f"Error updating with resolution: {e}")
            return False
    
    def poll_and_process(self, max_messages: int = 10, wait_time: int = 20) -> int:
        """
        Poll exception queue and process messages.
        
        Args:
            max_messages: Maximum number of messages to retrieve
            wait_time: Long polling wait time in seconds
        
        Returns:
            int: Number of messages processed
        """
        try:
            # Receive messages from queue
            response = self.sqs.receive_message(
                QueueUrl=self.exception_queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time,
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            
            if not messages:
                print("No messages in exception queue")
                return 0
            
            print(f"Received {len(messages)} exception messages")
            
            # Process each message
            processed = 0
            for message in messages:
                result = self.process_exception_event(message)
                
                if result["status"] == "success":
                    # Delete message from queue
                    self.sqs.delete_message(
                        QueueUrl=self.exception_queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    processed += 1
            
            return processed
            
        except Exception as e:
            print(f"Error polling queue: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "agent_id": self.agent_id,
            "stats": self.stats,
            "rl_stats": self.rl_handler.get_statistics(),
        }
    
    def save_rl_model(self, filepath: str) -> None:
        """Save RL model to file."""
        self.rl_handler.save_model(filepath)
    
    def run(self, duration_seconds: Optional[int] = None) -> None:
        """
        Run the agent continuously.
        
        Args:
            duration_seconds: Optional duration to run (None = run indefinitely)
        """
        print(f"Starting Exception Management Agent {self.agent_id}")
        
        # Register agent
        self.register_agent()
        
        start_time = datetime.utcnow()
        
        try:
            while True:
                # Check duration
                if duration_seconds:
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    if elapsed >= duration_seconds:
                        print(f"Reached duration limit of {duration_seconds} seconds")
                        break
                
                # Poll and process messages
                processed = self.poll_and_process()
                
                if processed > 0:
                    print(f"Processed {processed} exceptions")
                    print(f"Statistics: {self.get_statistics()}")
                
        except KeyboardInterrupt:
            print("\nStopping Exception Management Agent")
        finally:
            print(f"Final statistics: {self.get_statistics()}")


def main():
    """Main entry point for the Exception Management Agent."""
    import os
    
    # Get configuration from environment
    region_name = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    exception_queue_name = os.getenv("EXCEPTION_QUEUE_NAME", "exception-events")
    rl_model_path = os.getenv("RL_MODEL_PATH")
    
    # Create and run agent
    agent = ExceptionManagementAgent(
        region_name=region_name,
        exception_queue_name=exception_queue_name,
        rl_model_path=rl_model_path
    )
    
    # Run agent
    agent.run()


if __name__ == "__main__":
    main()
