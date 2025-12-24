#!/usr/bin/env python3
"""
Test script for status tracking functionality.
Tests the StatusTracker class without running the full orchestrator.

Usage:
    python test_status_tracking.py
"""

import sys
import os
from datetime import datetime, timezone
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from status_tracker import StatusTracker


def test_status_tracking():
    """Test status tracking operations."""
    
    print("=" * 80)
    print("Testing Status Tracking")
    print("=" * 80)
    
    # Initialize status tracker
    print("\n1. Initializing StatusTracker...")
    tracker = StatusTracker(
        table_name=os.getenv("STATUS_TABLE_NAME", "trade-matching-system-processing-status"),
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )
    print("✅ StatusTracker initialized")
    
    # Test data
    session_id = f"test-session-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    correlation_id = f"test-corr-{datetime.now(timezone.utc).strftime('%H%M%S')}"
    document_id = "TEST_DOC_12345"
    source_type = "BANK"
    
    print(f"\nTest Parameters:")
    print(f"  Session ID: {session_id}")
    print(f"  Correlation ID: {correlation_id}")
    print(f"  Document ID: {document_id}")
    print(f"  Source Type: {source_type}")
    
    # Test 1: Initialize status
    print("\n2. Testing initialize_status()...")
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
    
    # Test 2: Update agent status to in-progress
    print("\n3. Testing update_agent_status() - in-progress...")
    started_at = datetime.now(timezone.utc).isoformat() + "Z"
    success = tracker.update_agent_status(
        session_id=session_id,
        correlation_id=correlation_id,
        agent_key="pdfAdapter",
        status="in-progress"
    )
    
    if success:
        print("✅ PDF Adapter status updated to in-progress")
    else:
        print("❌ Failed to update PDF Adapter status")
    
    # Test 3: Update agent status to success with token usage
    print("\n4. Testing update_agent_status() - success with tokens...")
    mock_response = {
        "success": True,
        "token_usage": {
            "input_tokens": 1500,
            "output_tokens": 500,
            "total_tokens": 2000
        }
    }
    
    success = tracker.update_agent_status(
        session_id=session_id,
        correlation_id=correlation_id,
        agent_key="pdfAdapter",
        status="success",
        agent_response=mock_response,
        started_at=started_at
    )
    
    if success:
        print("✅ PDF Adapter status updated to success with token usage")
    else:
        print("❌ Failed to update PDF Adapter status to success")
    
    # Test 4: Update another agent to error
    print("\n5. Testing update_agent_status() - error...")
    error_response = {
        "success": False,
        "error": "Test error message",
        "token_usage": {
            "input_tokens": 100,
            "output_tokens": 0,
            "total_tokens": 100
        }
    }
    
    success = tracker.update_agent_status(
        session_id=session_id,
        correlation_id=correlation_id,
        agent_key="tradeExtraction",
        status="error",
        agent_response=error_response,
        started_at=datetime.now(timezone.utc).isoformat() + "Z"
    )
    
    if success:
        print("✅ Trade Extraction status updated to error")
    else:
        print("❌ Failed to update Trade Extraction status to error")
    
    # Test 5: Finalize status
    print("\n6. Testing finalize_status()...")
    success = tracker.finalize_status(
        session_id=session_id,
        correlation_id=correlation_id,
        overall_status="failed"  # Failed because trade extraction had error
    )
    
    if success:
        print("✅ Workflow status finalized")
    else:
        print("❌ Failed to finalize workflow status")
    
    # Test 6: Query the status from DynamoDB
    print("\n7. Querying status from DynamoDB...")
    try:
        import boto3
        dynamodb = boto3.client('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
        response = dynamodb.get_item(
            TableName=tracker.table_name,
            Key={"sessionId": {"S": session_id}}
        )
        
        if "Item" in response:
            print("✅ Status retrieved from DynamoDB")
            print("\nStatus Item:")
            print(json.dumps(response["Item"], indent=2, default=str))
        else:
            print("❌ Status not found in DynamoDB")
            
    except Exception as e:
        print(f"❌ Failed to query status: {e}")
    
    print("\n" + "=" * 80)
    print("Status Tracking Test Complete!")
    print("=" * 80)
    print(f"\nYou can query this status using session_id: {session_id}")
    print(f"Table: {tracker.table_name}")
    print("\nTo clean up, delete the test item from DynamoDB:")
    print(f"  aws dynamodb delete-item --table-name {tracker.table_name} --key '{{\"sessionId\": {{\"S\": \"{session_id}\"}}}}'")


if __name__ == "__main__":
    try:
        test_status_tracking()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
