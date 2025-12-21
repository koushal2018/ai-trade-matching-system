#!/bin/bash
# Simple deployment script for Trade Extraction Agent using AgentCore
# Requirements: 3.5, 7.4

set -e

# Enable detailed logging
exec > >(tee -a deployment.log)
exec 2>&1

echo "================================================"
echo "Trade Extraction Agent Deployment"
echo "================================================"
echo "Deployment started at: $(date)"
echo "User: $(whoami)"
echo "Working directory: $(pwd)"

# Configuration
AGENT_NAME="${AGENT_NAME:-trade_extraction_agent}"
AGENT_VERSION="${AGENT_VERSION:-2.0.0}"
ENVIRONMENT="${ENVIRONMENT:-production}"
REGION="${AWS_REGION:-us-east-1}"
S3_BUCKET="${S3_BUCKET_NAME:-trade-matching-system-agentcore-production}"

# Agent files
ENTRYPOINT="agent.py"
REQUIREMENTS_FILE="requirements.txt"
AGENTCORE_CONFIG="agentcore.yaml"

echo "Deployment Configuration:"
echo "  Agent Name: ${AGENT_NAME}"
echo "  Version: ${AGENT_VERSION}"
echo "  Environment: ${ENVIRONMENT}"
echo "  Region: ${REGION}"
echo "  S3 Bucket: ${S3_BUCKET}"
echo "  Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# Logging function
log_step() {
    local step="$1"
    local message="$2"
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] DEPLOY_STEP_${step}: ${message}"
}

log_error() {
    local step="$1"
    local message="$2"
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] DEPLOY_ERROR_${step}: ${message}" >&2
}

log_success() {
    local step="$1"
    local message="$2"
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] DEPLOY_SUCCESS_${step}: ${message}"
}

# Check prerequisites
echo "Step 1: Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI not found. Please install AWS CLI"
    exit 1
fi

# Check AgentCore CLI
if ! command -v agentcore &> /dev/null; then
    echo "❌ Error: agentcore CLI not found. Please install: pip install bedrock-agentcore-starter-toolkit"
    exit 1
fi

# Check required files
for file in "${ENTRYPOINT}" "${REQUIREMENTS_FILE}" "${AGENTCORE_CONFIG}"; do
    if [ ! -f "${file}" ]; then
        echo "❌ Error: Required file ${file} not found"
        exit 1
    fi
done

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS credentials not configured or invalid"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Step 2: Configure AgentCore
echo ""
echo "Step 2: Configuring AgentCore agent..."

# Configure the agent
agentcore configure \
    --entrypoint "${ENTRYPOINT}" \
    --name "${AGENT_NAME}" \
    --runtime "PYTHON_3_11" \
    --requirements-file "${REQUIREMENTS_FILE}" \
    --region "${REGION}" \
    --config-file "${AGENTCORE_CONFIG}" \
    --non-interactive

echo "✅ AgentCore agent configured"

# Step 3: Launch the agent
echo ""
echo "Step 3: Launching agent to AgentCore Runtime..."

agentcore launch \
    --agent "${AGENT_NAME}" \
    --env "AWS_REGION=${REGION}" \
    --env "S3_BUCKET_NAME=${S3_BUCKET}" \
    --env "DYNAMODB_BANK_TABLE=BankTradeData" \
    --env "DYNAMODB_COUNTERPARTY_TABLE=CounterpartyTradeData" \
    --env "AGENT_REGISTRY_TABLE=AgentRegistry" \
    --env "DEPLOYMENT_STAGE=${ENVIRONMENT}" \
    --env "AGENT_VERSION=${AGENT_VERSION}" \
    --auto-update-on-conflict

echo "✅ Agent launched successfully"

# Step 4: Register agent in DynamoDB
echo ""
echo "Step 4: Registering agent in DynamoDB AgentRegistry..."

# Get the runtime ARN from AgentCore
RUNTIME_ARN=$(agentcore status --agent "${AGENT_NAME}" --output json | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('runtime_arn', ''))
except:
    print('')
")

if [ -n "${RUNTIME_ARN}" ]; then
    # Run the agent registration script
    python3 register_agent_deployment.py register \
        --agent-name "${AGENT_NAME}" \
        --version "${AGENT_VERSION}" \
        --environment "${ENVIRONMENT}" \
        --region "${REGION}" \
        --runtime-arn "${RUNTIME_ARN}"
else
    echo "⚠️  Warning: Could not retrieve runtime ARN, skipping agent registration"
fi

# Step 5: Validate deployment
echo ""
echo "Step 5: Validating deployment..."

# Check agent status
echo "Checking agent status..."
agentcore status --agent "${AGENT_NAME}"

# Test basic connectivity
echo ""
echo "Testing basic agent connectivity..."
TEST_PAYLOAD='{
  "document_id": "deployment_test_001",
  "canonical_output_location": "s3://'"${S3_BUCKET}"'/extracted/BANK/deployment_test_001.json",
  "source_type": "BANK",
  "correlation_id": "corr_deploy_test_001"
}'

echo "Test payload: ${TEST_PAYLOAD}"
echo ""
echo "To test the agent manually, run:"
echo "  agentcore invoke --agent ${AGENT_NAME} '${TEST_PAYLOAD}'"

echo ""
echo "================================================"
echo "Trade Extraction Agent Deployment Complete!"
echo "================================================"
echo ""
echo "Deployment Summary:"
echo "  Agent Name: ${AGENT_NAME}"
echo "  Version: ${AGENT_VERSION}"
echo "  Environment: ${ENVIRONMENT}"
echo "  Region: ${REGION}"
echo "  Runtime ARN: ${RUNTIME_ARN}"
echo ""
echo "Useful commands:"
echo "  agentcore invoke --agent ${AGENT_NAME} '{...}'     # Invoke agent"
echo "  agentcore status --agent ${AGENT_NAME}             # Check status"
echo "  agentcore logs --agent ${AGENT_NAME} --follow      # View logs"
echo ""
echo "To clean up:"
echo "  agentcore destroy --agent ${AGENT_NAME}            # Delete agent"
echo ""