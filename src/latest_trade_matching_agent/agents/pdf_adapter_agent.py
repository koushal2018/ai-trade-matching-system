"""
PDF Adapter Agent

This agent processes PDF trade confirmations and produces standardized
canonical output for downstream agents. It subscribes to document-upload-events
and publishes PDF_PROCESSED events.

Requirements: 3.2, 5.1, 5.2, 5.3, 5.4, 5.5
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
from ..models.events import (
    EventTaxonomy,
    StandardEventMessage,
    PDFProcessedEvent,
    ExceptionRaisedEvent
)
from ..models.registry import AgentRegistry, AgentRegistryEntry, ScalingConfig

# Import tools
# NOTE: These tools have been moved to legacy/crewai/tools/ as they depend on CrewAI
# from ..tools.pdf_to_image import PDFToImageTool
# from ..tools.ocr_tool import OCRTool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFAdapterAgent:
    """
    PDF Adapter Agent for processing trade confirmation PDFs.
    
    This agent:
    1. Subscribes to document-upload-events SQS queue
    2. Converts PDFs to 300 DPI images
    3. Performs OCR extraction using AWS Bedrock Claude Sonnet 4
    4. Produces canonical output conforming to CanonicalAdapterOutput schema
    5. Publishes PDF_PROCESSED events to extraction-events queue
    6. Handles errors and publishes to exception-events queue
    7. Registers itself in AgentRegistry
    
    Validates: Requirements 3.2, 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    def __init__(
        self,
        agent_id: str = "pdf_adapter_agent",
        region_name: str = "us-east-1",
        s3_bucket: Optional[str] = None,
        document_upload_queue: str = "trade-matching-system-document-upload-events-production.fifo",
        extraction_events_queue: str = "trade-matching-system-extraction-events-production",
        exception_events_queue: str = "trade-matching-system-exception-events-production"
    ):
        """
        Initialize PDF Adapter Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            region_name: AWS region
            s3_bucket: S3 bucket for storage
            document_upload_queue: SQS queue for document uploads
            extraction_events_queue: SQS queue for extraction events
            exception_events_queue: SQS queue for exception events
        """
        self.agent_id = agent_id
        self.region_name = region_name
        self.s3_bucket = s3_bucket or os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
        self.document_upload_queue = document_upload_queue
        self.extraction_events_queue = extraction_events_queue
        self.exception_events_queue = exception_events_queue
        
        # Initialize AWS clients
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.s3 = boto3.client('s3', region_name=region_name)
        
        # Initialize tools
        self.pdf_to_image_tool = PDFToImageTool()
        self.ocr_tool = OCRTool()
        
        # Initialize registry
        self.registry = AgentRegistry(region_name=region_name)
        
        # Get queue URLs
        self.document_upload_queue_url = self._get_queue_url(document_upload_queue)
        self.extraction_events_queue_url = self._get_queue_url(extraction_events_queue)
        self.exception_events_queue_url = self._get_queue_url(exception_events_queue)
        
        logger.info(f"PDF Adapter Agent initialized: {agent_id}")
    
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
            agent_name="PDF Adapter Agent",
            agent_type="ADAPTER",
            version="1.0.0",
            capabilities=[
                "pdf_processing",
                "image_conversion",
                "ocr_extraction",
                "canonical_output_generation"
            ],
            event_subscriptions=[self.document_upload_queue],
            event_publications=[self.extraction_events_queue, self.exception_events_queue],
            sla_targets={
                "processing_time_ms": 30000.0,  # 30 seconds per PDF
                "throughput_per_hour": 120.0,   # 120 PDFs per hour
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
    
    def process_document(self, event_message) -> Dict[str, Any]:
        """
        Process a document upload event.
        
        Args:
            event_message: StandardEventMessage from SQS or dict payload
            
        Returns:
            dict: Processing result
            
        Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5
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
            document_path = payload.get("document_path")
            source_type = payload.get("source_type")
            
            logger.info(f"Processing document: {document_id} from {source_type}")
            
            # Validate inputs
            if not document_id or not document_path or not source_type:
                raise ValueError("Missing required fields: document_id, document_path, or source_type")
            
            if source_type not in ["BANK", "COUNTERPARTY"]:
                raise ValueError(f"Invalid source_type: {source_type}. Must be BANK or COUNTERPARTY")
            
            # Step 1: Convert PDF to images (300 DPI)
            logger.info(f"Step 1: Converting PDF to 300 DPI images")
            unique_id = f"{document_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            pdf_result = self.pdf_to_image_tool._run(
                pdf_path=document_path,
                s3_output_bucket=self.s3_bucket,
                s3_output_prefix=f"PDFIMAGES/{source_type}",
                dpi=300,  # Required: 300 DPI per requirements 5.1, 18.1
                output_format="JPEG",
                save_locally=True,
                local_output_folder="/tmp/pdf_images",
                unique_identifier=unique_id
            )
            
            if "Error" in pdf_result or "❌" in pdf_result:
                raise Exception(f"PDF conversion failed: {pdf_result}")
            
            logger.info("PDF conversion successful")
            
            # Step 2: Get list of image paths
            local_image_dir = Path(f"/tmp/pdf_images/{unique_id}")
            image_paths = sorted(list(local_image_dir.glob("*.jpg")))
            
            if not image_paths:
                raise Exception("No images found after PDF conversion")
            
            logger.info(f"Found {len(image_paths)} images to process")
            
            # Step 3: Perform OCR extraction
            logger.info(f"Step 2: Performing OCR extraction on {len(image_paths)} pages")
            
            ocr_output_key = f"extracted/{source_type}/{document_id}_ocr.txt"
            ocr_result = self.ocr_tool._run(
                image_paths=[str(p) for p in image_paths],
                s3_output_bucket=self.s3_bucket,
                s3_output_key=ocr_output_key,
                save_locally=True,
                local_output_path=f"/tmp/ocr_output/{unique_id}_ocr.txt",
                model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
                region_name=self.region_name
            )
            
            if "Error" in ocr_result or "❌" in ocr_result:
                raise Exception(f"OCR extraction failed: {ocr_result}")
            
            logger.info("OCR extraction successful")
            
            # Step 4: Read extracted text
            ocr_text_path = Path(f"/tmp/ocr_output/{unique_id}_ocr.txt")
            with open(ocr_text_path, 'r', encoding='utf-8') as f:
                extracted_text = f.read()
            
            # Step 5: Create canonical output
            logger.info("Step 3: Creating canonical output")
            
            # Get metadata (handle both StandardEventMessage and dict)
            if isinstance(event_message, StandardEventMessage):
                file_size_bytes = event_message.metadata.get("file_size_bytes", 0)
            else:
                file_size_bytes = payload.get("file_size_bytes", 0)
            
            canonical_output = CanonicalAdapterOutput(
                adapter_type="PDF",
                document_id=document_id,
                source_type=source_type,
                extracted_text=extracted_text,
                metadata={
                    "page_count": len(image_paths),
                    "dpi": 300,
                    "processing_timestamp": datetime.utcnow().isoformat(),
                    "file_size_bytes": file_size_bytes,
                    "ocr_model": "us.anthropic.claude-sonnet-4-20250514-v1:0"
                },
                s3_location=f"s3://{self.s3_bucket}/extracted/{source_type}/{document_id}.json",
                processing_timestamp=datetime.utcnow(),
                correlation_id=correlation_id
            )
            
            # Step 6: Save canonical output to S3
            canonical_output_key = f"extracted/{source_type}/{document_id}.json"
            self.s3.put_object(
                Bucket=self.s3_bucket,
                Key=canonical_output_key,
                Body=canonical_output.model_dump_json(indent=2),
                ContentType='application/json',
                Metadata={
                    'document_id': document_id,
                    'source_type': source_type,
                    'adapter_type': 'PDF',
                    'correlation_id': correlation_id
                }
            )
            
            logger.info(f"Canonical output saved to S3: {canonical_output.s3_location}")
            
            # Step 7: Publish PDF_PROCESSED event
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            pdf_processed_event = PDFProcessedEvent(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                source_agent=self.agent_id,
                correlation_id=correlation_id,
                payload={
                    "document_id": document_id,
                    "canonical_output_location": canonical_output.s3_location,
                    "page_count": len(image_paths),
                    "processing_time_ms": processing_time_ms
                },
                metadata={
                    "dpi": 300,
                    "source_type": source_type,
                    "adapter_type": "PDF"
                }
            )
            
            self.sqs.send_message(
                QueueUrl=self.extraction_events_queue_url,
                MessageBody=pdf_processed_event.to_sqs_message()
            )
            
            logger.info(f"Published PDF_PROCESSED event to {self.extraction_events_queue}")
            
            # Update agent metrics
            self.registry.update_agent_status(
                agent_id=self.agent_id,
                metrics={
                    "last_processing_time_ms": processing_time_ms,
                    "total_processed": 1.0
                },
                last_heartbeat=datetime.utcnow()
            )
            
            return {
                "success": True,
                "document_id": document_id,
                "canonical_output_location": canonical_output.s3_location,
                "processing_time_ms": processing_time_ms,
                "page_count": len(image_paths)
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            
            # Publish exception event
            exception_event = ExceptionRaisedEvent(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                source_agent=self.agent_id,
                correlation_id=correlation_id,
                payload={
                    "exception_id": f"exc_{uuid.uuid4().hex[:12]}",
                    "exception_type": "PDF_PROCESSING_ERROR",
                    "trade_id": payload.get("document_id", "unknown"),
                    "error_message": str(e),
                    "reason_codes": ["PDF_PROCESSING_ERROR"]
                },
                metadata={
                    "document_path": payload.get("document_path", "unknown"),
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
                "document_id": payload.get("document_id", "unknown")
            }
    
    def poll_and_process(self, max_messages: int = 1, wait_time_seconds: int = 20) -> None:
        """
        Poll SQS queue and process messages.
        
        Args:
            max_messages: Maximum number of messages to retrieve
            wait_time_seconds: Long polling wait time
            
        Validates: Requirements 3.2
        """
        logger.info(f"Polling queue: {self.document_upload_queue}")
        
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.document_upload_queue_url,
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
                    
                    # Process document
                    result = self.process_document(event_message)
                    
                    if result['success']:
                        # Delete message from queue
                        self.sqs.delete_message(
                            QueueUrl=self.document_upload_queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        logger.info(f"Message processed and deleted: {result['document_id']}")
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
        logger.info(f"Starting PDF Adapter Agent (continuous={continuous})")
        
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
    AgentCore Runtime entrypoint for PDF Adapter Agent.
    
    This function is called by AgentCore Runtime when the agent is invoked.
    
    Args:
        payload: Event payload from SQS or direct invocation
        context: AgentCore context (optional)
        
    Returns:
        dict: Processing result
        
    Validates: Requirements 2.1, 2.2, 3.2
    """
    logger.info("PDF Adapter Agent invoked via AgentCore Runtime")
    
    # Initialize agent
    agent = PDFAdapterAgent()
    
    # Check if payload is an SQS event or direct invocation
    if 'event_type' in payload:
        # Direct invocation with StandardEventMessage
        event_message = StandardEventMessage(**payload)
        result = agent.process_document(event_message)
    else:
        # Assume it's a raw document upload payload
        # Create a StandardEventMessage
        event_message = StandardEventMessage(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=EventTaxonomy.DOCUMENT_UPLOADED,
            source_agent="upload_service",
            correlation_id=payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}"),
            payload=payload
        )
        result = agent.process_document(event_message)
    
    return result


if __name__ == "__main__":
    """
    Run PDF Adapter Agent locally for testing.
    """
    import sys
    
    # Initialize agent
    agent = PDFAdapterAgent()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "register":
        # Just register the agent
        result = agent.register()
        print(json.dumps(result, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test with a sample document
        test_event = StandardEventMessage(
            event_id="evt_test_001",
            event_type=EventTaxonomy.DOCUMENT_UPLOADED,
            source_agent="test_harness",
            correlation_id="corr_test_001",
            payload={
                "document_id": "test_doc_001",
                "document_path": "s3://trade-matching-bucket/COUNTERPARTY/test_trade.pdf",
                "source_type": "COUNTERPARTY"
            },
            metadata={
                "file_size_bytes": 245678
            }
        )
        
        result = agent.process_document(test_event)
        print(json.dumps(result, indent=2, default=str))
    else:
        # Run continuously
        agent.run(continuous=True)
