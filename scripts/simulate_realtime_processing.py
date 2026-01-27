#!/usr/bin/env python3
"""
Simulate Real-Time Processing with WebSocket Broadcasts

This script simulates agent processing and updates the Real-Time Monitor
by updating DynamoDB processing status. The frontend polls for changes.

Usage:
    python3 simulate_realtime_processing.py <session_id>
"""

import sys
import time
import boto3
from datetime import datetime, timezone
from decimal import Decimal

AWS_REGION = 'us-east-1'

def simulate_processing(session_id: str):
    """Simulate processing workflow for a session."""
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table('trade-matching-system-processing-status')

    print(f"🚀 Simulating real-time processing for: {session_id}\n")
    print("Watch the Real-Time Monitor at http://localhost:3000/monitor")
    print("(Make sure 'Live' toggle is ON)\n")

    stages = [
        {
            'name': 'PDF Adapter',
            'key': 'pdfAdapter',
            'status': 'in-progress',
            'activity': 'Extracting text from uploaded PDF document',
            'overall': 'processing',
            'progress': 30,
            'duration': 2
        },
        {
            'name': 'PDF Adapter',
            'key': 'pdfAdapter',
            'status': 'completed',
            'activity': 'Successfully extracted 1 trade confirmation',
            'overall': 'processing',
            'progress': 100,
            'duration': 1
        },
        {
            'name': 'Trade Extraction',
            'key': 'tradeExtraction',
            'status': 'in-progress',
            'activity': 'Parsing trade fields: notional, currency, dates, counterparty',
            'overall': 'processing',
            'progress': 50,
            'duration': 2
        },
        {
            'name': 'Trade Extraction',
            'key': 'tradeExtraction',
            'status': 'completed',
            'activity': 'Extracted 1 trade record - Trade ID: TRD-2025-001',
            'overall': 'processing',
            'progress': 100,
            'duration': 1
        },
        {
            'name': 'Trade Matching',
            'key': 'tradeMatching',
            'status': 'in-progress',
            'activity': 'Comparing bank trade vs counterparty records',
            'overall': 'processing',
            'progress': 60,
            'duration': 2
        },
        {
            'name': 'Trade Matching',
            'key': 'tradeMatching',
            'status': 'in-progress',
            'activity': 'Calculating match score using weighted field comparison',
            'overall': 'processing',
            'progress': 85,
            'duration': 1
        },
        {
            'name': 'Trade Matching',
            'key': 'tradeMatching',
            'status': 'completed',
            'activity': 'Match found! Score: 0.98 - Classification: MATCHED',
            'overall': 'completed',
            'progress': 100,
            'duration': 1
        }
    ]

    for i, stage in enumerate(stages):
        now = datetime.now(timezone.utc).isoformat() + 'Z'

        print(f"[{i+1}/{len(stages)}] {stage['name']}: {stage['activity']}")

        # Build update expression
        update_parts = []
        attr_values = {':time': now, ':overall': stage['overall']}

        # Update specific agent
        update_parts.append(f"{stage['key']}.#status = :status")
        update_parts.append(f"{stage['key']}.activity = :activity")
        attr_values[':status'] = stage['status']
        attr_values[':activity'] = stage['activity']

        if stage['status'] == 'in-progress':
            update_parts.append(f"{stage['key']}.startedAt = :start")
            update_parts.append(f"{stage['key']}.progress = :progress")
            attr_values[':start'] = now
            attr_values[':progress'] = Decimal(str(stage['progress']))
        elif stage['status'] == 'completed':
            update_parts.append(f"{stage['key']}.completedAt = :complete")
            attr_values[':complete'] = now

        # Update overall status
        update_parts.append('overallStatus = :overall')
        update_parts.append('lastUpdated = :time')

        if stage['overall'] == 'completed':
            update_parts.append('completedAt = :time')

        update_expr = 'SET ' + ', '.join(update_parts)

        try:
            table.update_item(
                Key={'processing_id': session_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues=attr_values
            )
            print(f"   ✓ Updated (waiting {stage['duration']}s...)")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        time.sleep(stage['duration'])

    print(f"\n✅ Processing simulation complete!")
    print(f"   Session: {session_id}")
    print(f"   Status: completed")
    print(f"\nCheck Real-Time Monitor or Workflow Status page to see results.")


def main():
    if len(sys.argv) < 2:
        # Get most recent session
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        table = dynamodb.Table('trade-matching-system-processing-status')

        response = table.scan()
        items = response.get('Items', [])

        if not items:
            print("No processing sessions found.")
            print("Upload a file first, then run this script.")
            sys.exit(1)

        # Get most recent
        recent = sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)[0]
        session_id = recent['processing_id']
        print(f"Auto-detected session: {session_id}\n")
    else:
        session_id = sys.argv[1]

    simulate_processing(session_id)


if __name__ == '__main__':
    main()
