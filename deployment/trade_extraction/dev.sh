#!/bin/bash
# Local development script for Trade Extraction Agent
# This script starts the AgentCore development server with hot reloading

set -e

echo "🚀 Starting Trade Extraction Agent Development Server"
echo "================================================"

# Configuration
AGENT_NAME="trade_extraction_agent"
DEV_PORT="${DEV_PORT:-8080}"
AWS_REGION="${AWS_REGION:-us-east-1}"
S3_BUCKET="${S3_BUCKET_NAME:-trade-matching-system-agentcore-production}"

echo "Configuration:"
echo "  Agent Name: ${AGENT_NAME}"
echo "  Port: ${DEV_PORT}"
echo "  Region: ${AWS_REGION}"
echo "  S3 Bucket: ${S3_BUCKET}"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS credentials not configured"
    exit 1
fi

# Check if agent is configured
if ! agentcore status --agent "${AGENT_NAME}" &> /dev/null; then
    echo "❌ Error: Agent not configured"
    echo "Run: agentcore configure --agent ${AGENT_NAME}"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Start development server
echo "Starting development server on port ${DEV_PORT}..."
echo "Press Ctrl+C to stop"
echo ""

agentcore dev \
    --port "${DEV_PORT}" \
    --env "AWS_REGION=${AWS_REGION}" \
    --env "S3_BUCKET_NAME=${S3_BUCKET}" \
    --env "DYNAMODB_BANK_TABLE=BankTradeData" \
    --env "DYNAMODB_COUNTERPARTY_TABLE=CounterpartyTradeData" \
    --env "AGENT_REGISTRY_TABLE=AgentRegistry" \
    --env "DEPLOYMENT_STAGE=development" \
    --env "AGENT_VERSION=dev" \
    --env "BYPASS_TOOL_CONSENT=true"
