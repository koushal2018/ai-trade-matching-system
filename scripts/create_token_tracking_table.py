#!/usr/bin/env python3
"""
Create DynamoDB table for tracking token usage per trade/correlation_id.
"""

import boto3
from typing import Dict, Any

def create_token_tracking_table(region: str = "us-east-1") -> Dict[str, Any]:
    """Create DynamoDB table for token usage tracking."""
    
    dynamodb = boto3.client('dynamodb', region_name=region)
    
    table_name = "TokenUsageTracking"
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'correlation_id', 'KeyType': 'HASH'},
                {'AttributeName': 'agent_name', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'correlation_id', 'AttributeType': 'S'},
                {'AttributeName': 'agent_name', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'TimestampIndex',
                    'KeySchema': [
                        {'AttributeName': 'agent_name', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {'Key': 'Project', 'Value': 'AITradeMatching'},
                {'Key': 'Purpose', 'Value': 'TokenUsageTracking'}
            ]
        )
        
        print(f"✅ Created table: {table_name}")
        print(f"   Status: {response['TableDescription']['TableStatus']}")
        return response
        
    except dynamodb.exceptions.ResourceInUseException:
        print(f"⚠️  Table {table_name} already exists")
        return {"status": "exists"}


if __name__ == "__main__":
    create_token_tracking_table()
