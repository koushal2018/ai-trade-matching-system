#!/usr/bin/env python3
"""
Test script to debug DynamoDB write issues.
"""

import boto3
from datetime import datetime, timezone, timedelta
import os

# Load environment
from dotenv import load_dotenv
load_dotenv()

table_name = os.getenv("STATUS_TABLE_NAME", "trade-matching-system-processing-status")
region = "us-east-1"

print(f"Testing DynamoDB write to table: {table_name}")
print(f"Region: {region}")

dynamodb = boto3.client('dynamodb', region_name=region)

# Test data
session_id = "test-session-123"
now = datetime.now(timezone.utc)
expires_at = int((now + timedelta(days=90)).timestamp())

# Try to write using processing_id as partition key (matches actual table)
item = {
    "processing_id": {"S": session_id},
    "sessionId": {"S": session_id},
    "correlationId": {"S": "test-corr-123"},
    "documentId": {"S": "test-doc"},
    "sourceType": {"S": "BANK"},
    "overallStatus": {"S": "initializing"},
    "createdAt": {"S": now.isoformat() + "Z"},
    "lastUpdated": {"S": now.isoformat() + "Z"},
    "expiresAt": {"N": str(expires_at)}
}

print(f"\nAttempting PutItem with partition key: processing_id")
print(f"Session ID: {session_id}")

try:
    response = dynamodb.put_item(
        TableName=table_name,
        Item=item
    )
    print("✅ SUCCESS! Item written to DynamoDB")
    print(f"Response: {response['ResponseMetadata']['HTTPStatusCode']}")
    
    # Try to read it back
    print(f"\nAttempting GetItem...")
    get_response = dynamodb.get_item(
        TableName=table_name,
        Key={"processing_id": {"S": session_id}}
    )
    
    if "Item" in get_response:
        print("✅ SUCCESS! Item retrieved from DynamoDB")
        print(f"Retrieved sessionId: {get_response['Item'].get('sessionId', {}).get('S')}")
    else:
        print("❌ Item not found")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Try to get more details
    if hasattr(e, 'response'):
        print(f"Error code: {e.response.get('Error', {}).get('Code')}")
        print(f"Error message: {e.response.get('Error', {}).get('Message')}")
