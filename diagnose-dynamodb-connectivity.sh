#!/bin/bash

# Script to diagnose DynamoDB connectivity issues
# Run this to identify the root cause of Lambda function failures

echo "Diagnosing DynamoDB connectivity issues..."

# Set AWS region (change this if needed)
AWS_REGION="us-east-1"

echo "Using AWS region: $AWS_REGION"

# Check if tables exist and are accessible
echo ""
echo "=== Checking DynamoDB Tables ==="

TABLES=("BankTradeData" "CounterpartyTradeData" "TradeMatches")

for table in "${TABLES[@]}"; do
    echo "Checking table: $table"
    
    # Check if table exists and get status
    status=$(aws dynamodb describe-table --region $AWS_REGION --table-name $table --query 'Table.TableStatus' --output text 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "  ✓ Table $table exists and is $status"
        
        # Get table ARN for IAM policy reference
        arn=$(aws dynamodb describe-table --region $AWS_REGION --table-name $table --query 'Table.TableArn' --output text 2>/dev/null)
        echo "  ARN: $arn"
    else
        echo "  ✗ Cannot access table $table (check permissions or table name)"
    fi
    echo ""
done

echo "=== S3 Bucket Check ==="
BUCKET_NAME="fab-otc-reconciliation-deployment"

# Check if S3 bucket exists
aws s3 ls s3://$BUCKET_NAME/ > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ S3 bucket $BUCKET_NAME is accessible"
else
    echo "✗ Cannot access S3 bucket $BUCKET_NAME"
fi

echo ""
echo "=== IAM Policy Template ==="
echo "Your Lambda execution role needs this policy:"
echo ""

cat << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Scan",
                "dynamodb:Query",
                "dynamodb:BatchGetItem",
                "dynamodb:BatchWriteItem",
                "dynamodb:DescribeTable"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/BankTradeData",
                "arn:aws:dynamodb:*:*:table/CounterpartyTradeData",
                "arn:aws:dynamodb:*:*:table/TradeMatches"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::fab-otc-reconciliation-deployment/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::fab-otc-reconciliation-deployment"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
EOF

echo ""
echo "=== Environment Variables Needed ==="
echo "Set these environment variables in your Lambda function:"
echo "BUCKET_NAME=fab-otc-reconciliation-deployment"
echo "BANK_TABLE=BankTradeData"
echo "COUNTERPARTY_TABLE=CounterpartyTradeData"
echo "MATCHES_TABLE=TradeMatches"

echo ""
echo "=== Next Steps ==="
echo "1. Deploy the diagnostic Lambda function (lambda_function_diagnostic.py)"
echo "2. Test your API endpoint to get detailed error information"
echo "3. Check CloudWatch Logs for specific error messages"
echo "4. Update IAM permissions if needed"
echo "5. Set environment variables if missing"

echo ""
echo "Diagnostic completed!"
