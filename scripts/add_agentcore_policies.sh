#!/bin/bash
# Add policies to existing AgentCore Runtime Default Service Role
# This script adds the required policies to the existing IAM role

set -e

# Configuration
ROLE_NAME="AmazonBedrockAgentCoreRuntimeDefaultServiceRole-dmdo4"
REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Adding policies to existing AgentCore Runtime role..."
echo "Role Name: ${ROLE_NAME}"
echo "Account ID: ${ACCOUNT_ID}"
echo "Region: ${REGION}"

# Check if role exists
if ! aws iam get-role --role-name "${ROLE_NAME}" >/dev/null 2>&1; then
    echo "❌ Role ${ROLE_NAME} does not exist. Please create it first."
    exit 1
fi

echo "✅ Role exists, adding policies..."

# Create and attach S3 access policy
S3_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::trade-matching-system-agentcore-production",
        "arn:aws:s3:::trade-matching-system-agentcore-production/*"
      ]
    }
  ]
}'

echo "Creating S3 access policy..."
aws iam create-policy \
  --policy-name "${ROLE_NAME}-S3Access" \
  --policy-document "${S3_POLICY}" \
  --description "S3 access policy for AgentCore Runtime" 2>/dev/null || echo "S3 policy already exists"

echo "Attaching S3 access policy..."
aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${ROLE_NAME}-S3Access" || echo "S3 policy already attached"

# Create and attach DynamoDB access policy
DYNAMODB_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchGetItem",
        "dynamodb:BatchWriteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/BankTradeData*",
        "arn:aws:dynamodb:*:*:table/CounterpartyTradeData*",
        "arn:aws:dynamodb:*:*:table/Exceptions*",
        "arn:aws:dynamodb:*:*:table/AgentRegistry*"
      ]
    }
  ]
}'

echo "Creating DynamoDB access policy..."
aws iam create-policy \
  --policy-name "${ROLE_NAME}-DynamoDBAccess" \
  --policy-document "${DYNAMODB_POLICY}" \
  --description "DynamoDB access policy for AgentCore Runtime" 2>/dev/null || echo "DynamoDB policy already exists"

echo "Attaching DynamoDB access policy..."
aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${ROLE_NAME}-DynamoDBAccess" || echo "DynamoDB policy already attached"

# Create and attach Bedrock access policy
BEDROCK_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
      ]
    }
  ]
}'

echo "Creating Bedrock access policy..."
aws iam create-policy \
  --policy-name "${ROLE_NAME}-BedrockAccess" \
  --policy-document "${BEDROCK_POLICY}" \
  --description "Bedrock access policy for AgentCore Runtime" 2>/dev/null || echo "Bedrock policy already exists"

echo "Attaching Bedrock access policy..."
aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${ROLE_NAME}-BedrockAccess" || echo "Bedrock policy already attached"

# Create and attach CloudWatch Logs policy
CLOUDWATCH_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/agentcore/*"
      ]
    }
  ]
}'

echo "Creating CloudWatch Logs policy..."
aws iam create-policy \
  --policy-name "${ROLE_NAME}-CloudWatchLogs" \
  --policy-document "${CLOUDWATCH_POLICY}" \
  --description "CloudWatch Logs policy for AgentCore Runtime" 2>/dev/null || echo "CloudWatch policy already exists"

echo "Attaching CloudWatch Logs policy..."
aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${ROLE_NAME}-CloudWatchLogs" || echo "CloudWatch policy already attached"

# Attach AWS managed policy for AgentCore Runtime if not already attached
echo "Attaching AWS managed policy..."
aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonBedrockAgentCoreRuntimeServiceRolePolicy" 2>/dev/null || echo "AWS managed policy already attached"

echo ""
echo "✅ All policies added to AgentCore Runtime role successfully!"
echo "Role ARN: arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo ""
echo "Attached policies:"
aws iam list-attached-role-policies --role-name "${ROLE_NAME}" --output table