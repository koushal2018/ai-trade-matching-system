#!/usr/bin/env python3
"""
Seed Development Data Script

Populates DynamoDB tables with sample data for local development and testing.
Creates realistic trade, exception, HITL review, and audit records.

Usage:
    python scripts/seed_dev_data.py --all
    python scripts/seed_dev_data.py --trades
    python scripts/seed_dev_data.py --exceptions
    python scripts/seed_dev_data.py --hitl
    python scripts/seed_dev_data.py --audit
"""

import argparse
import boto3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import random

# AWS Configuration
AWS_REGION = 'us-east-1'

# Table Names
BANK_TABLE = 'BankTradeData'
COUNTERPARTY_TABLE = 'CounterpartyTradeData'
EXCEPTIONS_TABLE = 'ExceptionsTable'
HITL_TABLE = 'HITLReviews'
AUDIT_TABLE = 'AuditTrail'
PROCESSING_STATUS_TABLE = 'trade-matching-system-processing-status'

# Sample Data Templates
TRADE_TEMPLATES = [
    {
        'trade_id': 'TRD-2025-{:04d}',
        'counterparty': 'Goldman Sachs',
        'trade_date': '2025-01-20',
        'settlement_date': '2025-01-22',
        'notional': Decimal('1250000.00'),
        'currency': 'USD',
        'product': 'Interest Rate Swap',
        'direction': 'PAY'
    },
    {
        'trade_id': 'TRD-2025-{:04d}',
        'counterparty': 'JP Morgan',
        'trade_date': '2025-01-21',
        'settlement_date': '2025-01-23',
        'notional': Decimal('2500000.00'),
        'currency': 'EUR',
        'product': 'FX Forward',
        'direction': 'BUY'
    },
    {
        'trade_id': 'TRD-2025-{:04d}',
        'counterparty': 'Morgan Stanley',
        'trade_date': '2025-01-22',
        'settlement_date': '2025-01-24',
        'notional': Decimal('5000000.00'),
        'currency': 'USD',
        'product': 'Credit Default Swap',
        'direction': 'SELL'
    },
    {
        'trade_id': 'TRD-2025-{:04d}',
        'counterparty': 'Citibank',
        'trade_date': '2025-01-23',
        'settlement_date': '2025-01-25',
        'notional': Decimal('750000.00'),
        'currency': 'GBP',
        'product': 'Bond',
        'direction': 'BUY'
    },
]


def create_dynamodb_client():
    """Create DynamoDB resource."""
    return boto3.resource('dynamodb', region_name=AWS_REGION)


def seed_trade_data(count=20):
    """Seed bank and counterparty trade data."""
    print(f"\n🔄 Seeding {count} trade records...")

    dynamodb = create_dynamodb_client()
    bank_table = dynamodb.Table(BANK_TABLE)
    cp_table = dynamodb.Table(COUNTERPARTY_TABLE)

    for i in range(1, count + 1):
        template = TRADE_TEMPLATES[i % len(TRADE_TEMPLATES)]
        trade_id = template['trade_id'].format(i)
        internal_ref = f"INT-{uuid.uuid4()}"

        # Create bank trade
        bank_trade = {
            'trade_id': trade_id,
            'internal_reference': internal_ref,
            'counterparty': template['counterparty'],
            'trade_date': template['trade_date'],
            'settlement_date': template['settlement_date'],
            'notional': template['notional'],
            'currency': template['currency'],
            'product': template['product'],
            'direction': template['direction'],
            'created_at': (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5))).isoformat() + 'Z',
            'extraction_timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
            'source': 'BANK',
            'status': 'EXTRACTED'
        }

        bank_table.put_item(Item=bank_trade)
        print(f"  ✅ Created bank trade: {trade_id}")

        # Create matching counterparty trade (80% of the time)
        if random.random() < 0.8:
            # Introduce small variations for testing
            notional_variance = Decimal(str(random.uniform(-1000, 1000))) if random.random() < 0.2 else Decimal('0')

            cp_trade = {
                'trade_id': trade_id,
                'internal_reference': internal_ref,
                'counterparty': template['counterparty'],
                'trade_date': template['trade_date'],
                'settlement_date': template['settlement_date'],
                'notional': template['notional'] + notional_variance,
                'currency': template['currency'],
                'product': template['product'],
                'direction': 'RECEIVE' if template['direction'] == 'PAY' else 'PAY',
                'created_at': (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5))).isoformat() + 'Z',
                'extraction_timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
                'source': 'COUNTERPARTY',
                'status': 'EXTRACTED'
            }

            cp_table.put_item(Item=cp_trade)
            print(f"  ✅ Created counterparty trade: {trade_id}")

    print(f"✅ Seeded {count} trade records")


def seed_exceptions(count=10):
    """Seed exception records."""
    print(f"\n🔄 Seeding {count} exception records...")

    dynamodb = create_dynamodb_client()
    exceptions_table = dynamodb.Table(EXCEPTIONS_TABLE)

    severities = ['CRITICAL', 'ERROR', 'WARNING', 'INFO']
    agent_names = ['PDF Adapter Agent', 'Trade Extraction Agent', 'Trade Matching Agent', 'Exception Management Agent']
    messages = [
        'Notional amount mismatch: Bank=${bank_val}, Counterparty=${cp_val}',
        'Settlement date mismatch: Bank={bank_date}, Counterparty={cp_date}',
        'Missing counterparty confirmation for trade {trade_id}',
        'Trade extraction failed: Unable to parse PDF document',
        'Field validation error: Currency code invalid',
        'Confidence score below threshold: {score}%',
        'Timeout waiting for counterparty response',
        'Trade ID not found in counterparty system'
    ]

    for i in range(count):
        exception_id = f"exc-{uuid.uuid4()}"
        session_id = f"session-{uuid.uuid4()}-TRD-2025-{random.randint(1, 20):04d}"

        exception = {
            'exception_id': exception_id,
            'session_id': session_id,
            'agent_id': random.choice(agent_names).lower().replace(' ', '_'),
            'agent_name': random.choice(agent_names),
            'severity': random.choice(severities),
            'message': random.choice(messages).format(
                bank_val=random.randint(100000, 5000000),
                cp_val=random.randint(100000, 5000000),
                bank_date='2025-01-22',
                cp_date='2025-01-23',
                trade_id=f'TRD-2025-{random.randint(1, 20):04d}',
                score=random.randint(60, 85)
            ),
            'timestamp': (datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 48))).isoformat() + 'Z',
            'created_at': (datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 48))).isoformat() + 'Z',
            'recoverable': random.choice([True, False]),
            'resolution_status': random.choice(['PENDING', 'RESOLVED', 'ESCALATED']),
            'error_code': f'ERR-{random.randint(1000, 9999)}'
        }

        exceptions_table.put_item(Item=exception)
        print(f"  ✅ Created exception: {exception_id} ({exception['severity']})")

    print(f"✅ Seeded {count} exception records")


def seed_hitl_reviews(count=5):
    """Seed HITL review records."""
    print(f"\n🔄 Seeding {count} HITL review records...")

    dynamodb = create_dynamodb_client()
    hitl_table = dynamodb.Table(HITL_TABLE)

    for i in range(1, count + 1):
        review_id = f"rev-{uuid.uuid4()}"
        trade_id = f'TRD-2025-{random.randint(1, 20):04d}'

        review = {
            'review_id': review_id,
            'trade_id': trade_id,
            'session_id': f'session-{uuid.uuid4()}-{trade_id}',
            'match_score': Decimal(str(round(random.uniform(0.65, 0.85), 2))),
            'classification': 'REVIEW_REQUIRED',
            'decision_status': 'PENDING',
            'reason_codes': random.sample(['NOTIONAL_MISMATCH', 'DATE_MISMATCH', 'LOW_CONFIDENCE', 'FIELD_CONFLICT'], 2),
            'differences': {
                'notional': {'bank': Decimal('1250000.00'), 'counterparty': Decimal('1251000.00'), 'difference': Decimal('1000.00')},
                'settlement_date': {'bank': '2025-01-22', 'counterparty': '2025-01-23'}
            },
            'created_at': (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24))).isoformat() + 'Z',
            'status': 'PENDING',
            'assigned_to': None
        }

        hitl_table.put_item(Item=review)
        print(f"  ✅ Created HITL review: {review_id} (score: {review['match_score']})")

    print(f"✅ Seeded {count} HITL review records")


def seed_audit_trail(count=30):
    """Seed audit trail records."""
    print(f"\n🔄 Seeding {count} audit trail records...")

    dynamodb = create_dynamodb_client()
    audit_table = dynamodb.Table(AUDIT_TABLE)

    actions = ['UPLOAD', 'EXTRACT', 'MATCH', 'REVIEW', 'APPROVE', 'REJECT', 'ESCALATE']
    agent_ids = ['pdf_adapter', 'trade_extraction', 'trade_matching', 'exception_manager']
    users = ['admin@example.com', 'trader@example.com', 'ops@example.com']

    for i in range(count):
        audit_id = f"audit-{uuid.uuid4()}"

        audit_record = {
            'audit_id': audit_id,
            'timestamp': (datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 72))).isoformat() + 'Z',
            'action_type': random.choice(actions),
            'agent_id': random.choice(agent_ids),
            'user_email': random.choice(users),
            'session_id': f'session-{uuid.uuid4()}',
            'trade_id': f'TRD-2025-{random.randint(1, 20):04d}',
            'status': random.choice(['SUCCESS', 'FAILURE', 'WARNING']),
            'details': {
                'duration_ms': random.randint(500, 5000),
                'tokens_used': random.randint(1000, 10000)
            },
            'ip_address': f'10.0.{random.randint(1, 255)}.{random.randint(1, 255)}'
        }

        audit_table.put_item(Item=audit_record)
        print(f"  ✅ Created audit record: {audit_id} ({audit_record['action_type']})")

    print(f"✅ Seeded {count} audit trail records")


def seed_processing_status(count=10):
    """Seed processing status records."""
    print(f"\n🔄 Seeding {count} processing status records...")

    dynamodb = create_dynamodb_client()
    status_table = dynamodb.Table(PROCESSING_STATUS_TABLE)

    statuses = ['initializing', 'processing', 'completed', 'failed']
    agent_statuses = ['pending', 'loading', 'in-progress', 'success', 'error']

    for i in range(1, count + 1):
        trade_id = f'TRD-2025-{random.randint(1, 50):04d}'
        processing_id = f'session-{uuid.uuid4()}-{trade_id}'
        overall_status = random.choice(statuses)

        record = {
            'processing_id': processing_id,
            'overallStatus': overall_status,
            'created_at': (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))).isoformat() + 'Z',
            'lastUpdated': datetime.now(timezone.utc).isoformat() + 'Z',
            'pdfAdapter': {
                'status': random.choice(agent_statuses),
                'activity': 'Extracted text from PDF',
                'startedAt': (datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 2))).isoformat() + 'Z',
                'completedAt': datetime.now(timezone.utc).isoformat() + 'Z' if overall_status == 'completed' else None
            },
            'tradeExtraction': {
                'status': random.choice(agent_statuses),
                'activity': 'Parsed trade fields',
                'startedAt': (datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 2))).isoformat() + 'Z'
            },
            'tradeMatching': {
                'status': random.choice(agent_statuses),
                'activity': 'Comparing trade attributes'
            },
            'exceptionManagement': {
                'status': 'pending',
                'activity': 'No exceptions detected'
            }
        }

        status_table.put_item(Item=record)
        print(f"  ✅ Created processing status: {processing_id} ({overall_status})")

    print(f"✅ Seeded {count} processing status records")


def main():
    parser = argparse.ArgumentParser(description='Seed DynamoDB with sample development data')
    parser.add_argument('--all', action='store_true', help='Seed all tables')
    parser.add_argument('--trades', action='store_true', help='Seed trade data')
    parser.add_argument('--exceptions', action='store_true', help='Seed exceptions')
    parser.add_argument('--hitl', action='store_true', help='Seed HITL reviews')
    parser.add_argument('--audit', action='store_true', help='Seed audit trail')
    parser.add_argument('--status', action='store_true', help='Seed processing status')
    parser.add_argument('--count', type=int, default=None, help='Number of records to create')

    args = parser.parse_args()

    # If no specific flags, show help
    if not any([args.all, args.trades, args.exceptions, args.hitl, args.audit, args.status]):
        parser.print_help()
        return

    print("=" * 60)
    print("🌱 SEEDING DEVELOPMENT DATA")
    print("=" * 60)
    print(f"Region: {AWS_REGION}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    try:
        if args.all or args.trades:
            seed_trade_data(count=args.count or 20)

        if args.all or args.exceptions:
            seed_exceptions(count=args.count or 10)

        if args.all or args.hitl:
            seed_hitl_reviews(count=args.count or 5)

        if args.all or args.audit:
            seed_audit_trail(count=args.count or 30)

        if args.all or args.status:
            seed_processing_status(count=args.count or 10)

        print("\n" + "=" * 60)
        print("✅ SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
