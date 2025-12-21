#!/bin/bash
# DEPRECATED: Use deploy.sh instead
# This script is kept for reference but CloudFormation is not needed
# since AgentCore handles IAM role creation automatically
# Requirements: 3.5, 7.4

echo "⚠️  WARNING: This script is deprecated."
echo "Use deploy.sh instead - CloudFormation is not needed for AgentCore deployment."
echo "AgentCore automatically creates the required IAM role."
echo ""
echo "Run: ./deploy.sh"
exit 1

set -e

echo "================================================"
echo "Enhanced Trade Extraction Agent Deployment"
echo "================================================"

# Configuration
AGENT_NAME="${AGENT_NAME:-trade-extraction-agent}"
AGENT_VERSION="${AGENT_VERSION:-2.0.0}"
ENVIRONMENT="${ENVIRONMENT:-production}"
REGION="${AWS_REGION:-us-east-1}"
S3_BUCKET="${S3_BUCKET_NAME:-trade-matching-system-agentcore-production}"
STACK_NAME="${STACK_NAME:-trade-extraction-agent-${ENVIRONMENT}}"
NOTIFICATION_EMAIL="${NOTIFICATION_EMAIL:-admin@example.com}"

# CloudFormation template and parameters
CF_TEMPLATE="cloudformation-template.yaml"
CF_PARAMETERS_FILE="cf-parameters-${ENVIRONMENT}.json"

# Agent files
ENTRYPOINT="trade_extraction_agent_strands.py"
REQUIREMENTS_FILE="requirements.txt"
AGENTCORE_CONFIG="agentcore.yaml"

echo "Deployment Configuration:"
echo "  Agent Name: ${AGENT_NAME}"
echo "  Version: ${AGENT_VERSION}"
echo "  Environment: ${ENVIRONMENT}"
echo "  Region: ${REGION}"
echo "  S3 Bucket: ${S3_BUCKET}"
echo "  Stack Name: ${STACK_NAME}"
echo "  Notification Email: ${NOTIFICATION_EMAIL}"
echo ""

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
for file in "${CF_TEMPLATE}" "${ENTRYPOINT}" "${REQUIREMENTS_FILE}" "${AGENTCORE_CONFIG}"; do
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

# Step 2: Create CloudFormation parameters file
echo ""
echo "Step 2: Creating CloudFormation parameters..."

cat > "${CF_PARAMETERS_FILE}" << EOF
[
  {
    "ParameterKey": "AgentName",
    "ParameterValue": "${AGENT_NAME}"
  },
  {
    "ParameterKey": "AgentVersion",
    "ParameterValue": "${AGENT_VERSION}"
  },
  {
    "ParameterKey": "Environment",
    "ParameterValue": "${ENVIRONMENT}"
  },
  {
    "ParameterKey": "S3BucketName",
    "ParameterValue": "${S3_BUCKET}"
  },
  {
    "ParameterKey": "BankTableName",
    "ParameterValue": "BankTradeData"
  },
  {
    "ParameterKey": "CounterpartyTableName",
    "ParameterValue": "CounterpartyTradeData"
  },
  {
    "ParameterKey": "AgentRegistryTableName",
    "ParameterValue": "AgentRegistry"
  },
  {
    "ParameterKey": "NotificationEmail",
    "ParameterValue": "${NOTIFICATION_EMAIL}"
  }
]
EOF

echo "✅ CloudFormation parameters created: ${CF_PARAMETERS_FILE}"

# Step 3: Deploy CloudFormation stack
echo ""
echo "Step 3: Deploying CloudFormation stack..."

# Check if stack exists
if aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region "${REGION}" &> /dev/null; then
    echo "Stack ${STACK_NAME} exists, updating..."
    STACK_OPERATION="update-stack"
else
    echo "Stack ${STACK_NAME} does not exist, creating..."
    STACK_OPERATION="create-stack"
fi

# Deploy the stack
aws cloudformation "${STACK_OPERATION}" \
    --stack-name "${STACK_NAME}" \
    --template-body "file://${CF_TEMPLATE}" \
    --parameters "file://${CF_PARAMETERS_FILE}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "${REGION}" \
    --tags Key=Agent,Value="${AGENT_NAME}" Key=Environment,Value="${ENVIRONMENT}"

echo "Waiting for CloudFormation stack operation to complete..."
aws cloudformation wait stack-${STACK_OPERATION%-stack}-complete \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}"

# Get stack outputs
AGENT_ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`AgentRoleArn`].OutputValue' \
    --output text)

LOG_GROUP_NAME=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`LogGroupName`].OutputValue' \
    --output text)

echo "✅ CloudFormation stack deployed successfully"
echo "  Agent Role ARN: ${AGENT_ROLE_ARN}"
echo "  Log Group: ${LOG_GROUP_NAME}"

# Step 4: Configure AgentCore
echo ""
echo "Step 4: Configuring AgentCore agent..."

# Update agentcore.yaml with the IAM role
if [ -n "${AGENT_ROLE_ARN}" ]; then
    # Create a temporary agentcore config with the correct role
    cp "${AGENTCORE_CONFIG}" "${AGENTCORE_CONFIG}.backup"
    
    # Use Python to update the YAML (more reliable than sed)
    python3 << EOF
import yaml
import sys

try:
    with open('${AGENTCORE_CONFIG}', 'r') as f:
        config = yaml.safe_load(f)
    
    # Update the agent configuration
    config['agent']['version'] = '${AGENT_VERSION}'
    config['agent']['environment']['DEPLOYMENT_STAGE'] = '${ENVIRONMENT}'
    
    # Add IAM role if not present
    if 'permissions' not in config['agent']:
        config['agent']['permissions'] = []
    
    # Update runtime ARN in deployment section
    if 'deployment' not in config:
        config['deployment'] = {}
    
    config['deployment']['iam_role_arn'] = '${AGENT_ROLE_ARN}'
    
    with open('${AGENTCORE_CONFIG}', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    print("✅ AgentCore configuration updated")
except Exception as e:
    print(f"❌ Error updating AgentCore config: {e}")
    sys.exit(1)
EOF
fi

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

# Step 5: Launch the agent
echo ""
echo "Step 5: Launching agent to AgentCore Runtime..."

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

# Step 6: Register agent in DynamoDB
echo ""
echo "Step 6: Registering agent in DynamoDB AgentRegistry..."

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
    python3 << EOF
import sys
import os
sys.path.append('.')

try:
    from agent_registry import AgentRegistryManager
    
    registry = AgentRegistryManager(region_name='${REGION}')
    success, error = registry.register_trade_extraction_agent(
        runtime_arn='${RUNTIME_ARN}',
        version='${AGENT_VERSION}',
        status='active'
    )
    
    if success:
        print("✅ Agent registered in DynamoDB AgentRegistry")
    else:
        print(f"❌ Failed to register agent: {error}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error during agent registration: {e}")
    sys.exit(1)
EOF
else
    echo "⚠️  Warning: Could not retrieve runtime ARN, skipping agent registration"
fi

# Step 7: Validate deployment
echo ""
echo "Step 7: Validating deployment..."

# Check agent status
echo "Checking agent status..."
agentcore status --agent "${AGENT_NAME}" 2>&1 | tee -a deployment.log

# Test basic connectivity with enhanced logging
echo ""
echo "Testing basic agent connectivity..."
TEST_PAYLOAD='{
  "document_id": "deployment_test_001",
  "canonical_output_location": "s3://'"${S3_BUCKET}"'/extracted/BANK/deployment_test_001.json",
  "source_type": "BANK",
  "correlation_id": "corr_deploy_test_001"
}'

echo "Test payload: ${TEST_PAYLOAD}" | tee -a deployment.log
echo ""

# Run deployment validation script
echo "Running comprehensive deployment validation..."
if [ -f "validate_deployment.py" ]; then
    python3 validate_deployment.py \
        --agent-name "${AGENT_NAME}" \
        --region "${REGION}" \
        --environment "${ENVIRONMENT}" \
        --output-file "deployment-validation-results.json" \
        --verbose 2>&1 | tee -a deployment.log
    
    if [ $? -eq 0 ]; then
        echo "✅ Deployment validation passed"
    else
        echo "⚠️  Deployment validation found issues - check deployment-validation-results.json"
    fi
else
    echo "⚠️  Deployment validation script not found"
fi

echo ""
echo "To test the agent manually, run:"
echo "  agentcore invoke --agent ${AGENT_NAME} '${TEST_PAYLOAD}'"
echo ""
echo "To monitor logs in real-time:"
echo "  aws logs tail ${LOG_GROUP_NAME} --follow --region ${REGION}"

# Step 8: Cleanup temporary files
echo ""
echo "Step 8: Cleaning up temporary files..."
rm -f "${CF_PARAMETERS_FILE}"
if [ -f "${AGENTCORE_CONFIG}.backup" ]; then
    mv "${AGENTCORE_CONFIG}.backup" "${AGENTCORE_CONFIG}"
fi

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
echo "  CloudFormation Stack: ${STACK_NAME}"
echo "  Agent Role ARN: ${AGENT_ROLE_ARN}"
echo "  Log Group: ${LOG_GROUP_NAME}"
echo "  Runtime ARN: ${RUNTIME_ARN}"
echo ""
echo "Useful commands:"
echo "  agentcore invoke --agent ${AGENT_NAME} '{...}'     # Invoke agent"
echo "  agentcore status --agent ${AGENT_NAME}             # Check status"
echo "  aws logs tail ${LOG_GROUP_NAME} --follow           # View logs"
echo "  aws cloudformation describe-stacks --stack-name ${STACK_NAME}  # Check CF stack"
echo ""
echo "To clean up:"
echo "  agentcore destroy --agent ${AGENT_NAME}            # Delete agent"
echo "  aws cloudformation delete-stack --stack-name ${STACK_NAME}     # Delete CF stack"
echo ""