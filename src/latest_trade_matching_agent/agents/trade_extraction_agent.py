"""
Trade Data Extraction Agent

This agent extracts structured trade data from canonical adapter output and
stores it in the appropriate DynamoDB table. It subscribes to extraction-events
and publishes TRADE_EXTRACTED events.

Requirements: 3.3, 6.1, 6.2, 6.3, 6.4, 6.5
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import boto3
import logging

# Import models
from ..models.adapter import CanonicalAdapterOutput
from ..models.trade import CanonicalTradeModel
from ..models.events import (
    EventTaxonomy,
    StandardEventMessage,
    TradeExtractedEvent,
    ExceptionRaisedEvent
)
from ..models.registry import AgentRegistry, AgentRegistryEntry, ScalingConfig

# Import tools
from ..tools.llm_extraction_tool import LLMExtractionTool
from ..tools.trade_source_classifier import TradeSourceClassifier

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradeDataExtractionAgent:
    """
    Trade Data Extraction Agent for parsing unstructured text into canonical trade model.
    
    This agent:
    1. Subscribes to extraction-events SQS queue
    2. Reads canonical adapter output from S3
    3. Extracts trade data using LLM
    4. Classifies trade source (BANK or COUNTERPARTY)
    5. Validates against canonical trade model
    6. Stores in appropriate DynamoDB table via boto3
    7. Publishes TRADE_EXTRACTED events to matching-events queue
    8. Handles errors and publishes to exception-events queue
    9. Registers itself in AgentRegistry
    
    Validates: Requirements 3.3, 6.1, 6.2, 6.3, 6.4, 6.5
    """
    
    def __init__(
        self,
        agent_id: str = "trade_extraction_agent",
        region_name: str = "us-east-1",
        s3_bucket: Optional[str] = None,
        extraction_events_queue: str = "trade-matching-system-extraction-events-production",
        matching_events_queue: str = "trade-matching-system-matching-events-production",
        exception_events_queue: str = "trade-matching-system-exception-events-production",
        bank_table_name: str = "BankTradeData",
        counterparty_table_name: str = "CounterpartyTradeData"
    ):
        """
        Initialize Trade Data Extraction Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            region_name: AWS region
            s3_bucket: S3 bucket for storage
            extraction_events_queue: SQS queue for extraction events
            matching_events_queue: SQS queue for matching events
            exception_events_queue: SQS queue for exception events
            bank_table_name: DynamoDB table for bank trades
            counterparty_table_name: DynamoDB table for counterparty trades
        """
        self.agent_id = agent_id
        self.region_name = region_name
        self.s3_bucket = s3_bucket or os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
        self.extraction_events_queue = extraction_events_queue
        self.matching_events_queue = matching_events_queue
        self.exception_events_queue = exception_events_queue
        self.bank_table_name = bank_table_name
        self.counterparty_table_name = counterparty_table_name
        
        # Initialize AWS clients
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.s3 = boto3.client('s3', region_name=region_name)
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        
        # Initialize tools
        self.llm_extraction_tool = LLMExtractionTool(region_name=region_name)
        self.trade_source_classifier = TradeSourceClassifier(region_name=region_name)
        
        # Initialize registry
        self.registry = AgentRegistry(region_name=region_name)
        
        # Get queue URLs
        self.extraction_events_queue_url = self._get_queue_url(extraction_events_queue)
        self.matching_events_queue_url = self._get_queue_url(matching_events_queue)
        self.exception_events_queue_url = self._get_queue_url(exception_events_queue)
        
        logger.info(f"Trade Data Extraction Agent initialized: {agent_id}")
    
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
            agent_name="Trade Data Extraction Agent",
            agent_type="EXTRACTOR",
            version="1.0.0",
            capabilities=[
                "trade_extraction",
                "llm_parsing",
                "source_classification",
                "dynamodb_storage",
                "canonical_trade_validation"
            ],
            event_subscriptions=[self.extraction_events_queue],
            event_publications=[self.matching_events_queue, self.exception_events_queue],
            sla_targets={
                "processing_time_ms": 15000.0,  # 15 seconds per trade
                "throughput_per_hour": 240.0,   # 240 trades per hour
                "error_rate": 0.05              # 5% error rate
            },
            scaling_config=ScalingConfig(
                min_instances=1,
                max_instances=10,
                target_queue_depth=50,
                scale_up_threshold=0.8,
                scale_down_threshold=0.2
            ),
            deployment_status="ACTIVE"
        )
        
        result = self.registry.register_agent(entry)
        logger.info(f"Agent registration result: {result}")
        return result
    
    def extract_trade(self, event_message) -> Dict[str, Any]:
        """
        Extract trade data from canonical adapter output.
        
        Args:
            event_message: StandardEventMessage from SQS or dict payload
            
        Returns:
            dict: Extraction result
            
        Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
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
            document_id = payload.get("document_id")
            canonical_output_location = payload.get("canonical_output_location")
            
            logger.info(f"Extracting trade from document: {document_id}")
            
            # Validate inputs
            if not document_id or not canonical_output_location:
                raise ValueError("Missing required fields: document_id or canonical_output_location")
            
            # Step 1: Read canonical adapter output from S3
            logger.info(f"Step 1: Reading canonical output from S3: {canonical_output_location}")
            
            # Parse S3 URI
            if canonical_output_location.startswith("s3://"):
                s3_uri_parts = canonical_output_location[5:].split("/", 1)
                bucket = s3_uri_parts[0]
                key = s3_uri_parts[1]
            else:
                raise ValueError(f"Invalid S3 URI: {canonical_output_location}")
            
            # Read from S3
            response = self.s3.get_object(Bucket=bucket, Key=key)
            canonical_output_json = response['Body'].read().decode('utf-8')
            canonical_output_data = json.loads(canonical_output_json)
            
            # Validate canonical output
            canonical_output = CanonicalAdapterOutput(**canonical_output_data)
            
            logger.info(f"Canonical output loaded: adapter_type={canonical_output.adapter_type}")
            
            # Step 2: Extract trade data using LLM
            logger.info("Step 2: Extracting trade fields using LLM")
            
            extraction_result = self.llm_extraction_tool.extract_trade_fields(
                extracted_text=canonical_output.extracted_text,
                source_type=canonical_output.source_type,
                document_id=document_id
            )
            
            if not extraction_result["success"]:
                raise Exception(f"Trade extraction failed: {extraction_result.get('error')}")
            
            canonical_trade = extraction_result["canonical_trade"]
            extraction_confidence = extraction_result["extraction_confidence"]
            
            logger.info(f"Trade extracted: {canonical_trade.Trade_ID} (confidence: {extraction_confidence})")
            
            # Step 3: Verify trade source classification
            logger.info("Step 3: Verifying trade source classification")
            
            # The LLM extraction already set TRADE_SOURCE based on canonical_output.source_type
            # But we can double-check with the classifier for validation
            classification_result = self.trade_source_classifier.classify_trade_source(
                extracted_text=canonical_output.extracted_text,
                document_path=canonical_output_location
            )
            
            if classification_result["success"]:
                classified_source = classification_result["source_type"]
                classification_confidence = classification_result["confidence"]
                
                # Warn if classification disagrees with canonical output
                if classified_source != canonical_output.source_type:
                    logger.warning(
                        f"Classification mismatch: canonical={canonical_output.source_type}, "
                        f"classified={classified_source} (confidence={classification_confidence})"
                    )
                    # Use canonical output source_type as authoritative
                else:
                    logger.info(
                        f"Classification confirmed: {classified_source} "
                        f"(confidence: {classification_confidence})"
                    )
            
            # Step 4: Determine target DynamoDB table
            if canonical_trade.TRADE_SOURCE == "BANK":
                table_name = self.bank_table_name
            elif canonical_trade.TRADE_SOURCE == "COUNTERPARTY":
                table_name = self.counterparty_table_name
            else:
                raise ValueError(f"Invalid TRADE_SOURCE: {canonical_trade.TRADE_SOURCE}")
            
            logger.info(f"Step 4: Storing trade in DynamoDB table: {table_name}")
            
            # Step 5: Store in DynamoDB
            dynamodb_item = canonical_trade.to_dynamodb_format()
            
            self.dynamodb.put_item(
                TableName=table_name,
                Item=dynamodb_item
            )
            
            logger.info(f"Trade stored successfully: {canonical_trade.Trade_ID}")
            
            # Step 6: Save structured JSON to S3 for audit trail
            json_output_key = f"extracted/{canonical_trade.TRADE_SOURCE}/{canonical_trade.Trade_ID}.json"
            self.s3.put_object(
                Bucket=self.s3_bucket,
                Key=json_output_key,
                Body=canonical_trade.model_dump_json(indent=2),
                ContentType='application/json',
                Metadata={
                    'trade_id': canonical_trade.Trade_ID,
                    'source_type': canonical_trade.TRADE_SOURCE,
                    'extraction_confidence': str(extraction_confidence),
                    'correlation_id': correlation_id
                }
            )
            
            logger.info(f"Trade JSON saved to S3: s3://{self.s3_bucket}/{json_output_key}")
            
            # Step 7: Publish TRADE_EXTRACTED event
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            trade_extracted_event = TradeExtractedEvent(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                source_agent=self.agent_id,
                correlation_id=correlation_id,
                payload={
                    "trade_id": canonical_trade.Trade_ID,
                    "source_type": canonical_trade.TRADE_SOURCE,
                    "table_name": table_name,
                    "processing_time_ms": processing_time_ms
                },
                metadata={
                    "extraction_confidence": extraction_confidence,
                    "fields_extracted": len([
                        k for k, v in canonical_trade.model_dump(exclude_none=True).items()
                        if v is not None
                    ]),
                    "document_id": document_id
                }
            )
            
            self.sqs.send_message(
                QueueUrl=self.matching_events_queue_url,
                MessageBody=trade_extracted_event.to_sqs_message()
            )
            
            logger.info(f"Published TRADE_EXTRACTED event to {self.matching_events_queue}")
            
            # Update agent metrics
            self.registry.update_agent_status(
                agent_id=self.agent_id,
                metrics={
                    "last_processing_time_ms": processing_time_ms,
                    "total_processed": 1.0,
                    "last_extraction_confidence": extraction_confidence
                },
                last_heartbeat=datetime.utcnow()
            )
            
            return {
                "success": True,
                "trade_id": canonical_trade.Trade_ID,
                "source_type": canonical_trade.TRADE_SOURCE,
                "table_name": table_name,
                "extraction_confidence": extraction_confidence,
                "processing_time_ms": processing_time_ms
            }
            
        except Exception as e:
            logger.error(f"Error extracting trade: {e}")
            
            # Publish exception event
            exception_event = ExceptionRaisedEvent(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                source_agent=self.agent_id,
                correlation_id=correlation_id,
                payload={
                    "exception_id": f"exc_{uuid.uuid4().hex[:12]}",
                    "exception_type": "EXTRACTION_FAILED",
                    "trade_id": payload.get("document_id", "unknown"),
                    "error_message": str(e),
                    "reason_codes": ["EXTRACTION_FAILED"]
                },
                metadata={
                    "canonical_output_location": payload.get("canonical_output_location", "unknown"),
                    "document_id": payload.get("document_id", "unknown")
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
                "document_id": payload.get("document_id", "unknown")
            }
    
    def poll_and_process(self, max_messages: int = 1, wait_time_seconds: int = 20) -> None:
        """
        Poll SQS queue and process messages.
        
        Args:
            max_messages: Maximum number of messages to retrieve
            wait_time_seconds: Long polling wait time
            
        Validates: Requirements 3.3
        """
        logger.info(f"Polling queue: {self.extraction_events_queue}")
        
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.extraction_events_queue_url,
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
                    
                    # Extract trade
                    result = self.extract_trade(event_message)
                    
                    if result['success']:
                        # Delete message from queue
                        self.sqs.delete_message(
                            QueueUrl=self.extraction_events_queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        logger.info(f"Message processed and deleted: {result['trade_id']}")
                    else:
                        logger.error(f"Message processing failed: {result.get('error')}")
                        # Message will be retried or sent to DLQ based on queue configuration
                        
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
        logger.info(f"Starting Trade Data Extraction Agent (continuous={continuous})")
        
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
    AgentCore Runtime entrypoint for Trade Data Extraction Agent.
    
    This function is called by AgentCore Runtime when the agent is invoked.
    
    Args:
        payload: Event payload from SQS or direct invocation
        context: AgentCore context (optional)
        
    Returns:
        dict: Extraction result
        
    Validates: Requirements 2.1, 2.2, 3.3
    """
    logger.info("Trade Data Extraction Agent invoked via AgentCore Runtime")
    
    # Initialize agent
    agent = TradeDataExtractionAgent()
    
    # Check if payload is an SQS event or direct invocation
    if 'event_type' in payload:
        # Direct invocation with StandardEventMessage
        event_message = StandardEventMessage(**payload)
        result = agent.extract_trade(event_message)
    else:
        # Assume it's a raw extraction payload
        # Create a StandardEventMessage
        event_message = StandardEventMessage(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=EventTaxonomy.PDF_PROCESSED,
            source_agent="pdf_adapter_agent",
            correlation_id=payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}"),
            payload=payload
        )
        result = agent.extract_trade(event_message)
    
    return result


if __name__ == "__main__":
    """
    Run Trade Data Extraction Agent locally for testing.
    """
    import sys
    
    # Initialize agent
    agent = TradeDataExtractionAgent()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "register":
        # Just register the agent
        result = agent.register()
        print(json.dumps(result, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test with a sample event
        test_event = StandardEventMessage(
            event_id="evt_test_002",
            event_type=EventTaxonomy.PDF_PROCESSED,
            source_agent="pdf_adapter_agent",
            correlation_id="corr_test_002",
            payload={
                "document_id": "test_doc_002",
                "canonical_output_location": "s3://trade-matching-bucket/extracted/COUNTERPARTY/test_doc_002.json",
                "page_count": 5,
                "processing_time_ms": 8500
            },
            metadata={
                "dpi": 300,
                "source_type": "COUNTERPARTY"
            }
        )
        
        result = agent.extract_trade(test_event)
        print(json.dumps(result, indent=2, default=str))
    else:
        # Run continuously
        agent.run(continuous=True)
