#!/bin/bash

# Script to create DynamoDB tables for the trade reconciliation system
# Make sure you have AWS CLI configured with appropriate permissions

echo "Creating DynamoDB tables for trade reconciliation system..."

# Set AWS region (change this if needed)
AWS_REGION="us-east-1"

echo "Using AWS region: $AWS_REGION"

# Create BankTradeData table
echo "Creating BankTradeData table..."
aws dynamodb create-table \
    --region $AWS_REGION \
    --table-name BankTradeData \
    --attribute-definitions \
        AttributeName=trade_id,AttributeType=S \
    --key-schema \
        AttributeName=trade_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --tags Key=Project,Value=TradeReconciliation Key=Environment,Value=Development

if [ $? -eq 0 ]; then
    echo "✓ BankTradeData table created successfully"
else
    echo "✗ Failed to create BankTradeData table (may already exist)"
fi

# Create CounterpartyTradeData table
echo "Creating CounterpartyTradeData table..."
aws dynamodb create-table \
    --region $AWS_REGION \
    --table-name CounterpartyTradeData \
    --attribute-definitions \
        AttributeName=trade_id,AttributeType=S \
    --key-schema \
        AttributeName=trade_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --tags Key=Project,Value=TradeReconciliation Key=Environment,Value=Development

if [ $? -eq 0 ]; then
    echo "✓ CounterpartyTradeData table created successfully"
else
    echo "✗ Failed to create CounterpartyTradeData table (may already exist)"
fi

# Create TradeMatches table
echo "Creating TradeMatches table..."
aws dynamodb create-table \
    --region $AWS_REGION \
    --table-name TradeMatches \
    --attribute-definitions \
        AttributeName=match_id,AttributeType=S \
    --key-schema \
        AttributeName=match_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --tags Key=Project,Value=TradeReconciliation Key=Environment,Value=Development

if [ $? -eq 0 ]; then
    echo "✓ TradeMatches table created successfully"
else
    echo "✗ Failed to create TradeMatches table (may already exist)"
fi

echo ""
echo "Waiting for tables to be active..."

# Wait for tables to be active
aws dynamodb wait table-exists --region $AWS_REGION --table-name BankTradeData
aws dynamodb wait table-exists --region $AWS_REGION --table-name CounterpartyTradeData
aws dynamodb wait table-exists --region $AWS_REGION --table-name TradeMatches

echo ""
echo "Checking table status..."

# Check table status
aws dynamodb describe-table --region $AWS_REGION --table-name BankTradeData --query 'Table.TableStatus' --output text
aws dynamodb describe-table --region $AWS_REGION --table-name CounterpartyTradeData --query 'Table.TableStatus' --output text
aws dynamodb describe-table --region $AWS_REGION --table-name TradeMatches --query 'Table.TableStatus' --output text

echo ""
echo "DynamoDB table creation completed!"
echo ""
echo "Next steps:"
echo "1. Update your Lambda function's IAM role with DynamoDB permissions"
echo "2. Set environment variables in your Lambda function"
echo "3. Deploy the diagnostic Lambda function to test connectivity"
