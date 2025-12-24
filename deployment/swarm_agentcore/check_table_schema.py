#!/usr/bin/env python3
"""
Quick script to check the actual DynamoDB table schema.
"""

import boto3
import json

table_name = "trade-matching-system-processing-status"
region = "us-east-1"

dynamodb = boto3.client('dynamodb', region_name=region)

try:
    response = dynamodb.describe_table(TableName=table_name)
    
    print(f"Table: {table_name}")
    print(f"Status: {response['Table']['TableStatus']}")
    print(f"\nKey Schema:")
    for key in response['Table']['KeySchema']:
        print(f"  - {key['AttributeName']} ({key['KeyType']})")
    
    print(f"\nAttribute Definitions:")
    for attr in response['Table']['AttributeDefinitions']:
        print(f"  - {attr['AttributeName']}: {attr['AttributeType']}")
    
    print(f"\nTTL Configuration:")
    ttl_response = dynamodb.describe_time_to_live(TableName=table_name)
    ttl_desc = ttl_response.get('TimeToLiveDescription', {})
    print(f"  Status: {ttl_desc.get('TimeToLiveStatus', 'UNKNOWN')}")
    print(f"  Attribute Name: {ttl_desc.get('AttributeName', 'NONE')}")
    
except Exception as e:
    print(f"Error: {e}")

