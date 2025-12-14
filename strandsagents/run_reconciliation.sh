#!/bin/bash

# Set AWS region environment variables
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1

# Set other required environment variables
export BANK_TRADES_TABLE=BankTradeData
export COUNTERPARTY_TRADES_TABLE=CounterpartyTradeData
export TRADE_MATCHES_TABLE=TradeMatches
export BUCKET_NAME=fab-otc-reconciliation-deployment

echo "Starting Trade Reconciliation Agent with region: $AWS_REGION"
echo "Using tables: $BANK_TRADES_TABLE, $COUNTERPARTY_TRADES_TABLE, $TRADE_MATCHES_TABLE"

# Run the trade reconciliation agent
python trade_reconciliation_agent.py