#!/usr/bin/env python3
"""
Script to invoke the PDF Adapter Agent locally.

This demonstrates how to process a PDF document using the agent.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from latest_trade_matching_agent.agents.pdf_adapter_agent import PDFAdapterAgent
from latest_trade_matching_agent.models.events import StandardEventMessage, EventTaxonomy


def invoke_agent(pdf_path: str, source_type: str = "COUNTERPARTY"):
    """
    Invoke the PDF Adapter Agent to process a PDF.
    
    Args:
        pdf_path: Path to PDF file (local or S3)
        source_type: "BANK" or "COUNTERPARTY"
    """
    print("="*80)
    print("Invoking PDF Adapter Agent")
    print("="*80)
    
    # Initialize agent
    agent = PDFAdapterAgent(
        agent_id="pdf_adapter_local",
        region_name="us-east-1"
    )
    
    print(f"✅ Agent initialized: {agent.agent_id}")
    print(f"   S3 Bucket: {agent.s3_bucket}")
    print(f"   Region: {agent.region_name}")
    
    # Create event payload
    import uuid
    import time
    
    document_id = f"doc_{int(time.time())}"
    
    # If local file, upload to S3 first
    if not pdf_path.startswith("s3://"):
        print(f"\n📤 Uploading {pdf_path} to S3...")
        s3_key = f"{source_type}/{document_id}.pdf"
        
        with open(pdf_path, 'rb') as f:
            agent.s3.put_object(
                Bucket=agent.s3_bucket,
                Key=s3_key,
                Body=f
            )
        
        document_path = f"s3://{agent.s3_bucket}/{s3_key}"
        print(f"✅ Uploaded to: {document_path}")
    else:
        document_path = pdf_path
    
    # Create event
    event = StandardEventMessage(
        event_id=f"evt_{uuid.uuid4().hex[:12]}",
        event_type=EventTaxonomy.DOCUMENT_UPLOADED,
        source_agent="manual_invocation",
        correlation_id=f"corr_{uuid.uuid4().hex[:12]}",
        payload={
            "document_id": document_id,
            "document_path": document_path,
            "source_type": source_type,
            "s3_bucket": agent.s3_bucket,
            "s3_key": f"{source_type}/{document_id}.pdf"
        }
    )
    
    print(f"\n🚀 Processing document...")
    print(f"   Document ID: {document_id}")
    print(f"   Source Type: {source_type}")
    print(f"   Path: {document_path}")
    print(f"\n⏳ This will take 30-60 seconds...\n")
    
    # Process the document
    result = agent.process_document(event.payload)
    
    if result.get("success"):
        print("\n" + "="*80)
        print("✅ SUCCESS!")
        print("="*80)
        print(f"Document ID: {result['document_id']}")
        print(f"Processing Time: {result['processing_time_ms']:.0f}ms ({result['processing_time_ms']/1000:.1f}s)")
        print(f"Pages Processed: {result['page_count']}")
        print(f"Canonical Output: {result['canonical_output_location']}")
        print("\n📊 Next Steps:")
        print("   1. Check S3 for canonical output")
        print("   2. Check SQS extraction-events queue for PDF_PROCESSED event")
        print("   3. Trade Data Extraction Agent can now process this document")
        return result
    else:
        print("\n" + "="*80)
        print("❌ FAILED")
        print("="*80)
        print(f"Error: {result.get('error_message', 'Unknown error')}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Invoke PDF Adapter Agent")
    parser.add_argument("pdf_path", help="Path to PDF file (local or s3://)")
    parser.add_argument(
        "--source-type",
        choices=["BANK", "COUNTERPARTY"],
        default="COUNTERPARTY",
        help="Trade source type"
    )
    
    args = parser.parse_args()
    
    result = invoke_agent(args.pdf_path, args.source_type)
    
    sys.exit(0 if result else 1)
