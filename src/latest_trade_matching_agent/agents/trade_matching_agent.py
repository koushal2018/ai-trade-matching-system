"""
Trade Matching Agent

This agent performs fuzzy matching between bank and counterparty trades,
computes match scores, classifies results, and generates detailed reports.
It subscribes to matching-events and publishes results to hitl-review-queue
or exception-events queue based on decision status.

Requirements: 3.4, 7.1, 7.2, 7.3, 7.4, 7.5
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import boto3
import logging

# Import models
from ..models.trade import CanonicalTradeModel
from ..models.matching import MatchingResult, MatchClassification, DecisionStatus
from ..models.events import (
    EventTaxonomy,
    StandardEventMessage,
    MatchCompletedEvent,
    MatchingExceptionEvent,
    HITLRequiredEvent,
    ExceptionRaisedEvent
)
from ..models.registry import AgentRegistry, AgentRegistryEntry, ScalingConfig

# Import matching logic
from ..matching import (
    fuzzy_match,
    compute_match_score,
    classify_match,
    generate_report
)
from ..matching.classifier import create_matching_result, check_data_integrity

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradeMatchingAgent:
    """
    Trade Matching Agent for identifying discrepancies between bank and counterparty trades.
    
    This agent:
    1. Subscribes to matching-events SQS queue
    2. Retrieves trades from both DynamoDB tables
    3. Performs fuzzy matching with tolerances
    4. Computes match scores (0.0 to 1.0)
    5. Classifies results and determines decision status
    6. Generates and saves detailed reports to S3
    7. Publishes results to hitl-review-queue or exception-events queue
    8. Registers itself in AgentRegistry
    
    Validates: Requirements 3.4, 7.1, 7.2, 7.3, 7.4, 7.5
    """
    
    def __init__(
        self,
        agent_id: str = "trade_matching_agent",
        region_name: str = "us-east-1",
        s3_bucket: Optional[str] = None,
        matching_events_queue: str = "trade-matching-system-matching-events-production",
        hitl_review_queue: str = "trade-matching-system-hitl-review-production",
        exception_events_queue: str = "trade-matching-system-exception-events-production",
        bank_table_name: str = "BankTradeData",
        counterparty_table_name: str = "CounterpartyTradeData"
    ):
        """
        Initialize Trade Matching Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            region_name: AWS region
            s3_bucket: S3 bucket for report storage
            matching_events_queue: SQS queue for matching events
            hitl_review_queue: SQS queue for HITL reviews
            exception_events_queue: SQS queue for exception events
            bank_table_name: DynamoDB table for bank trades
            counterparty_table_name: DynamoDB table for counterparty trades
        """
        self.agent_id = agent_id
        self.region_name = region_name
        self.s3_bucket = s3_bucket or os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
        self.matching_events_queue = matching_events_queue
        self.hitl_review_queue = hitl_review_queue
        self.exception_events_queue = exception_events_queue
        self.bank_table_name = bank_table_name
        self.counterparty_table_name = counterparty_table_name
        
        # Initialize AWS clients
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.s3 = boto3.client('s3', region_name=region_name)
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        
        # Initialize registry
        self.registry = AgentRegistry(region_name=region_name)
        
        # Get queue URLs
        self.matching_events_queue_url = self._get_queue_url(matching_events_queue)
        self.hitl_review_queue_url = self._get_queue_url(hitl_review_queue)
        self.exception_events_queue_url = self._get_queue_url(exception_events_queue)
        
        logger.info(f"Trade Matching Agent initialized: {agent_id}")
    
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
            agent_name="Trade Matching Agent",
            agent_type="MATCHER",
            version="1.0.0",
            capabilities=[
                "fuzzy_matching",
                "match_scoring",
                "result_classification",
                "report_generation",
                "data_integrity_checking"
            ],
            event_subscriptions=[self.matching_events_queue],
            event_publications=[self.hitl_review_queue, self.exception_events_queue],
            sla_targets={
                "processing_time_ms": 20000.0,  # 20 seconds per match
                "throughput_per_hour": 180.0,   # 180 matches per hour
                "error_rate": 0.03              # 3% error rate
            },
            scaling_config=ScalingConfig(
                min_instances=1,
                max_instances=10,
                target_queue_depth=30,
                scale_up_threshold=0.8,
                scale_down_threshold=0.2
            ),
            deployment_status="ACTIVE"
        )
        
        result = self.registry.register_agent(entry)
        logger.info(f"Agent registration result: {result}")
        return result
    
    def match_trades(self, event_message) -> Dict[str, Any]:
        """
        Perform trade matching between bank and counterparty trades.
        
        Args:
            event_message: StandardEventMessage from SQS or dict payload
            
        Returns:
            dict: Matching result
            
        Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5
        """
        start_time = datetime.utcnow()
        
        # Handle both StandardEventMessage objects and dict payloads
        if isinstance(event_message, StandardEventMessage):
            correlation_id = event_message.correlation_id
            payload = event_message.payload
        elif isinstance(event_message, dict):
            correlation_id = event_message.get("correlation_id", str(uuid.uuid4()))
            payload = event_message
        else:
            raise ValueError(f"Invalid event_message type: {type(event_message)}")
        
        try:
            # Extract payload fields
            trade_id = payload.get("trade_id")
            source_type = payload.get("source_type")
            
            logger.info(f"Matching trade: {trade_id} (source: {source_type})")
            
            # Validate inputs
            if not trade_id:
                raise ValueError("Missing required field: trade_id")
            
            # Step 1: Retrieve trades from both DynamoDB tables
            logger.info(f"Step 1: Retrieving trades from DynamoDB")
            
            bank_trade = self._get_trade_from_dynamodb(self.bank_table_name, trade_id)
            counterparty_trade = self._get_trade_from_dynamodb(self.counterparty_table_name, trade_id)
            
            logger.info(
                f"Retrieved trades: bank={'found' if bank_trade else 'not found'}, "
                f"counterparty={'found' if counterparty_trade else 'not found'}"
            )
            
            # Step 2: Check data integrity
            logger.info("Step 2: Checking data integrity")
            
            if bank_trade and counterparty_trade:
                is_valid, integrity_errors = check_data_integrity(bank_trade, counterparty_trade)
                
                if not is_valid:
                    logger.error(f"Data integrity check failed: {integrity_errors}")
                    # Create DATA_ERROR result
                    matching_result = MatchingResult(
                        trade_id=trade_id,
                        classification=MatchClassification.DATA_ERROR,
                        match_score=0.0,
                        decision_status=DecisionStatus.EXCEPTION,
                        reason_codes=integrity_errors,
                        bank_trade=bank_trade,
                        counterparty_trade=counterparty_trade,
                        differences=[],
                        confidence_score=1.0,
                        requires_hitl=False,
                        matching_timestamp=datetime.utcnow().isoformat()
                    )
                    
                    # Generate report
                    report_path = generate_report(matching_result, self.s3_bucket)
                    matching_result.report_path = report_path
                    
                    # Publish exception event
                    self._publish_exception_event(matching_result, correlation_id)
                    
                    return {
                        "success": True,
                        "trade_id": trade_id,
                        "classification": "DATA_ERROR",
                        "decision_status": "EXCEPTION",
                        "report_path": report_path
                    }
            
            # Step 3: Perform fuzzy matching
            logger.info("Step 3: Performing fuzzy matching")
            
            if not bank_trade or not counterparty_trade:
                # Missing trade - create appropriate result
                logger.warning(f"Missing trade data for {trade_id}")
                
                match_result = None
                match_score = 0.0
            else:
                match_result = fuzzy_match(bank_trade, counterparty_trade)
                
                # Step 4: Compute match score
                logger.info("Step 4: Computing match score")
                match_score = compute_match_score(match_result)
                
                logger.info(f"Match score computed: {match_score:.2f}")
            
            # Step 5: Classify result and determine decision status
            logger.info("Step 5: Classifying match result")
            
            matching_result = create_matching_result(
                trade_id=trade_id,
                match_score=match_score,
                match_result=match_result if match_result else None,
                bank_trade=bank_trade,
                counterparty_trade=counterparty_trade,
                matching_timestamp=datetime.utcnow().isoformat()
            )
            
            logger.info(
                f"Classification: {matching_result.classification.value}, "
                f"Decision: {matching_result.decision_status.value}"
            )
            
            # Step 6: Generate and save report to S3
            logger.info("Step 6: Generating matching report")
            
            report_path = generate_report(matching_result, self.s3_bucket)
            matching_result.report_path = report_path
            
            logger.info(f"Report saved to: {report_path}")
            
            # Step 7: Publish results based on decision status
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if matching_result.decision_status == DecisionStatus.AUTO_MATCH:
                # Publish MATCH_COMPLETED event (for audit/monitoring)
                logger.info("Step 7: Publishing MATCH_COMPLETED event")
                self._publish_match_completed_event(matching_result, correlation_id, processing_time_ms)
                
            elif matching_result.decision_status == DecisionStatus.ESCALATE:
                # Publish HITL_REQUIRED event
                logger.info("Step 7: Publishing HITL_REQUIRED event")
                self._publish_hitl_required_event(matching_result, correlation_id, processing_time_ms)
                
            else:  # EXCEPTION
                # Publish MATCHING_EXCEPTION event
                logger.info("Step 7: Publishing MATCHING_EXCEPTION event")
                self._publish_exception_event(matching_result, correlation_id, processing_time_ms)
            
            # Update agent metrics
            self.registry.update_agent_status(
                agent_id=self.agent_id,
                metrics={
                    "last_processing_time_ms": processing_time_ms,
                    "total_processed": 1.0,
                    "last_match_score": match_score
                },
                last_heartbeat=datetime.utcnow()
            )
            
            return {
                "success": True,
                "trade_id": trade_id,
                "classification": matching_result.classification.value,
                "match_score": match_score,
                "decision_status": matching_result.decision_status.value,
                "report_path": report_path,
                "processing_time_ms": processing_time_ms
            }
            
        except Exception as e:
            logger.error(f"Error matching trade: {e}")
            
            # Publish exception event
            exception_event = ExceptionRaisedEvent(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                source_agent=self.agent_id,
                correlation_id=correlation_id,
                payload={
                    "exception_id": f"exc_{uuid.uuid4().hex[:12]}",
                    "exception_type": "MATCHING_FAILED",
                    "trade_id": payload.get("trade_id", "unknown"),
                    "error_message": str(e),
                    "reason_codes": ["MATCHING_FAILED"]
                },
                metadata={
                    "source_type": payload.get("source_type", "unknown")
                }
            )
            
            self.sqs.send_message(
                QueueUrl=self.exception_events_queue_url,
                MessageBody=exception_event.to_sqs_message()
            )
            
            logger.info(f"Published EXCEPTION_RAISED event to {self.exception_events_queue}")
            
            return {
                "success": False,
                "error": str(e),
                "trade_id": payload.get("trade_id", "unknown")
            }
    
    def _get_trade_from_dynamodb(self, table_name: str, trade_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve trade from DynamoDB table.
        
        Args:
            table_name: DynamoDB table name
            trade_id: Trade identifier
            
        Returns:
            Trade data in DynamoDB format or None if not found
        """
        try:
            response = self.dynamodb.get_item(
                TableName=table_name,
                Key={"Trade_ID": {"S": trade_id}}
            )
            
            return response.get('Item')
            
        except self.dynamodb.exceptions.ResourceNotFoundException:
            logger.warning(f"Table not found: {table_name}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving trade from {table_name}: {e}")
            return None
    
    def _publish_match_completed_event(
        self,
        matching_result: MatchingResult,
        correlation_id: str,
        processing_time_ms: float
    ) -> None:
        """Publish MATCH_COMPLETED event for audit/monitoring."""
        event = MatchCompletedEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            source_agent=self.agent_id,
            correlation_id=correlation_id,
            payload={
                "trade_id": matching_result.trade_id,
                "classification": matching_result.classification.value,
                "match_score": matching_result.match_score,
                "decision_status": matching_result.decision_status.value,
                "report_path": matching_result.report_path,
                "processing_time_ms": processing_time_ms
            },
            metadata={
                "reason_codes": matching_result.reason_codes,
                "confidence_score": matching_result.confidence_score,
                "differences_count": len(matching_result.differences)
            }
        )
        
        # For AUTO_MATCH, we might send to a monitoring queue or just log
        # For now, log the event
        logger.info(f"Match completed: {event.to_sqs_message()}")
    
    def _publish_hitl_required_event(
        self,
        matching_result: MatchingResult,
        correlation_id: str,
        processing_time_ms: float
    ) -> None:
        """Publish HITL_REQUIRED event to hitl-review-queue."""
        event = HITLRequiredEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            source_agent=self.agent_id,
            correlation_id=correlation_id,
            payload={
                "review_id": f"review_{uuid.uuid4().hex[:12]}",
                "trade_id": matching_result.trade_id,
                "match_score": matching_result.match_score,
                "report_path": matching_result.report_path,
                "bank_trade": matching_result.bank_trade,
                "counterparty_trade": matching_result.counterparty_trade,
                "differences": [diff.model_dump() for diff in matching_result.differences]
            },
            metadata={
                "reason_codes": matching_result.reason_codes,
                "confidence_score": matching_result.confidence_score,
                "processing_time_ms": processing_time_ms
            }
        )
        
        self.sqs.send_message(
            QueueUrl=self.hitl_review_queue_url,
            MessageBody=event.to_sqs_message()
        )
        
        logger.info(f"Published HITL_REQUIRED event to {self.hitl_review_queue}")
    
    def _publish_exception_event(
        self,
        matching_result: MatchingResult,
        correlation_id: str,
        processing_time_ms: float = 0.0
    ) -> None:
        """Publish MATCHING_EXCEPTION event to exception-events queue."""
        event = MatchingExceptionEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            source_agent=self.agent_id,
            correlation_id=correlation_id,
            payload={
                "exception_id": f"exc_{uuid.uuid4().hex[:12]}",
                "trade_id": matching_result.trade_id,
                "match_score": matching_result.match_score,
                "reason_codes": matching_result.reason_codes,
                "report_path": matching_result.report_path
            },
            metadata={
                "classification": matching_result.classification.value,
                "confidence_score": matching_result.confidence_score,
                "processing_time_ms": processing_time_ms
            }
        )
        
        self.sqs.send_message(
            QueueUrl=self.exception_events_queue_url,
            MessageBody=event.to_sqs_message()
        )
        
        logger.info(f"Published MATCHING_EXCEPTION event to {self.exception_events_queue}")
    
    def poll_and_process(self, max_messages: int = 1, wait_time_seconds: int = 20) -> None:
        """
        Poll SQS queue and process messages.
        
        Args:
            max_messages: Maximum number of messages to retrieve
            wait_time_seconds: Long polling wait time
            
        Validates: Requirements 3.4
        """
        logger.info(f"Polling queue: {self.matching_events_queue}")
        
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.matching_events_queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time_seconds,
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            
            if not messages:
                logger.info("No messages received")
                return
            
            logger.info(f"Received {len(messages)} messages")
            
            for message in messages:
                try:
                    # Parse event message
                    event_message = StandardEventMessage.from_sqs_message(message['Body'])
                    
                    # Match trades
                    result = self.match_trades(event_message)
                    
                    if result['success']:
                        # Delete message from queue
                        self.sqs.delete_message(
                            QueueUrl=self.matching_events_queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        logger.info(f"Message processed and deleted: {result['trade_id']}")
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
        logger.info(f"Starting Trade Matching Agent (continuous={continuous})")
        
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
    AgentCore Runtime entrypoint for Trade Matching Agent.
    
    This function is called by AgentCore Runtime when the agent is invoked.
    
    Args:
        payload: Event payload from SQS or direct invocation
        context: AgentCore context (optional)
        
    Returns:
        dict: Matching result
        
    Validates: Requirements 2.1, 2.2, 3.4
    """
    logger.info("Trade Matching Agent invoked via AgentCore Runtime")
    
    # Initialize agent
    agent = TradeMatchingAgent()
    
    # Check if payload is an SQS event or direct invocation
    if 'event_type' in payload:
        # Direct invocation with StandardEventMessage
        event_message = StandardEventMessage(**payload)
        result = agent.match_trades(event_message)
    else:
        # Assume it's a raw matching payload
        # Create a StandardEventMessage
        event_message = StandardEventMessage(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=EventTaxonomy.TRADE_EXTRACTED,
            source_agent="trade_extraction_agent",
            correlation_id=payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}"),
            payload=payload
        )
        result = agent.match_trades(event_message)
    
    return result


if __name__ == "__main__":
    """
    Run Trade Matching Agent locally for testing.
    """
    import sys
    
    # Initialize agent
    agent = TradeMatchingAgent()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "register":
        # Just register the agent
        result = agent.register()
        print(json.dumps(result, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test with a sample event
        test_event = StandardEventMessage(
            event_id="evt_test_003",
            event_type=EventTaxonomy.TRADE_EXTRACTED,
            source_agent="trade_extraction_agent",
            correlation_id="corr_test_003",
            payload={
                "trade_id": "GCS382857",
                "source_type": "COUNTERPARTY",
                "table_name": "CounterpartyTradeData",
                "processing_time_ms": 12500
            },
            metadata={
                "extraction_confidence": 0.92,
                "fields_extracted": 28
            }
        )
        
        result = agent.match_trades(test_event)
        print(json.dumps(result, indent=2, default=str))
    else:
        # Run continuously
        agent.run(continuous=True)
