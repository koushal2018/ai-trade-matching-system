#!/bin/bash
set -e

echo "Deploying AgentCore Gateway resources..."

# DynamoDB Gateway
echo "Creating DynamoDB MCP Gateway..."
aws bedrock-agent create-gateway \
  --name "trade-matching-system-dynamodb-gateway-production" \
  --description "MCP Gateway for DynamoDB operations" \
  --target-type MCP_SERVER \
  --mcp-server-type dynamodb \
  --authentication-type IAM \
  --role-arn arn:aws:iam::401552979575:role/trade-matching-system-agentcore-gateway-production \
  --region us-east-1 \
  --tags Component=AgentCore,Environment=production,Purpose=DynamoDB

# S3 Gateway
echo "Creating S3 MCP Gateway..."
aws bedrock-agent create-gateway \
  --name "trade-matching-system-s3-gateway-production" \
  --description "MCP Gateway for S3 operations" \
  --target-type MCP_SERVER \
  --mcp-server-type s3 \
  --authentication-type IAM \
  --role-arn arn:aws:iam::401552979575:role/trade-matching-system-agentcore-gateway-production \
  --region us-east-1 \
  --tags Component=AgentCore,Environment=production,Purpose=S3

# Custom Operations Gateway (Lambda)
echo "Creating Custom Operations Gateway..."
aws bedrock-agent create-gateway \
  --name "trade-matching-system-custom-ops-gateway-production" \
  --description "MCP Gateway for custom Lambda operations" \
  --target-type LAMBDA \
  --lambda-function-arn arn:aws:lambda:us-east-1:401552979575:function:trade-matching-system-custom-operations-production \
  --authentication-type IAM \
  --role-arn arn:aws:iam::401552979575:role/trade-matching-system-agentcore-gateway-production \
  --region us-east-1 \
  --tags Component=AgentCore,Environment=production,Purpose=CustomOperations

echo "AgentCore Gateway resources deployed successfully!"
