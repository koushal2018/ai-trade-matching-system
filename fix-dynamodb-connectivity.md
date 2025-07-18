# Fix DynamoDB Connectivity Issues

## Root Cause Analysis
The 502 "Bad Gateway" errors from your API Gateway are caused by Lambda function failures, specifically DynamoDB connectivity issues.

## Common Issues and Solutions

### 1. Missing Environment Variables
Your Lambda function needs these environment variables:
```
BUCKET_NAME=fab-otc-reconciliation-deployment
BANK_TABLE=BankTradeData
COUNTERPARTY_TABLE=CounterpartyTradeData  
MATCHES_TABLE=TradeMatches
```

### 2. Missing IAM Permissions
Your Lambda execution role needs DynamoDB permissions:

```json
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
        }
    ]
}
```

### 3. Create Missing DynamoDB Tables
If the tables don't exist, you need to create them:

#### BankTradeData Table
```bash
aws dynamodb create-table \
    --table-name BankTradeData \
    --attribute-definitions \
        AttributeName=trade_id,AttributeType=S \
    --key-schema \
        AttributeName=trade_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

#### CounterpartyTradeData Table
```bash
aws dynamodb create-table \
    --table-name CounterpartyTradeData \
    --attribute-definitions \
        AttributeName=trade_id,AttributeType=S \
    --key-schema \
        AttributeName=trade_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

#### TradeMatches Table
```bash
aws dynamodb create-table \
    --table-name TradeMatches \
    --attribute-definitions \
        AttributeName=match_id,AttributeType=S \
    --key-schema \
        AttributeName=match_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

## Quick Fix Steps

1. **Deploy the diagnostic Lambda function** I created to identify the exact issue
2. **Check CloudWatch Logs** for the Lambda function to see specific error messages
3. **Verify IAM permissions** for the Lambda execution role
4. **Set environment variables** in the Lambda function configuration
5. **Create missing DynamoDB tables** if they don't exist

## Testing the Fix

Use the diagnostic Lambda function to test connectivity:
1. Deploy `lambda_function_diagnostic.py` 
2. Test the API endpoint: `POST https://your-api-gateway-url/dev/documents`
3. Check the response for detailed diagnostic information

The diagnostic function will tell you exactly which service (S3 or DynamoDB) is failing and why.
