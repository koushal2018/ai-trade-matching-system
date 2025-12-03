#!/bin/bash
# Master deployment script for all agents to AgentCore Runtime
# Requirements: 2.1, 2.2, 2.3, 2.4, 2.5

set -e

echo "========================================="
echo "AgentCore Deployment - All Agents"
echo "========================================="

# Configuration
REGION="${AWS_REGION:-us-east-1}"
S3_BUCKET="${S3_BUCKET_NAME:-trade-matching-system-agentcore-production}"

# Check prerequisites
echo "Checking prerequisites..."

# Check if agentcore CLI is installed
if ! command -v agentcore &> /dev/null; then
    echo "❌ ERROR: agentcore CLI not found. Please install it first."
    echo "Run: pip install bedrock-agentcore-starter-toolkit"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ ERROR: AWS credentials not configured."
    echo "Please configure AWS credentials with access to us-east-1 region."
    exit 1
fi

# Check environment variables (optional - memory is opt-in)
if [ -z "${AGENTCORE_MEMORY_ARN}" ]; then
    echo "⚠️  WARNING: AGENTCORE_MEMORY_ARN environment variable not set."
    echo "Memory integration will be skipped. Agents will still deploy."
    echo ""
    echo "To enable memory, set AGENTCORE_MEMORY_ARN before running this script."
    echo ""
fi

echo "✅ Prerequisites check passed!"
echo ""
echo "Configuration:"
echo "  Region: ${REGION}"
echo "  S3 Bucket: ${S3_BUCKET}"
echo "  Memory ARN: ${AGENTCORE_MEMORY_ARN:-Not set}"
echo ""

# Deploy agents in order
AGENTS=(
    "orchestrator"
    "pdf_adapter"
    "trade_extraction"
    "trade_matching"
    "exception_management"
)

FAILED_AGENTS=()
SUCCESSFUL_AGENTS=()

for agent in "${AGENTS[@]}"; do
    echo ""
    echo "========================================="
    echo "Deploying ${agent} agent..."
    echo "========================================="
    
    if [ ! -d "${agent}" ]; then
        echo "❌ ERROR: Directory ${agent} not found"
        FAILED_AGENTS+=("${agent}")
        continue
    fi
    
    cd "${agent}"
    
    if [ ! -f "deploy.sh" ]; then
        echo "❌ ERROR: deploy.sh not found in ${agent}"
        FAILED_AGENTS+=("${agent}")
        cd ..
        continue
    fi
    
    chmod +x deploy.sh
    
    if ./deploy.sh; then
        echo "✅ ${agent} deployment complete!"
        SUCCESSFUL_AGENTS+=("${agent}")
    else
        echo "❌ ${agent} deployment failed!"
        FAILED_AGENTS+=("${agent}")
    fi
    
    cd ..
    
    # Wait between deployments to avoid rate limits
    if [ "${agent}" != "exception_management" ]; then
        echo "Waiting 30 seconds before next deployment..."
        sleep 30
    fi
done

echo ""
echo "========================================="
echo "Deployment Summary"
echo "========================================="
echo ""

if [ ${#SUCCESSFUL_AGENTS[@]} -gt 0 ]; then
    echo "✅ Successfully deployed agents:"
    for agent in "${SUCCESSFUL_AGENTS[@]}"; do
        echo "   - ${agent}"
    done
fi

if [ ${#FAILED_AGENTS[@]} -gt 0 ]; then
    echo ""
    echo "❌ Failed deployments:"
    for agent in "${FAILED_AGENTS[@]}"; do
        echo "   - ${agent}"
    done
    echo ""
    echo "Please check the logs above for error details."
fi

echo ""
echo "========================================="
echo "Next Steps"
echo "========================================="
echo ""
echo "1. Verify all agents are active:"
echo "   agentcore status"
echo ""
echo "2. List all configured agents:"
echo "   agentcore configure list"
echo ""
echo "3. Test an agent:"
echo "   agentcore invoke --agent pdf_adapter_agent '{\"document_id\": \"test\", \"document_path\": \"s3://bucket/test.pdf\", \"source_type\": \"COUNTERPARTY\"}'"
echo ""
echo "4. View agent logs:"
echo "   agentcore status --agent <agent_name> -v"
echo ""

# Exit with error if any deployments failed
if [ ${#FAILED_AGENTS[@]} -gt 0 ]; then
    exit 1
fi

echo "All agents deployed successfully! 🎉"
