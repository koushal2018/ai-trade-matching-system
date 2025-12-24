#!/bin/bash
# Verify all AWS resources have required tags for OTC Trade Matching System
# Required tags: applicationName=OTC_Agent, awsApplication=arn:aws:resource-groups:us-east-1:401552979575:group/OTC_Agent/038wkdij7bnpfmi7bbkvpt87s1

set -e

REGION="us-east-1"
EXPECTED_APP_NAME="OTC_Agent"
EXPECTED_AWS_APP="arn:aws:resource-groups:us-east-1:401552979575:group/OTC_Agent/038wkdij7bnpfmi7bbkvpt87s1"
ACCOUNT_ID="401552979575"

MISSING_TAGS=()
VERIFIED=()

echo "=== Verifying AWS Resource Tags for OTC Trade Matching System ==="
echo "Region: $REGION"
echo "Expected applicationName: $EXPECTED_APP_NAME"
echo "Expected awsApplication: $EXPECTED_AWS_APP"
echo ""

# Function to check tags
check_tags() {
    local resource_type=$1
    local resource_name=$2
    local tags_json=$3
    
    local app_name=$(echo "$tags_json" | jq -r '.[] | select(.Key=="applicationName") | .Value' 2>/dev/null || echo "")
    local aws_app=$(echo "$tags_json" | jq -r '.[] | select(.Key=="awsApplication") | .Value' 2>/dev/null || echo "")
    
    if [[ "$app_name" == "$EXPECTED_APP_NAME" && "$aws_app" == "$EXPECTED_AWS_APP" ]]; then
        echo "  ✓ $resource_type: $resource_name - Tags verified"
        VERIFIED+=("$resource_type: $resource_name")
    else
        echo "  ✗ $resource_type: $resource_name - Missing or incorrect tags"
        echo "    applicationName: ${app_name:-MISSING}"
        echo "    awsApplication: ${aws_app:-MISSING}"
        MISSING_TAGS+=("$resource_type: $resource_name")
    fi
}

echo "=== 1. Checking DynamoDB Tables ==="
DYNAMODB_TABLES=(
    "BankTradeData"
    "BankTradeData-production"
    "CounterpartyTradeData"
    "CounterpartyTradeData-production"
    "trade-matching-system-processing-status"
    "trade-matching-system-exceptions-production"
    "trade-matching-system-agent-registry-production"
    "trade-matching-system-idempotency"
)

for table in "${DYNAMODB_TABLES[@]}"; do
    TAGS=$(aws dynamodb list-tags-of-resource \
        --resource-arn "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/$table" \
        --region $REGION \
        --query 'Tags' \
        --output json 2>/dev/null || echo "[]")
    check_tags "DynamoDB" "$table" "$TAGS"
done

echo ""
echo "=== 2. Checking S3 Buckets ==="
S3_BUCKETS=(
    "trade-matching-system-agentcore-production"
    "trade-matching-system-agentcore-logs-production"
    "trade-matching-system-agentcore-production-production"
)

for bucket in "${S3_BUCKETS[@]}"; do
    TAGS=$(aws s3api get-bucket-tagging \
        --bucket "$bucket" \
        --query 'TagSet' \
        --output json 2>/dev/null || echo "[]")
    check_tags "S3" "$bucket" "$TAGS"
done

echo ""
echo "=== 3. Checking IAM Roles ==="
IAM_ROLES=(
    "trade-matching-system-agentcore-runtime-production"
    "trade-matching-system-agentcore-gateway-production"
    "trade-matching-system-lambda-orchestrator-production"
    "trade-matching-system-lambda-pdf-adapter-production"
    "trade-matching-system-lambda-trade-extraction-production"
    "trade-matching-system-lambda-trade-matching-production"
    "trade-matching-system-lambda-exception-mgmt-production"
    "trade-matching-system-lambda-custom-ops-production"
)

for role in "${IAM_ROLES[@]}"; do
    TAGS=$(aws iam list-role-tags \
        --role-name "$role" \
        --query 'Tags' \
        --output json 2>/dev/null || echo "[]")
    check_tags "IAM Role" "$role" "$TAGS"
done

echo ""
echo "=== 4. Checking Lambda Functions ==="
LAMBDA_FUNCTIONS=(
    "trade-matching-system-custom-operations-production"
)

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    TAGS=$(aws lambda list-tags \
        --resource "arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$func" \
        --region $REGION \
        --output json 2>/dev/null | jq '[.Tags | to_entries[] | {Key: .key, Value: .value}]' || echo "[]")
    check_tags "Lambda" "$func" "$TAGS"
done

echo ""
echo "=== 5. Checking SQS Queues ==="
SQS_QUEUES=(
    "trade-matching-system-extraction-events-production"
    "trade-matching-system-matching-events-production"
    "trade-matching-system-exception-events-production"
)

for queue in "${SQS_QUEUES[@]}"; do
    QUEUE_URL="https://sqs.$REGION.amazonaws.com/$ACCOUNT_ID/$queue"
    TAGS=$(aws sqs list-queue-tags \
        --queue-url "$QUEUE_URL" \
        --region $REGION \
        --output json 2>/dev/null | jq '[.Tags | to_entries[] | {Key: .key, Value: .value}]' || echo "[]")
    check_tags "SQS" "$queue" "$TAGS"
done

echo ""
echo "=== 6. Checking SNS Topics ==="
SNS_TOPICS=(
    "trade-matching-system-agentcore-alerts-production"
    "trade-matching-system-billing-alerts-production"
)

for topic in "${SNS_TOPICS[@]}"; do
    TAGS=$(aws sns list-tags-for-resource \
        --resource-arn "arn:aws:sns:$REGION:$ACCOUNT_ID:$topic" \
        --region $REGION \
        --query 'Tags' \
        --output json 2>/dev/null || echo "[]")
    check_tags "SNS" "$topic" "$TAGS"
done

echo ""
echo "=== 7. Checking CloudWatch Log Groups ==="
LOG_GROUPS=(
    "/aws/agentcore/trade-matching-system/orchestrator-production"
    "/aws/agentcore/trade-matching-system/pdf-adapter-production"
)

for log_group in "${LOG_GROUPS[@]}"; do
    TAGS=$(aws logs list-tags-log-group \
        --log-group-name "$log_group" \
        --region $REGION \
        --output json 2>/dev/null | jq '[.tags | to_entries[] | {Key: .key, Value: .value}]' || echo "[]")
    check_tags "CloudWatch Log Group" "$log_group" "$TAGS"
done

echo ""
echo "=========================================="
echo "=== VERIFICATION SUMMARY ==="
echo "=========================================="
echo ""
echo "Verified Resources: ${#VERIFIED[@]}"
echo "Missing/Incorrect Tags: ${#MISSING_TAGS[@]}"
echo ""

if [ ${#MISSING_TAGS[@]} -gt 0 ]; then
    echo "Resources with missing or incorrect tags:"
    for resource in "${MISSING_TAGS[@]}"; do
        echo "  - $resource"
    done
    echo ""
    echo "Run scripts/tag_aws_resources.sh to apply missing tags."
    exit 1
else
    echo "All checked resources have correct tags!"
    exit 0
fi
