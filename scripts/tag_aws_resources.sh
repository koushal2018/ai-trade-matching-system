#!/bin/bash
# Tag all AWS resources for OTC Trade Matching System
# Tags: applicationName=OTC_Agent, awsApplication=arn:aws:resource-groups:us-east-1:401552979575:group/OTC_Agent/038wkdij7bnpfmi7bbkvpt87s1

set -e

REGION="us-east-1"
APP_NAME="OTC_Agent"
AWS_APP_ARN="arn:aws:resource-groups:us-east-1:401552979575:group/OTC_Agent/038wkdij7bnpfmi7bbkvpt87s1"

echo "=== Tagging AWS Resources for OTC Trade Matching System ==="
echo "Region: $REGION"
echo "Application Name: $APP_NAME"
echo ""

# Function to tag a resource with error handling
tag_resource() {
    local resource_type=$1
    local resource_name=$2
    local command=$3
    
    echo "Tagging $resource_type: $resource_name"
    if eval "$command" 2>/dev/null; then
        echo "  ✓ Tagged successfully"
    else
        echo "  ✗ Failed to tag (may already be tagged or doesn't exist)"
    fi
}

echo "=== 1. Tagging DynamoDB Tables ==="
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
    tag_resource "DynamoDB" "$table" \
        "aws dynamodb tag-resource \
            --resource-arn arn:aws:dynamodb:$REGION:401552979575:table/$table \
            --tags Key=applicationName,Value=$APP_NAME Key=awsApplication,Value=$AWS_APP_ARN \
            --region $REGION"
done

echo ""
echo "=== 2. Tagging S3 Buckets ==="
S3_BUCKETS=(
    "trade-matching-system-agentcore-production"
    "trade-matching-system-agentcore-logs-production"
)

for bucket in "${S3_BUCKETS[@]}"; do
    tag_resource "S3" "$bucket" \
        "aws s3api put-bucket-tagging \
            --bucket $bucket \
            --tagging 'TagSet=[{Key=applicationName,Value=$APP_NAME},{Key=awsApplication,Value=$AWS_APP_ARN}]'"
done

echo ""
echo "=== 3. Tagging IAM Roles ==="
IAM_ROLES=(
    "trade-matching-system-agentcore-runtime-production"
    "trade-matching-system-agentcore-gateway-production"
    "trade-matching-system-lambda-orchestrator-production"
    "trade-matching-system-lambda-pdf-adapter-production"
    "trade-matching-system-lambda-trade-extraction-production"
    "trade-matching-system-lambda-trade-matching-production"
    "trade-matching-system-lambda-exception-mgmt-production"
    "trade-matching-system-lambda-custom-ops-production"
    "trade-matching-system-cognito-admin-production"
    "trade-matching-system-cognito-operator-production"
    "trade-matching-system-cognito-auditor-production"
)

for role in "${IAM_ROLES[@]}"; do
    tag_resource "IAM Role" "$role" \
        "aws iam tag-role \
            --role-name $role \
            --tags Key=applicationName,Value=$APP_NAME Key=awsApplication,Value=$AWS_APP_ARN"
done

echo ""
echo "=== 4. Tagging Lambda Functions ==="
LAMBDA_FUNCTIONS=(
    "trade-matching-system-custom-operations-production"
)

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    tag_resource "Lambda" "$func" \
        "aws lambda tag-resource \
            --resource arn:aws:lambda:$REGION:401552979575:function:$func \
            --tags applicationName=$APP_NAME,awsApplication=$AWS_APP_ARN \
            --region $REGION"
done

echo ""
echo "=== 5. Tagging SQS Queues ==="
SQS_QUEUES=(
    "trade-matching-system-document-upload-events-production.fifo"
    "trade-matching-system-document-upload-dlq-production.fifo"
    "trade-matching-system-extraction-events-production"
    "trade-matching-system-extraction-dlq-production"
    "trade-matching-system-matching-events-production"
    "trade-matching-system-matching-dlq-production"
    "trade-matching-system-exception-events-production"
    "trade-matching-system-exception-dlq-production"
    "trade-matching-system-hitl-review-queue-production.fifo"
    "trade-matching-system-hitl-dlq-production.fifo"
    "trade-matching-system-compliance-queue-production.fifo"
    "trade-matching-system-ops-desk-queue-production.fifo"
    "trade-matching-system-senior-ops-queue-production.fifo"
    "trade-matching-system-engineering-queue-production"
    "trade-matching-system-orchestrator-monitoring-queue-production"
)

for queue in "${SQS_QUEUES[@]}"; do
    QUEUE_URL="https://sqs.$REGION.amazonaws.com/401552979575/$queue"
    tag_resource "SQS" "$queue" \
        "aws sqs tag-queue \
            --queue-url $QUEUE_URL \
            --tags applicationName=$APP_NAME,awsApplication=$AWS_APP_ARN \
            --region $REGION"
done

echo ""
echo "=== 6. Tagging SNS Topics ==="
SNS_TOPICS=(
    "trade-matching-system-agentcore-alerts-production"
    "trade-matching-system-agent-events-fanout-production"
    "trade-matching-system-billing-alerts-production"
)

for topic in "${SNS_TOPICS[@]}"; do
    tag_resource "SNS" "$topic" \
        "aws sns tag-resource \
            --resource-arn arn:aws:sns:$REGION:401552979575:$topic \
            --tags Key=applicationName,Value=$APP_NAME Key=awsApplication,Value=$AWS_APP_ARN \
            --region $REGION"
done

echo ""
echo "=== 7. Tagging CloudWatch Log Groups ==="
LOG_GROUPS=(
    "/aws/agentcore/trade-matching-system/orchestrator-production"
    "/aws/agentcore/trade-matching-system/pdf-adapter-production"
    "/aws/agentcore/trade-matching-system/trade-extraction-production"
    "/aws/agentcore/trade-matching-system/trade-matching-production"
    "/aws/agentcore/trade-matching-system/exception-management-production"
)

for log_group in "${LOG_GROUPS[@]}"; do
    tag_resource "CloudWatch Log Group" "$log_group" \
        "aws logs tag-log-group \
            --log-group-name '$log_group' \
            --tags applicationName=$APP_NAME,awsApplication=$AWS_APP_ARN \
            --region $REGION"
done

echo ""
echo "=== 8. Tagging CloudWatch Alarms ==="
CW_ALARMS=(
    "trade-matching-system-pdf-adapter-latency-production"
    "trade-matching-system-pdf-adapter-error-rate-production"
    "trade-matching-system-trade-matching-error-rate-production"
    "trade-matching-system-total-charges-production"
    "trade-matching-system-total-charges-warning-production"
    "trade-matching-system-daily-charges-production"
    "trade-matching-system-bedrock-charges-production"
    "trade-matching-system-s3-charges-production"
    "trade-matching-system-dynamodb-charges-production"
    "trade-matching-system-cloudwatch-charges-production"
)

for alarm in "${CW_ALARMS[@]}"; do
    tag_resource "CloudWatch Alarm" "$alarm" \
        "aws cloudwatch tag-resource \
            --resource-arn arn:aws:cloudwatch:$REGION:401552979575:alarm:$alarm \
            --tags Key=applicationName,Value=$APP_NAME Key=awsApplication,Value=$AWS_APP_ARN \
            --region $REGION"
done

echo ""
echo "=== Tagging Complete ==="
echo "Run scripts/verify_resource_tags.sh to verify all tags are applied correctly."
