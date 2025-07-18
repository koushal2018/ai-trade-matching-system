#!/bin/bash

# Quick troubleshooting script for when DynamoDB connectivity suddenly stops working
# This will help identify what changed since it was working

echo "=== Quick Troubleshooting for DynamoDB Connectivity Issues ==="
echo "Timestamp: $(date)"
echo ""

# Test API endpoint directly
echo "1. Testing API endpoint..."

# You'll need to replace this with your actual API Gateway URL
API_URL="YOUR_API_GATEWAY_URL_HERE"
echo "Testing: POST $API_URL/documents"

# Test the API endpoint
curl -X POST "$API_URL/documents" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "fileName": "test.pdf",
    "source": "BANK",
    "tradeDateRange": "test"
  }' \
  -v \
  -w "\n\nResponse Time: %{time_total}s\nHTTP Code: %{http_code}\n" 2>&1

echo ""
echo "=== Common Issues When It Suddenly Stops Working ==="
echo ""

echo "2. Check recent Lambda deployments:"
echo "   - Did you recently redeploy your Lambda function?"
echo "   - Check if environment variables were reset during deployment"
echo ""

echo "3. Check CloudWatch Logs:"
echo "   - Look for new error messages in Lambda logs"
echo "   - Check if there are any timeout errors"
echo "   - Look for IAM permission denied errors"
echo ""

echo "4. Quick fixes to try:"
echo "   a) Redeploy Lambda function with correct environment variables"
echo "   b) Check if Lambda execution role still has DynamoDB permissions"
echo "   c) Verify API Gateway is pointing to correct Lambda function"
echo "   d) Check if Lambda function timeout is sufficient (increase to 30 seconds)"
echo ""

echo "5. Environment Variables Check:"
echo "   Your Lambda function should have these environment variables:"
echo "   - BUCKET_NAME=fab-otc-reconciliation-deployment"
echo "   - BANK_TABLE=BankTradeData"
echo "   - COUNTERPARTY_TABLE=CounterpartyTradeData"
echo "   - MATCHES_TABLE=TradeMatches"
echo ""

echo "6. Test with the diagnostic Lambda function:"
echo "   Deploy lambda_function_diagnostic.py to get detailed error information"
echo ""

echo "=== CloudWatch Logs Command ==="
echo "To check recent logs, run:"
echo "aws logs describe-log-groups --log-group-name-prefix '/aws/lambda/your-function-name'"
echo "aws logs describe-log-streams --log-group-name '/aws/lambda/your-function-name' --order-by LastEventTime --descending"
echo "aws logs get-log-events --log-group-name '/aws/lambda/your-function-name' --log-stream-name 'LATEST_STREAM_NAME'"

echo ""
echo "=== Most Likely Causes ==="
echo "Since it was working before and suddenly stopped:"
echo "1. Lambda function was redeployed without environment variables"
echo "2. IAM role was modified and lost DynamoDB permissions"
echo "3. Lambda function timeout is too short for DynamoDB operations"
echo "4. API Gateway configuration was changed"
echo "5. Lambda function code was updated with a bug"

echo ""
echo "=== Immediate Action Items ==="
echo "1. Deploy the diagnostic Lambda function to get specific error details"
echo "2. Check CloudWatch logs for the exact error message"
echo "3. Verify environment variables are still set in Lambda function"
echo "4. Check IAM role permissions for DynamoDB access"
