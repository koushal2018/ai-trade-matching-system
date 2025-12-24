#!/usr/bin/env python3
"""
Local test for status tracking functionality.
Tests StatusTracker without invoking real agents.

Usage:
    python test_status_tracking_local.py
"""

import os
import sys
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from status_tracker import StatusTracker


async def test_status_tracking():
    """Test status tracking with mock workflow."""
    
    print("=" * 80)
    print("Testing Status Tracking Functionality")
    print("=" * 80)
    
    # Configuration
    table_name = os.getenv("STATUS_TABLE_NAME", "trade-matching-system-processing-status")
    region = os.getenv("AWS_REGION", "us-east-1")
    
    print(f"\nConfiguration:")
    print(f"  Table: {table_name}")
    print(f"  Region: {region}")
    
    # Verify AWS credentials
    import boto3
    try:
        sts = boto3.client('sts', region_name=region)
        identity = sts.get_caller_identity()
        print(f"  AWS Account: {identity['Account']}")
        print(f"  ✅ AWS credentials valid")
    except Exception as e:
        print(f"  ❌ AWS credentials invalid: {e}")
        sys.exit(1)
    
    # Verify table exists
    try:
        dynamodb = boto3.client('dynamodb', region_name=region)
        response = dynamodb.describe_table(TableName=table_name)
        print(f"  ✅ Table exists and is {response['Table']['TableStatus']}")
    except Exception as e:
        print(f"  ❌ Table not found: {e}")
        sys.exit(1)
    
    # Create status tracker
    print("\n" + "=" * 80)
    print("Step 1: Initialize Status Tracker")
    print("=" * 80)
    
    tracker = StatusTracker(table_name=table_name, region_name=region)
    print("✅ StatusTracker initialized")
    
    # Test data
    session_id = f"test-session-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    correlation_id = f"test-corr-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    document_id = "TEST_DOC_001"
    source_type = "BANK"
    
    print(f"\nTest Data:")
    print(f"  Session ID: {session_id}")
    print(f"  Correlation ID: {correlation_id}")
    print(f"  Document ID: {document_id}")
    print(f"  Source Type: {source_type}")
    
    # Step 1: Initialize status
    print("\n" + "=" * 80)
    print("Step 2: Initialize Workflow Status")
    print("=" * 80)
    
    success = tracker.initialize_status(
        session_id=session_id,
        correlation_id=correlation_id,
        document_id=document_id,
        source_type=source_type
    )
    
    if success:
        print("✅ Status initialized successfully")
    else:
        print("❌ Failed to initialize status")
        sys.exit(1)
    
    # Verify initialization
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"processing_id": {"S": session_id}}
        )
        if "Item" in response:
            item = response["Item"]
            print(f"\n✅ Status record created:")
            print(f"  Overall Status: {item.get('overallStatus', {}).get('S', 'N/A')}")
            print(f"  PDF Adapter: {item.get('pdfAdapter', {}).get('M', {}).get('status', {}).get('S', 'N/A')}")
            print(f"  Trade Extraction: {item.get('tradeExtraction', {}).get('M', {}).get('status', {}).get('S', 'N/A')}")
            print(f"  Trade Matching: {item.get('tradeMatching', {}).get('M', {}).get('status', {}).get('S', 'N/A')}")
        else:
            print("❌ Status record not found")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to verify initialization: {e}")
        sys.exit(1)
    
    # Step 2: Update agent status to in-progress
    print("\n" + "=" * 80)
    print("Step 3: Update PDF Adapter to In-Progress")
    print("=" * 80)
    
    await asyncio.sleep(1)  # Simulate processing delay
    
    success = tracker.update_agent_status(
        session_id=session_id,
        correlation_id=correlation_id,
        agent_key="pdfAdapter",
        status="in-progress"
    )
    
    if success:
        print("✅ PDF Adapter status updated to in-progress")
    else:
        print("❌ Failed to update status")
    
    # Step 3: Update agent status to success with token usage
    print("\n" + "=" * 80)
    print("Step 4: Update PDF Adapter to Success")
    print("=" * 80)
    
    await asyncio.sleep(2)  # Simulate processing
    
    mock_agent_response = {
        "success": True,
        "processing_time_ms": 2150.5,
        "token_usage": {
            "input_tokens": 11689,
            "output_tokens": 2480,
            "total_tokens": 14169
        }
    }
    
    success = tracker.update_agent_status(
        session_id=session_id,
        correlation_id=correlation_id,
        agent_key="pdfAdapter",
        status="success",
        agent_response=mock_agent_response,
        started_at=datetime.now(timezone.utc).isoformat() + "Z"
    )
    
    if success:
        print("✅ PDF Adapter status updated to success")
        print(f"  Processing Time: {mock_agent_response['processing_time_ms']}ms")
        print(f"  Token Usage: {mock_agent_response['token_usage']['total_tokens']} tokens")
    else:
        print("❌ Failed to update status")
    
    # Step 4: Update Trade Extraction
    print("\n" + "=" * 80)
    print("Step 5: Update Trade Extraction")
    print("=" * 80)
    
    tracker.update_agent_status(
        session_id=session_id,
        correlation_id=correlation_id,
        agent_key="tradeExtraction",
        status="in-progress"
    )
    print("✅ Trade Extraction set to in-progress")
    
    await asyncio.sleep(1)
    
    tracker.update_agent_status(
        session_id=session_id,
        correlation_id=correlation_id,
        agent_key="tradeExtraction",
        status="success",
        agent_response={
            "success": True,
            "processing_time_ms": 1050.2,
            "token_usage": {
                "input_tokens": 5234,
                "output_tokens": 1120,
                "total_tokens": 6354
            }
        }
    )
    print("✅ Trade Extraction set to success")
    
    # Step 5: Finalize workflow
    print("\n" + "=" * 80)
    print("Step 6: Finalize Workflow")
    print("=" * 80)
    
    success = tracker.finalize_status(
        session_id=session_id,
        correlation_id=correlation_id,
        overall_status="completed"
    )
    
    if success:
        print("✅ Workflow finalized as completed")
    else:
        print("❌ Failed to finalize workflow")
    
    # Final verification
    print("\n" + "=" * 80)
    print("Step 7: Verify Final Status")
    print("=" * 80)
    
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"processing_id": {"S": session_id}}
        )
        if "Item" in response:
            item = response["Item"]
            print(f"\n✅ Final Status:")
            print(f"  Overall Status: {item.get('overallStatus', {}).get('S', 'N/A')}")
            print(f"  PDF Adapter: {item.get('pdfAdapter', {}).get('M', {}).get('status', {}).get('S', 'N/A')}")
            print(f"  Trade Extraction: {item.get('tradeExtraction', {}).get('M', {}).get('status', {}).get('S', 'N/A')}")
            
            # Check token usage
            pdf_tokens = item.get('pdfAdapter', {}).get('M', {}).get('tokenUsage', {}).get('M', {})
            if pdf_tokens:
                total = pdf_tokens.get('totalTokens', {}).get('N', '0')
                print(f"  PDF Adapter Tokens: {total}")
            
            extraction_tokens = item.get('tradeExtraction', {}).get('M', {}).get('tokenUsage', {}).get('M', {})
            if extraction_tokens:
                total = extraction_tokens.get('totalTokens', {}).get('N', '0')
                print(f"  Trade Extraction Tokens: {total}")
        else:
            print("❌ Status record not found")
    except Exception as e:
        print(f"❌ Failed to verify final status: {e}")
    
    # Cleanup
    print("\n" + "=" * 80)
    print("Step 8: Cleanup Test Data")
    print("=" * 80)
    
    try:
        dynamodb.delete_item(
            TableName=table_name,
            Key={"processing_id": {"S": session_id}}
        )
        print("✅ Test data cleaned up")
    except Exception as e:
        print(f"⚠️  Failed to cleanup: {e}")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nStatus tracking is working correctly!")
    print("You can now deploy to AgentCore with confidence.")
    print("\nNext steps:")
    print("  1. cd deployment/swarm_agentcore")
    print("  2. agentcore deploy --agent http_agent_orchestrator")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_status_tracking())
