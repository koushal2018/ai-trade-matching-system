#!/bin/bash
# Attach required policies to existing AgentCore Runtime role

set -e

ROLE_NAME="AmazonBedrockAgentCoreRuntimeDefaultServiceRole-dmdo4"
ACCOUNT_ID="401552979575"

echo "Attaching policies to role: ${ROLE_NAME}"

# S3 Policy
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

# DynamoDB Policy
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
        "dynamodb:Scan"
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

# Bedrock Policy
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

# Create and attach S3 policy
aws iam create-policy \
  --policy-name "${ROLE_NAME}-S3Access" \
  --policy-document "${S3_POLICY}" 2>/dev/null || echo "S3 policy exists"

aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${ROLE_NAME}-S3Access"

# Create and attach DynamoDB policy
aws iam create-policy \
  --policy-name "${ROLE_NAME}-DynamoDBAccess" \
  --policy-document "${DYNAMODB_POLICY}" 2>/dev/null || echo "DynamoDB policy exists"

aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${ROLE_NAME}-DynamoDBAccess"

# Create and attach Bedrock policy
aws iam create-policy \
  --policy-name "${ROLE_NAME}-BedrockAccess" \
  --policy-document "${BEDROCK_POLICY}" 2>/dev/null || echo "Bedrock policy exists"

aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${ROLE_NAME}-BedrockAccess"

echo "✅ Policies attached successfully"