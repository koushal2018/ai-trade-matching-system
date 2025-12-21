#!/bin/bash
# Create AgentCore Runtime Default Service Role
# This script creates the IAM role required for AgentCore Runtime

set -e

# Configuration
ROLE_NAME="AmazonBedrockAgentCoreRuntimeDefaultServiceRole-dmdo4"
REGION="${AWS_REGION:-us-east-1}"

echo "Creating AgentCore Runtime Default Service Role..."
echo "Role Name: ${ROLE_NAME}"
echo "Region: ${REGION}"

# Trust policy for AgentCore Runtime
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

# Create the IAM role
echo "Creating IAM role..."
aws iam create-role \
  --role-name "${ROLE_NAME}" \
  --assume-role-policy-document "${TRUST_POLICY}" \
  --description "Default service role for Amazon Bedrock AgentCore Runtime" \
  --region "${REGION}"

# Attach AWS managed policy for AgentCore Runtime
echo "Attaching AWS managed policy..."
aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonBedrockAgentCoreRuntimeServiceRolePolicy" \
  --region "${REGION}"

# Create custom policy for S3 access
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
  --description "S3 access policy for AgentCore Runtime" \
  --region "${REGION}" || echo "Policy may already exist"

echo "Attaching S3 access policy..."
aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/${ROLE_NAME}-S3Access" \
  --region "${REGION}"

# Create custom policy for DynamoDB access
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
  --description "DynamoDB access policy for AgentCore Runtime" \
  --region "${REGION}" || echo "Policy may already exist"

echo "Attaching DynamoDB access policy..."
aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/${ROLE_NAME}-DynamoDBAccess" \
  --region "${REGION}"

# Create custom policy for Bedrock access
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
  --description "Bedrock access policy for AgentCore Runtime" \
  --region "${REGION}" || echo "Policy may already exist"

echo "Attaching Bedrock access policy..."
aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/${ROLE_NAME}-BedrockAccess" \
  --region "${REGION}"

echo "✅ AgentCore Runtime Default Service Role created successfully!"
echo "Role ARN: arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/${ROLE_NAME}"