#!/usr/bin/env python3
"""
SQS Listener for PDF Adapter Agent

This script continuously polls the document-upload-events queue
and processes documents as they arrive.

This simulates how the agent would run in AgentCore Runtime.
"""

import json
import sys
import time
import signal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from latest_trade_matching_agent.agents.pdf_adapter_agent import PDFAdapterAgent
from latest_trade_matching_agent.models.events import StandardEventMessage
import boto3
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
running = True


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    logger.info("\n🛑 Shutting down gracefully...")
    running = False


def run_listener():
    """Run the PDF Adapter Agent as an SQS listener."""
    global running
    
    logger.info("="*80)
    logger.info("PDF Adapter Agent - SQS Listener")
    logger.info("="*80)
    
    # Initialize agent
    agent = PDFAdapterAgent(
        agent_id="pdf_adapter_listener",
        region_name="us-east-1"
    )
    
    logger.info(f"✅ Agent initialized: {agent.agent_id}")
    logger.info(f"   S3 Bucket: {agent.s3_bucket}")
    logger.info(f"   Queue: {agent.document_upload_queue}")
    logger.info(f"   Region: {agent.region_name}")
    
    # Initialize SQS client
    sqs = boto3.client('sqs', region_name='us-east-1')
    
    # Get queue URL
    queue_url = agent.document_upload_queue_url
    
    logger.info(f"\n👂 Listening for messages on queue...")
    logger.info(f"   Queue URL: {queue_url}")
    logger.info(f"\n⏳ Waiting for documents... (Press Ctrl+C to stop)\n")
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    processed_count = 0
    error_count = 0
    
    while running:
        try:
            # Poll for messages (long polling with 20 second wait)
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,  # Long polling
                MessageAttributeNames=['All'],
                AttributeNames=['All']
            )
            
            if 'Messages' not in response:
                # No messages, continue polling
                continue
            
            for message in response['Messages']:
                try:
                    # Parse message
                    body = json.loads(message['Body'])
                    event = StandardEventMessage(**body)
                    
                    logger.info("="*80)
                    logger.info(f"📨 Received message: {event.event_id}")
                    logger.info(f"   Event Type: {event.event_type}")
                    logger.info(f"   Document ID: {event.payload.get('document_id')}")
                    logger.info(f"   Source Type: {event.payload.get('source_type')}")
                    logger.info("="*80)
                    
                    # Process the document
                    result = agent.process_document(event)
                    
                    if result.get("success"):
                        logger.info(f"\n✅ Document processed successfully!")
                        logger.info(f"   Processing Time: {result['processing_time_ms']:.0f}ms")
                        logger.info(f"   Pages: {result['page_count']}")
                        logger.info(f"   Output: {result['canonical_output_location']}")
                        
                        # Delete message from queue (successful processing)
                        sqs.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        
                        processed_count += 1
                        logger.info(f"\n📊 Stats: {processed_count} processed, {error_count} errors\n")
                    else:
                        logger.error(f"\n❌ Document processing failed!")
                        logger.error(f"   Error: {result.get('error_message')}")
                        
                        # Don't delete message - it will be retried or go to DLQ
                        error_count += 1
                        logger.info(f"\n📊 Stats: {processed_count} processed, {error_count} errors\n")
                
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    error_count += 1
                    # Don't delete message on error
        
        except Exception as e:
            if running:  # Only log if not shutting down
                logger.error(f"❌ Error polling queue: {e}")
                time.sleep(5)  # Wait before retrying
    
    logger.info("\n" + "="*80)
    logger.info("📊 Final Statistics")
    logger.info("="*80)
    logger.info(f"Documents Processed: {processed_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("\n✅ Listener stopped gracefully")


if __name__ == "__main__":
    run_listener()
