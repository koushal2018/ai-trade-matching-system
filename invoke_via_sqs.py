#!/usr/bin/env python3
"""
Script to invoke the PDF Adapter Agent via SQS (event-driven).

This simulates how the agent would be triggered in production.
"""

import json
import sys
import time
import uuid
import boto3
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from latest_trade_matching_agent.models.events import StandardEventMessage, EventTaxonomy


def send_document_upload_event(pdf_path: str, source_type: str = "COUNTERPARTY"):
    """
    Send a DOCUMENT_UPLOADED event to SQS to trigger the agent.
    
    Args:
        pdf_path: Path to PDF file (local or S3)
        source_type: "BANK" or "COUNTERPARTY"
    """
    print("="*80)
    print("Sending Document Upload Event to SQS")
    print("="*80)
    
    # Initialize AWS clients
    s3 = boto3.client('s3', region_name='us-east-1')
    sqs = boto3.client('sqs', region_name='us-east-1')
    
    s3_bucket = "trade-matching-system-agentcore-production"
    queue_name = "trade-matching-system-document-upload-events-production.fifo"
    
    # Get queue URL
    response = sqs.get_queue_url(QueueName=queue_name)
    queue_url = response['QueueUrl']
    
    print(f"✅ Queue URL: {queue_url}")
    
    # Generate document ID
    document_id = f"doc_{int(time.time())}"
    
    # If local file, upload to S3 first
    if not pdf_path.startswith("s3://"):
        print(f"\n📤 Uploading {pdf_path} to S3...")
        s3_key = f"{source_type}/{document_id}.pdf"
        
        with open(pdf_path, 'rb') as f:
            s3.put_object(
                Bucket=s3_bucket,
                Key=s3_key,
                Body=f
            )
        
        document_path = f"s3://{s3_bucket}/{s3_key}"
        print(f"✅ Uploaded to: {document_path}")
    else:
        document_path = pdf_path
    
    # Create event
    event = StandardEventMessage(
        event_id=f"evt_{uuid.uuid4().hex[:12]}",
        event_type=EventTaxonomy.DOCUMENT_UPLOADED,
        source_agent="manual_trigger",
        correlation_id=f"corr_{uuid.uuid4().hex[:12]}",
        payload={
            "document_id": document_id,
            "document_path": document_path,
            "source_type": source_type,
            "s3_bucket": s3_bucket,
            "s3_key": f"{source_type}/{document_id}.pdf"
        },
        metadata={
            "trigger_source": "manual"
        }
    )
    
    print(f"\n📨 Sending event to SQS...")
    print(f"   Document ID: {document_id}")
    print(f"   Source Type: {source_type}")
    print(f"   Event ID: {event.event_id}")
    print(f"   Correlation ID: {event.correlation_id}")
    
    # Send message to SQS (FIFO queue requires MessageGroupId and MessageDeduplicationId)
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=event.to_sqs_message(),
        MessageGroupId=source_type,  # Group by source type
        MessageDeduplicationId=event.event_id  # Prevent duplicates
    )
    
    print(f"\n✅ Event sent to SQS!")
    print(f"   Message ID: {response['MessageId']}")
    print(f"   Sequence Number: {response.get('SequenceNumber', 'N/A')}")
    
    print(f"\n⚠️  NOTE: The agent is NOT running yet!")
    print(f"   To process this event, you need to:")
    print(f"   1. Run the agent listener: python run_pdf_adapter_listener.py")
    print(f"   2. OR deploy the agent to AgentCore Runtime (Task 14.2)")
    
    return {
        "document_id": document_id,
        "event_id": event.event_id,
        "correlation_id": event.correlation_id,
        "queue_url": queue_url
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Send document upload event to SQS")
    parser.add_argument("pdf_path", help="Path to PDF file (local or s3://)")
    parser.add_argument(
        "--source-type",
        choices=["BANK", "COUNTERPARTY"],
        default="COUNTERPARTY",
        help="Trade source type"
    )
    
    args = parser.parse_args()
    
    result = send_document_upload_event(args.pdf_path, args.source_type)
    
    print(f"\n📋 Event Details:")
    print(json.dumps(result, indent=2))
