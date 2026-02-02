#!/usr/bin/env python3
"""
Cleanup Test Data Script

Removes all test data from S3 and DynamoDB tables while preserving
the infrastructure (buckets, tables, folders).

Usage:
    python3 cleanup_test_data.py [--skip-s3] [--skip-dynamodb] [--keep-agents] [--yes]
"""

import boto3
import sys
import argparse
from decimal import Decimal
from datetime import datetime, timezone
from botocore.exceptions import ClientError

# AWS Configuration
AWS_REGION = 'us-east-1'
S3_BUCKET = 'trade-matching-system-agentcore-production'

# DynamoDB Tables
DYNAMODB_TABLES = {
    'BankTradeData': 'trade data (bank)',
    'CounterpartyTradeData': 'trade data (counterparty)',
    'TradeMatches': 'matching results',
    'ExceptionsTable': 'exceptions',
    'HITLReviews': 'HITL reviews',
    'AuditTrail': 'audit records',
    'trade-matching-system-processing-status': 'processing status'
}

# Initialize AWS clients
s3 = boto3.client('s3', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)


def confirm_action(message: str, auto_yes: bool = False) -> bool:
    """Ask user for confirmation."""
    if auto_yes:
        print(f"{message} [auto-confirmed]")
        return True

    response = input(f"{message} (yes/no): ").lower().strip()
    return response in ['yes', 'y']


def cleanup_s3_bucket(skip_s3: bool = False, auto_yes: bool = False):
    """Delete all objects from S3 bucket without deleting the bucket."""
    if skip_s3:
        print("\n📦 S3 Cleanup: SKIPPED (--skip-s3 flag)")
        return

    print(f"\n📦 S3 CLEANUP: {S3_BUCKET}")
    print("=" * 60)

    try:
        # List all objects in bucket
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET)

        object_count = 0
        objects_to_delete = []

        print("Scanning bucket for objects...")
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    objects_to_delete.append({'Key': obj['Key']})
                    object_count += 1

        if object_count == 0:
            print("✓ Bucket is already empty")
            return

        print(f"\nFound {object_count} objects:")
        # Show first 10 objects as preview
        for i, obj in enumerate(objects_to_delete[:10]):
            print(f"  - {obj['Key']}")
        if object_count > 10:
            print(f"  ... and {object_count - 10} more")

        if not confirm_action(f"\n⚠️  Delete all {object_count} objects?", auto_yes):
            print("Cancelled.")
            return

        # Delete objects in batches of 1000 (S3 limit)
        deleted_count = 0
        batch_size = 1000

        for i in range(0, len(objects_to_delete), batch_size):
            batch = objects_to_delete[i:i + batch_size]
            response = s3.delete_objects(
                Bucket=S3_BUCKET,
                Delete={'Objects': batch}
            )
            deleted_count += len(response.get('Deleted', []))
            print(f"  Deleted {deleted_count}/{object_count} objects...")

        print(f"✓ Successfully deleted {deleted_count} objects from {S3_BUCKET}")
        print(f"✓ Bucket {S3_BUCKET} preserved (empty)")

    except ClientError as e:
        print(f"✗ Error cleaning S3: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def get_table_key_schema(table_name: str):
    """Get the key schema for a DynamoDB table."""
    try:
        table = dynamodb.Table(table_name)
        table.load()

        key_schema = {}
        for key in table.key_schema:
            attr_name = key['AttributeName']
            key_type = key['KeyType']
            key_schema[key_type] = attr_name

        return key_schema
    except Exception as e:
        print(f"  ✗ Could not get key schema for {table_name}: {e}")
        return None


def cleanup_dynamodb_table(table_name: str, description: str, auto_yes: bool = False):
    """Delete all items from a DynamoDB table without deleting the table."""
    print(f"\n📊 Cleaning: {table_name}")
    print(f"   ({description})")

    try:
        table = dynamodb.Table(table_name)

        # Get key schema
        key_schema = get_table_key_schema(table_name)
        if not key_schema:
            print(f"  ✗ Skipping {table_name} - could not determine key schema")
            return

        # Scan to get all items
        response = table.scan()
        items = response.get('Items', [])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        if len(items) == 0:
            print("  ✓ Table is already empty")
            return

        print(f"  Found {len(items)} items")

        if not auto_yes:
            # Show sample of first few items
            print(f"  Sample items:")
            for i, item in enumerate(items[:3]):
                keys = {k: str(v)[:50] for k, v in item.items() if k in key_schema.values()}
                print(f"    {i+1}. {keys}")
            if len(items) > 3:
                print(f"    ... and {len(items) - 3} more")

        # Delete items in batches
        deleted_count = 0
        batch_size = 25  # DynamoDB batch write limit

        print(f"  Deleting {len(items)} items...")
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            with table.batch_writer() as writer:
                for item in batch:
                    # Extract only key attributes
                    key = {}
                    if 'HASH' in key_schema:
                        key[key_schema['HASH']] = item[key_schema['HASH']]
                    if 'RANGE' in key_schema:
                        key[key_schema['RANGE']] = item[key_schema['RANGE']]

                    writer.delete_item(Key=key)
                    deleted_count += 1

            if deleted_count % 100 == 0 or deleted_count == len(items):
                print(f"    Deleted {deleted_count}/{len(items)} items...")

        print(f"  ✓ Successfully deleted {deleted_count} items from {table_name}")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"  ⚠️  Table {table_name} not found - skipping")
        else:
            print(f"  ✗ Error cleaning {table_name}: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected error cleaning {table_name}: {e}")


def cleanup_dynamodb_tables(skip_dynamodb: bool = False, auto_yes: bool = False):
    """Delete all items from DynamoDB tables."""
    if skip_dynamodb:
        print("\n📊 DynamoDB Cleanup: SKIPPED (--skip-dynamodb flag)")
        return

    print(f"\n📊 DYNAMODB CLEANUP")
    print("=" * 60)

    if not auto_yes:
        print(f"\nWill clean {len(DYNAMODB_TABLES)} tables:")
        for table_name, desc in DYNAMODB_TABLES.items():
            print(f"  - {table_name} ({desc})")

        if not confirm_action("\n⚠️  Proceed with cleanup?", auto_yes):
            print("Cancelled.")
            return

    for table_name, description in DYNAMODB_TABLES.items():
        cleanup_dynamodb_table(table_name, description, auto_yes=auto_yes)


def reseed_agents(auto_yes: bool = False):
    """Optionally reseed agent registry with healthy agents."""
    print("\n🤖 AGENT REGISTRY")
    print("=" * 60)

    if not confirm_action("Reseed agent registry with healthy test agents?", auto_yes):
        print("Skipped agent reseeding.")
        return

    print("Reseeding agent registry...")

    table = dynamodb.Table('trade-matching-system-agent-registry-production')
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    agents = [
        {
            'agent_id': 'orchestrator_otc',
            'agent_type': 'ORCHESTRATOR',
            'agent_name': 'Orchestrator',
            'deployment_status': 'ACTIVE',
            'last_heartbeat': now,
            'avg_latency_ms': 1800,
            'error_rate': Decimal('0.005'),
            'throughput_per_hour': 82,
            'total_tokens': 5495,
            'input_tokens': 4396,
            'output_tokens': 1099,
            'avg_cycles': 4,
            'tool_calls': 6,
            'success_rate': Decimal('0.9967'),
            'active_tasks': 2
        },
        {
            'agent_id': 'trade_matching_agent',
            'agent_type': 'TRADE_MATCHER',
            'agent_name': 'Trade Matching Agent',
            'deployment_status': 'ACTIVE',
            'last_heartbeat': now,
            'avg_latency_ms': 8000,
            'error_rate': Decimal('0.005'),
            'throughput_per_hour': 39,
            'total_tokens': 16413,
            'input_tokens': 13131,
            'output_tokens': 3282,
            'avg_cycles': 3,
            'tool_calls': 5,
            'success_rate': Decimal('0.9869'),
            'active_tasks': 2
        },
        {
            'agent_id': 'trade_extraction_agent',
            'agent_type': 'TRADE_EXTRACTOR',
            'agent_name': 'Trade Extraction Agent',
            'deployment_status': 'ACTIVE',
            'last_heartbeat': now,
            'avg_latency_ms': 6000,
            'error_rate': Decimal('0.008'),
            'throughput_per_hour': 45,
            'total_tokens': 12847,
            'input_tokens': 10278,
            'output_tokens': 2569,
            'avg_cycles': 2,
            'tool_calls': 4,
            'success_rate': Decimal('0.992'),
            'active_tasks': 2
        },
        {
            'agent_id': 'pdf_adapter_agent',
            'agent_type': 'PDF_ADAPTER',
            'agent_name': 'PDF Adapter Agent',
            'deployment_status': 'ACTIVE',
            'last_heartbeat': now,
            'avg_latency_ms': 12000,
            'error_rate': Decimal('0.012'),
            'throughput_per_hour': 28,
            'total_tokens': 8934,
            'input_tokens': 7147,
            'output_tokens': 1787,
            'avg_cycles': 2,
            'tool_calls': 3,
            'success_rate': Decimal('0.9873'),
            'active_tasks': 2
        },
        {
            'agent_id': 'exception_manager',
            'agent_type': 'EXCEPTION_HANDLER',
            'agent_name': 'Exception Management Agent',
            'deployment_status': 'ACTIVE',
            'last_heartbeat': now,
            'avg_latency_ms': 2500,
            'error_rate': Decimal('0.03'),
            'throughput_per_hour': 156,
            'total_tokens': 3421,
            'input_tokens': 2737,
            'output_tokens': 684,
            'avg_cycles': 1,
            'tool_calls': 2,
            'success_rate': Decimal('0.9934'),
            'active_tasks': 2
        }
    ]

    for agent in agents:
        table.put_item(Item=agent)
        print(f"  ✓ Added {agent['agent_id']}")

    print(f"✓ Reseeded {len(agents)} healthy agents")


def main():
    parser = argparse.ArgumentParser(
        description='Cleanup test data from S3 and DynamoDB',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--skip-s3', action='store_true', help='Skip S3 cleanup')
    parser.add_argument('--skip-dynamodb', action='store_true', help='Skip DynamoDB cleanup')
    parser.add_argument('--yes', '-y', action='store_true', help='Auto-confirm all prompts')
    parser.add_argument('--reseed-agents', action='store_true', help='Reseed agent registry after cleanup')

    args = parser.parse_args()

    print("=" * 60)
    print("🧹 TEST DATA CLEANUP SCRIPT")
    print("=" * 60)
    print()
    print("This script will:")
    print("  ✓ Delete all objects from S3 bucket (but keep bucket)")
    print("  ✓ Delete all items from DynamoDB tables (but keep tables)")
    print("  ℹ️  Agent registry table will NOT be cleaned")
    print()
    print(f"S3 Bucket: {S3_BUCKET}")
    print(f"DynamoDB Tables: {len(DYNAMODB_TABLES)}")
    print()

    if not args.yes:
        if not confirm_action("⚠️  Continue with cleanup?"):
            print("\nCancelled. No changes made.")
            sys.exit(0)

    # Cleanup S3
    cleanup_s3_bucket(skip_s3=args.skip_s3, auto_yes=args.yes)

    # Cleanup DynamoDB
    cleanup_dynamodb_tables(skip_dynamodb=args.skip_dynamodb, auto_yes=args.yes)

    # Optionally reseed agents
    if args.reseed_agents:
        reseed_agents(auto_yes=args.yes)

    print("\n" + "=" * 60)
    print("✅ CLEANUP COMPLETE")
    print("=" * 60)
    print()
    print("Infrastructure preserved:")
    print(f"  ✓ S3 bucket: {S3_BUCKET} (empty)")
    print(f"  ✓ DynamoDB tables: {len(DYNAMODB_TABLES)} tables (empty)")
    print()
    print("You can now test the system from a clean state!")
    print()


if __name__ == '__main__':
    main()
