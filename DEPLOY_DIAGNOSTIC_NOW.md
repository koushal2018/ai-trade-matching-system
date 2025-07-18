# DEPLOY DIAGNOSTIC FUNCTION - IMMEDIATE STEPS

## You have a 502 "Internal server error" - Lambda is crashing

The curl output shows:
- **HTTP Status: 502** 
- **{"message": "Internal server error"}**
- **x-amzn-errortype: InternalServerErrorException**

This means your Lambda function is failing. Here's how to deploy the diagnostic function:

## Option 1: AWS CLI (Quick)
```bash
# If you know your function name, replace YOUR_FUNCTION_NAME:
aws lambda update-function-code \
    --function-name YOUR_FUNCTION_NAME \
    --zip-file fileb://diagnostic-function.zip

# Or deploy as a new function:
aws lambda create-function \
    --function-name trade-diagnostic \
    --runtime python3.9 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_LAMBDA_ROLE \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://diagnostic-function.zip
```

## Option 2: AWS Console (Recommended)

### Step 1: Go to AWS Lambda Console
1. Open https://console.aws.amazon.com/lambda/
2. Find your existing Lambda function (likely named something with "trade", "reconciliation", or "document")

### Step 2: Backup & Replace Code
1. **IMPORTANT**: Copy your current Lambda code to a text file first!
2. Go to the **Code** tab in your Lambda function
3. Delete all existing code
4. Copy and paste the entire contents of `lambda_function_diagnostic.py` into the Lambda editor
5. Click **Deploy**

### Step 3: Test the Diagnostic
Run this command again:
```bash
curl -X POST "https://mdj9ch24qg.execute-api.us-east-1.amazonaws.com/dev/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "fileName": "test.pdf",
    "source": "BANK", 
    "tradeDateRange": "test"
  }' | jq .
```

## Expected Diagnostic Output
Instead of `{"message": "Internal server error"}`, you should get:
```json
{
  "message": "Diagnostic completed",
  "diagnostics": {
    "s3_status": "OK" or "FAILED",
    "dynamodb_status": "OK" or "FAILED", 
    "environment_variables": {...},
    "errors": [...],
    "recommendations": [...]
  }
}
```

## What to Look For:
- **"dynamodb_status": "FAILED"** → IAM permissions issue
- **"s3_status": "FAILED"** → S3 bucket permissions issue  
- **Missing environment variables** → Need to set BUCKET_NAME, BANK_TABLE, etc.
- **Specific error messages** → Will tell you exactly what to fix

## Quick Fix Commands (Based on Common Issues):

### If DynamoDB permissions missing:
```bash
aws iam attach-role-policy \
    --role-name YOUR_LAMBDA_ROLE \
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

### If environment variables missing:
```bash
aws lambda update-function-configuration \
    --function-name YOUR_FUNCTION_NAME \
    --environment Variables='{
        "BUCKET_NAME":"fab-otc-reconciliation-deployment",
        "BANK_TABLE":"BankTradeData", 
        "COUNTERPARTY_TABLE":"CounterpartyTradeData",
        "MATCHES_TABLE":"TradeMatches"
    }'
```

## After Diagnosis:
1. **Fix the identified issue**
2. **Restore your original Lambda code**
3. **Test that it works**

---

**ACTION NEEDED**: Deploy the diagnostic function now to see exactly why your Lambda is failing!
