#!/bin/bash

# Script to validate the Orchestrator Status Table deployment
# Checks table existence, configuration, and permissions

set -e

TABLE_NAME="ai-trade-matching-processing-status"
REGION="us-east-1"

echo "=========================================="
echo "Validating Orchestrator Status Table"
echo "=========================================="
echo ""

# Check if table exists
echo "1. Checking if table exists..."
if aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" > /dev/null 2>&1; then
    echo "✓ Table '$TABLE_NAME' exists"
else
    echo "✗ Table '$TABLE_NAME' does not exist"
    echo "Run ./scripts/deploy_status_table.sh to create it"
    exit 1
fi
echo ""

# Check table status
echo "2. Checking table status..."
TABLE_STATUS=$(aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" --query 'Table.TableStatus' --output text)
if [ "$TABLE_STATUS" == "ACTIVE" ]; then
    echo "✓ Table status: ACTIVE"
else
    echo "⚠ Table status: $TABLE_STATUS"
fi
echo ""

# Check billing mode
echo "3. Checking billing mode..."
BILLING_MODE=$(aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" --query 'Table.BillingModeSummary.BillingMode' --output text)
if [ "$BILLING_MODE" == "PAY_PER_REQUEST" ]; then
    echo "✓ Billing mode: PAY_PER_REQUEST (on-demand)"
else
    echo "⚠ Billing mode: $BILLING_MODE (expected PAY_PER_REQUEST)"
fi
echo ""

# Check partition key
echo "4. Checking partition key..."
PARTITION_KEY=$(aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" --query 'Table.KeySchema[?KeyType==`HASH`].AttributeName' --output text)
if [ "$PARTITION_KEY" == "sessionId" ]; then
    echo "✓ Partition key: sessionId"
else
    echo "✗ Partition key: $PARTITION_KEY (expected sessionId)"
fi
echo ""

# Check TTL
echo "5. Checking TTL configuration..."
TTL_STATUS=$(aws dynamodb describe-time-to-live --table-name "$TABLE_NAME" --region "$REGION" --query 'TimeToLiveDescription.TimeToLiveStatus' --output text)
TTL_ATTRIBUTE=$(aws dynamodb describe-time-to-live --table-name "$TABLE_NAME" --region "$REGION" --query 'TimeToLiveDescription.AttributeName' --output text)

if [ "$TTL_STATUS" == "ENABLED" ] && [ "$TTL_ATTRIBUTE" == "expiresAt" ]; then
    echo "✓ TTL enabled on 'expiresAt' attribute"
elif [ "$TTL_STATUS" == "ENABLING" ]; then
    echo "⚠ TTL is being enabled (status: ENABLING)"
    echo "  This may take a few minutes. Check again later."
else
    echo "✗ TTL status: $TTL_STATUS, attribute: $TTL_ATTRIBUTE"
fi
echo ""

# Check Point-in-Time Recovery
echo "6. Checking Point-in-Time Recovery..."
PITR_STATUS=$(aws dynamodb describe-continuous-backups --table-name "$TABLE_NAME" --region "$REGION" --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus' --output text)
if [ "$PITR_STATUS" == "ENABLED" ]; then
    echo "✓ Point-in-Time Recovery: ENABLED"
else
    echo "⚠ Point-in-Time Recovery: $PITR_STATUS"
fi
echo ""

# Check encryption
echo "7. Checking server-side encryption..."
SSE_STATUS=$(aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" --query 'Table.SSEDescription.Status' --output text)
if [ "$SSE_STATUS" == "ENABLED" ]; then
    echo "✓ Server-side encryption: ENABLED"
    SSE_TYPE=$(aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" --query 'Table.SSEDescription.SSEType' --output text)
    echo "  Encryption type: $SSE_TYPE"
else
    echo "⚠ Server-side encryption: $SSE_STATUS"
fi
echo ""

# Test write access
echo "8. Testing write access..."
TEST_SESSION_ID="validation-test-$(date +%s)"
TEST_EXPIRES_AT=$(($(date +%s) + 7776000))  # 90 days from now

aws dynamodb put-item \
  --table-name "$TABLE_NAME" \
  --item "{
    \"sessionId\": {\"S\": \"$TEST_SESSION_ID\"},
    \"correlationId\": {\"S\": \"test-validation\"},
    \"overallStatus\": {\"S\": \"initializing\"},
    \"createdAt\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"},
    \"expiresAt\": {\"N\": \"$TEST_EXPIRES_AT\"}
  }" \
  --region "$REGION" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Write access: SUCCESS"
else
    echo "✗ Write access: FAILED"
    echo "  Check IAM permissions for your AWS credentials"
fi
echo ""

# Test read access
echo "9. Testing read access..."
aws dynamodb get-item \
  --table-name "$TABLE_NAME" \
  --key "{\"sessionId\": {\"S\": \"$TEST_SESSION_ID\"}}" \
  --region "$REGION" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Read access: SUCCESS"
else
    echo "✗ Read access: FAILED"
fi
echo ""

# Clean up test item
echo "10. Cleaning up test data..."
aws dynamodb delete-item \
  --table-name "$TABLE_NAME" \
  --key "{\"sessionId\": {\"S\": \"$TEST_SESSION_ID\"}}" \
  --region "$REGION" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Test data cleaned up"
else
    echo "⚠ Failed to clean up test data"
fi
echo ""

# Summary
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo ""
echo "Table Configuration:"
echo "  Name: $TABLE_NAME"
echo "  Status: $TABLE_STATUS"
echo "  Billing: $BILLING_MODE"
echo "  Partition Key: $PARTITION_KEY"
echo "  TTL: $TTL_STATUS on $TTL_ATTRIBUTE"
echo "  PITR: $PITR_STATUS"
echo "  Encryption: $SSE_STATUS"
echo ""
echo "✓ Validation complete!"
echo ""
echo "Next steps:"
echo "1. Implement StatusWriter class (Task 2)"
echo "2. Integrate with orchestrator (Task 3)"
echo "3. Update agent response formats (Task 5)"
echo ""
