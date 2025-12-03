#!/bin/bash
# Deployment script for Trade Matching Agent to AgentCore Runtime
# Requirements: 2.1, 2.2, 3.4

set -e

echo "============================================="
echo "Deploying Trade Matching Agent to AgentCore"
echo "============================================="

# Configuration
AGENT_NAME="trade_matching_agent"
RUNTIME="PYTHON_3_11"
REGION="${AWS_REGION:-us-east-1}"
S3_BUCKET="${S3_BUCKET_NAME:-trade-matching-system-agentcore-production}"
ENTRYPOINT="trade_matching_agent.py"

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v agentcore &> /dev/null; then
    echo "❌ Error: agentcore CLI not found. Please install: pip install bedrock-agentcore-starter-toolkit"
    exit 1
fi

if [ ! -f "${ENTRYPOINT}" ]; then
    echo "❌ Error: Entry point file ${ENTRYPOINT} not found"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found"
    exit 1
fi

# Verify agent code structure
echo "Verifying agent code structure..."
if ! grep -q "from bedrock_agentcore import BedrockAgentCoreApp" "${ENTRYPOINT}"; then
    echo "❌ Error: Agent must import BedrockAgentCoreApp"
    exit 1
fi

if ! grep -q "@app.entrypoint" "${ENTRYPOINT}"; then
    echo "❌ Error: Agent must have @app.entrypoint decorator"
    exit 1
fi

if ! grep -q "app.run()" "${ENTRYPOINT}"; then
    echo "❌ Error: Agent must call app.run()"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Step 1: Configure the agent
echo ""
echo "Step 1: Configuring agent with PYTHON_3_11 runtime..."
agentcore configure \
  --entrypoint "${ENTRYPOINT}" \
  --name "${AGENT_NAME}" \
  --runtime "${RUNTIME}" \
  --requirements-file "requirements.txt" \
  --region "${REGION}" \
  --non-interactive

echo "✅ Agent configured"

# Step 2: Configure memory integration (if AGENTCORE_MEMORY_ARN is set)
if [ -n "${AGENTCORE_MEMORY_ARN}" ]; then
    echo ""
    echo "Step 2: Memory integration configured via environment"
    echo "Memory ARN: ${AGENTCORE_MEMORY_ARN}"
    echo "Memory Strategy: semantic"
else
    echo ""
    echo "Step 2: Skipping memory integration (AGENTCORE_MEMORY_ARN not set)"
    echo "To enable memory, set AGENTCORE_MEMORY_ARN environment variable"
fi

# Step 3: Launch the agent
echo ""
echo "Step 3: Launching agent to AgentCore Runtime..."
agentcore launch \
  --agent "${AGENT_NAME}" \
  --env "AWS_REGION=${REGION}" \
  --env "S3_BUCKET_NAME=${S3_BUCKET}" \
  --env "DYNAMODB_BANK_TABLE=BankTradeData" \
  --env "DYNAMODB_COUNTERPARTY_TABLE=CounterpartyTradeData" \
  --auto-update-on-conflict

echo "✅ Agent launched successfully"

# Step 4: Check agent status
echo ""
echo "Step 4: Checking agent status..."
agentcore status --agent "${AGENT_NAME}"

# Step 5: Test the agent
echo ""
echo "Step 5: Testing agent with sample invocation..."

TEST_PAYLOAD='{
  "event_type": "TRADE_EXTRACTED",
  "trade_id": "GCS382857",
  "source_type": "COUNTERPARTY",
  "table_name": "CounterpartyTradeData"
}'

echo "Test payload: ${TEST_PAYLOAD}"
echo ""
echo "To test manually, run:"
echo "  agentcore invoke --agent ${AGENT_NAME} '${TEST_PAYLOAD}'"

echo ""
echo "============================================="
echo "Trade Matching Agent deployed successfully!"
echo "============================================="
echo ""
echo "Agent Name: ${AGENT_NAME}"
echo "Region: ${REGION}"
echo "Runtime: ${RUNTIME}"
echo ""
echo "Useful commands:"
echo "  agentcore invoke --agent ${AGENT_NAME} '{...}'  # Invoke agent"
echo "  agentcore status --agent ${AGENT_NAME}          # Check status"
echo "  agentcore destroy --agent ${AGENT_NAME}         # Delete agent"
echo ""
