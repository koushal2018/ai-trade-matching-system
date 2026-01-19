#!/usr/bin/env python3
"""
Create DynamoDB tables for the AI Trade Matching System.
This script creates the required tables directly without Terraform.
"""

import boto3
from botocore.exceptions import ClientError
import time

REGION = "us-east-1"

# Table definitions (simplified versions without KMS for local testing)
TABLES = [
    {
        "TableName": "BankTradeData",
        "KeySchema": [{"AttributeName": "Trade_ID", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "Trade_ID", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "CounterpartyTradeData",
        "KeySchema": [{"AttributeName": "Trade_ID", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "Trade_ID", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "TradeMatches",
        "KeySchema": [{"AttributeName": "match_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "match_id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "ExceptionsTable",
        "KeySchema": [
            {"AttributeName": "exception_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "exception_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "AgentRegistry",
        "KeySchema": [{"AttributeName": "agent_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "agent_id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "HITLReviews",
        "KeySchema": [{"AttributeName": "review_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "review_id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "AuditTrail",
        "KeySchema": [
            {"AttributeName": "audit_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "audit_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "trade-matching-system-processing-status",
        "KeySchema": [{"AttributeName": "processing_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "processing_id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
]


def create_tables():
    """Create all required DynamoDB tables."""
    dynamodb = boto3.client("dynamodb", region_name=REGION)

    print("Creating DynamoDB tables for AI Trade Matching System...")
    print(f"Region: {REGION}")
    print()

    created = 0
    skipped = 0
    failed = 0

    for table_def in TABLES:
        table_name = table_def["TableName"]
        try:
            # Check if table exists
            dynamodb.describe_table(TableName=table_name)
            print(f"  [SKIP] {table_name} - already exists")
            skipped += 1
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                # Table doesn't exist, create it
                try:
                    dynamodb.create_table(**table_def)
                    print(f"  [CREATE] {table_name} - creating...")
                    created += 1
                except ClientError as create_error:
                    print(f"  [ERROR] {table_name} - {create_error}")
                    failed += 1
            else:
                print(f"  [ERROR] {table_name} - {e}")
                failed += 1

    print()
    print(f"Summary: {created} created, {skipped} already exist, {failed} failed")

    if created > 0:
        print()
        print("Waiting for tables to become active...")
        for table_def in TABLES:
            table_name = table_def["TableName"]
            try:
                waiter = dynamodb.get_waiter("table_exists")
                waiter.wait(
                    TableName=table_name,
                    WaiterConfig={"Delay": 2, "MaxAttempts": 30},
                )
                print(f"  {table_name}: ACTIVE")
            except Exception as e:
                print(f"  {table_name}: Error waiting - {e}")

    print()
    print("DynamoDB table creation complete!")


def list_tables():
    """List all DynamoDB tables."""
    dynamodb = boto3.client("dynamodb", region_name=REGION)
    response = dynamodb.list_tables()
    print("Existing DynamoDB tables:")
    for table_name in response.get("TableNames", []):
        print(f"  - {table_name}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Create DynamoDB tables for testing")
    parser.add_argument("--list", action="store_true", help="List existing tables")
    parser.add_argument("--delete", action="store_true", help="Delete tables (use with caution)")

    args = parser.parse_args()

    if args.list:
        list_tables()
    elif args.delete:
        print("Table deletion not implemented for safety. Delete manually if needed.")
    else:
        create_tables()


if __name__ == "__main__":
    main()
