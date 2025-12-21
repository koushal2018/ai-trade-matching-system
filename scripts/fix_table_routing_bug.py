#!/usr/bin/env python3
"""
Fix Table Routing Bug
Identifies and corrects trades that were stored in the wrong DynamoDB table.
"""

import boto3
import json
from typing import Dict, List, Any

def analyze_table_routing_issue():
    """Analyze the table routing issue and provide recommendations."""
    
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    
    print("🔍 Analyzing Table Routing Issue")
    print("=" * 50)
    
    # Check BankTradeData for misrouted trades
    print("\n📊 Scanning BankTradeData table...")
    bank_response = dynamodb.scan(TableName='BankTradeData')
    bank_trades = bank_response['Items']
    
    print(f"Found {len(bank_trades)} trades in BankTradeData")
    
    # Check CounterpartyTradeData
    print("\n📊 Scanning CounterpartyTradeData table...")
    cp_response = dynamodb.scan(TableName='CounterpartyTradeData')
    cp_trades = cp_response['Items']
    
    print(f"Found {len(cp_trades)} trades in CounterpartyTradeData")
    
    # Analyze each trade in BankTradeData
    misrouted_trades = []
    
    for trade in bank_trades:
        trade_id = trade.get('trade_id', {}).get('S', '')
        trade_source = trade.get('TRADE_SOURCE', {}).get('S', '')
        
        # Check if we can find the original extracted file
        try:
            # Try COUNTERPARTY folder first
            counterparty_key = f"extracted/COUNTERPARTY/{trade_id}.json"
            try:
                s3_response = s3.get_object(
                    Bucket='trade-matching-system-agentcore-production',
                    Key=counterparty_key
                )
                extracted_data = json.loads(s3_response['Body'].read().decode('utf-8'))
                original_source = extracted_data.get('source_type', '')
                
                if original_source == 'COUNTERPARTY' and trade_source == 'BANK':
                    misrouted_trades.append({
                        'trade_id': trade_id,
                        'current_table': 'BankTradeData',
                        'current_source': trade_source,
                        'correct_source': original_source,
                        'correct_table': 'CounterpartyTradeData',
                        'extracted_file': counterparty_key
                    })
                    print(f"❌ MISROUTED: {trade_id} (COUNTERPARTY → BankTradeData)")
                
            except s3.exceptions.NoSuchKey:
                # Try BANK folder
                bank_key = f"extracted/BANK/{trade_id}.json"
                try:
                    s3_response = s3.get_object(
                        Bucket='trade-matching-system-agentcore-production',
                        Key=bank_key
                    )
                    extracted_data = json.loads(s3_response['Body'].read().decode('utf-8'))
                    original_source = extracted_data.get('source_type', '')
                    
                    if original_source == 'BANK' and trade_source == 'BANK':
                        print(f"✅ CORRECT: {trade_id} (BANK → BankTradeData)")
                    
                except s3.exceptions.NoSuchKey:
                    print(f"⚠️  NO EXTRACTED FILE: {trade_id}")
                    
        except Exception as e:
            print(f"❌ ERROR checking {trade_id}: {e}")
    
    # Summary
    print(f"\n📋 ANALYSIS SUMMARY")
    print("=" * 30)
    print(f"Total Bank Trades: {len(bank_trades)}")
    print(f"Total Counterparty Trades: {len(cp_trades)}")
    print(f"Misrouted Trades: {len(misrouted_trades)}")
    
    if misrouted_trades:
        print(f"\n🔧 MISROUTED TRADES:")
        for trade in misrouted_trades:
            print(f"  • {trade['trade_id']}: {trade['correct_source']} → {trade['current_table']} (should be {trade['correct_table']})")
    
    return misrouted_trades

def fix_routing_issue(misrouted_trades: List[Dict[str, Any]], dry_run: bool = True):
    """Fix the routing issue by moving trades to correct tables."""
    
    if not misrouted_trades:
        print("✅ No misrouted trades to fix!")
        return
    
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    print(f"\n🔧 {'DRY RUN: ' if dry_run else ''}Fixing {len(misrouted_trades)} misrouted trades...")
    
    for trade in misrouted_trades:
        trade_id = trade['trade_id']
        
        try:
            # Get the full trade data from BankTradeData
            response = dynamodb.get_item(
                TableName='BankTradeData',
                Key={'trade_id': {'S': trade_id}}
            )
            
            if 'Item' not in response:
                print(f"❌ Trade {trade_id} not found in BankTradeData")
                continue
            
            trade_data = response['Item']
            
            # Update TRADE_SOURCE to correct value
            trade_data['TRADE_SOURCE'] = {'S': trade['correct_source']}
            
            if not dry_run:
                # Put in correct table
                dynamodb.put_item(
                    TableName=trade['correct_table'],
                    Item=trade_data
                )
                
                # Delete from wrong table
                dynamodb.delete_item(
                    TableName='BankTradeData',
                    Key={'trade_id': {'S': trade_id}}
                )
                
                print(f"✅ MOVED: {trade_id} → {trade['correct_table']}")
            else:
                print(f"🔍 WOULD MOVE: {trade_id} → {trade['correct_table']}")
                
        except Exception as e:
            print(f"❌ ERROR fixing {trade_id}: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix table routing bug')
    parser.add_argument('--fix', action='store_true', help='Actually fix the issue (default: dry run)')
    
    args = parser.parse_args()
    
    # Analyze the issue
    misrouted_trades = analyze_table_routing_issue()
    
    # Fix if requested
    if misrouted_trades:
        fix_routing_issue(misrouted_trades, dry_run=not args.fix)
        
        if not args.fix:
            print(f"\n💡 To actually fix the issue, run:")
            print(f"   python {__file__} --fix")
    else:
        print(f"\n✅ No routing issues found!")

if __name__ == "__main__":
    main()