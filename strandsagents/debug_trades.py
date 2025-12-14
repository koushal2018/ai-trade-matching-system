#!/usr/bin/env python3
"""
Debug script to check what trades are actually in the DynamoDB tables
"""

import os
import boto3
from agents import get_dynamodb_resource, TABLE_CONFIG

# Set AWS region
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

def debug_table_contents():
    """Debug function to check table contents and status values"""
    try:
        dynamodb = get_dynamodb_resource()
        
        # Check bank trades table
        print(f"=== Checking Bank Trades Table: {TABLE_CONFIG.bank_trades_table} ===")
        bank_table = dynamodb.Table(TABLE_CONFIG.bank_trades_table)
        
        # Scan first 10 items to see what's there
        response = bank_table.scan(Limit=10)
        bank_trades = response.get('Items', [])
        print(f"Found {len(bank_trades)} bank trades (showing first 10)")
        
        # Show status distribution
        status_counts = {}
        for trade in bank_trades:
            status = trade.get('matched_status', 'NO_STATUS')
            status_counts[status] = status_counts.get(status, 0) + 1
            print(f"  Trade ID: {trade.get('trade_id', 'NO_ID')}, Status: {status}")
        
        print(f"Bank trades status distribution: {status_counts}")
        
        # Check counterparty trades table
        print(f"\n=== Checking Counterparty Trades Table: {TABLE_CONFIG.counterparty_trades_table} ===")
        cp_table = dynamodb.Table(TABLE_CONFIG.counterparty_trades_table)
        
        response = cp_table.scan(Limit=10)
        cp_trades = response.get('Items', [])
        print(f"Found {len(cp_trades)} counterparty trades (showing first 10)")
        
        # Show status distribution
        status_counts = {}
        for trade in cp_trades:
            status = trade.get('matched_status', 'NO_STATUS')
            status_counts[status] = status_counts.get(status, 0) + 1
            print(f"  Trade ID: {trade.get('trade_id', 'NO_ID')}, Status: {status}")
        
        print(f"Counterparty trades status distribution: {status_counts}")
        
        # Test the actual fetch_unmatched_trades function
        print(f"\n=== Testing fetch_unmatched_trades function ===")
        from agents import fetch_unmatched_trades
        
        try:
            bank_unmatched = fetch_unmatched_trades("BANK", 10)
            print(f"fetch_unmatched_trades('BANK') returned {len(bank_unmatched)} trades")
            for trade in bank_unmatched:
                print(f"  Bank Trade: {trade.get('trade_id')}, Status: {trade.get('matched_status')}")
        except Exception as e:
            print(f"Error fetching bank unmatched trades: {e}")
        
        try:
            cp_unmatched = fetch_unmatched_trades("COUNTERPARTY", 10)
            print(f"fetch_unmatched_trades('COUNTERPARTY') returned {len(cp_unmatched)} trades")
            for trade in cp_unmatched:
                print(f"  CP Trade: {trade.get('trade_id')}, Status: {trade.get('matched_status')}")
        except Exception as e:
            print(f"Error fetching counterparty unmatched trades: {e}")
            
    except Exception as e:
        print(f"Error debugging tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_table_contents()