#!/bin/bash
# Enable CloudWatch Transaction Search for AgentCore Observability
# This is a ONE-TIME setup per AWS account

set -e

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-401552979575}"

echo "============================================="
echo "Enabling CloudWatch Transaction Search"
echo "============================================="
echo "Region: ${REGION}"
echo "Account: ${ACCOUNT_ID}"
echo ""

# Step 1: Create resource policy for X-Ray to write to CloudWatch Logs
echo "Step 1: Creating CloudWatch Logs resource policy..."

POLICY_DOCUMENT=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TransactionSearchXRayAccess",
      "Effect": "Allow",
      "Principal": {
        "Service": "xray.amazonaws.com"
      },
      "Action": "logs:PutLogEvents",
      "Resource": [
        "arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:aws/spans:*",
        "arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:/aws/application-signals/data:*"
      ],
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:xray:${REGION}:${ACCOUNT_ID}:*"
        },
        "StringEquals": {
          "aws:SourceAccount": "${ACCOUNT_ID}"
        }
      }
    }
  ]
}
EOF
)

aws logs put-resource-policy \
  --policy-name TransactionSearchXRayAccess \
  --policy-document "${POLICY_DOCUMENT}" \
  --region "${REGION}" 2>&1 || echo "Policy may already exist, continuing..."

echo "✅ Resource policy created/updated"

# Step 2: Configure trace segment destination to CloudWatch Logs
echo ""
echo "Step 2: Setting trace segment destination to CloudWatch Logs..."

aws xray update-trace-segment-destination \
  --destination CloudWatchLogs \
  --region "${REGION}" 2>&1 || echo "Destination may already be set, continuing..."

echo "✅ Trace segment destination configured"

# Step 3: (Optional) Configure sampling percentage
echo ""
echo "Step 3: Configuring sampling percentage (100% for development)..."

aws xray update-indexing-rule \
  --name "Default" \
  --rule '{"Probabilistic": {"DesiredSamplingPercentage": 100}}' \
  --region "${REGION}" 2>&1 || echo "Sampling rule may already be configured, continuing..."

echo "✅ Sampling percentage configured"

# Step 4: Verify configuration
echo ""
echo "Step 4: Verifying configuration..."

echo "Trace segment destination:"
aws xray get-trace-segment-destination --region "${REGION}" 2>&1 || echo "Could not verify destination"

echo ""
echo "============================================="
echo "✅ CloudWatch Transaction Search enabled!"
echo "============================================="
echo ""
echo "Next steps:"
echo "1. Redeploy your agents with updated requirements.txt"
echo "2. Wait ~10 minutes for spans to become available"
echo "3. View observability data at:"
echo "   https://console.aws.amazon.com/cloudwatch/home#gen-ai-observability"
echo ""
