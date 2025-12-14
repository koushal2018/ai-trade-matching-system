#!/bin/bash
#
# AgentCore Runtime Deployment Script
#
# This script deploys the Trade Matching Swarm to Amazon Bedrock AgentCore Runtime.
# It handles configuration, deployment, and verification of the agent.
#
# Prerequisites:
# - AgentCore CLI installed (pip install bedrock-agentcore)
# - AWS credentials configured
# - AGENTCORE_MEMORY_ID environment variable set (run setup_memory.py first)
#
# Usage:
#   ./deploy_agentcore.sh [--agent-name NAME] [--region REGION]
#

set -e  # Exit on error

# Default values
AGENT_NAME="${AGENT_NAME:-trade-matching-swarm}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ACTOR_ID="${ACTOR_ID:-trade_matching_system}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent-name)
            AGENT_NAME="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --agent-name NAME    Agent name (default: trade-matching-swarm)"
            echo "  --region REGION      AWS region (default: us-east-1)"
            echo "  --help, -h           Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  AGENTCORE_MEMORY_ID       Required - Memory resource ID"
            echo "  S3_BUCKET_NAME            Required - S3 bucket for documents"
            echo "  DYNAMODB_BANK_TABLE       Required - Bank trades table"
            echo "  DYNAMODB_COUNTERPARTY_TABLE  Required - Counterparty trades table"
            echo "  DYNAMODB_EXCEPTIONS_TABLE    Required - Exceptions table"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print section headers
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning messages
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Validate prerequisites
print_header "Validating Prerequisites"

# Check if agentcore CLI is installed
if ! command_exists agentcore; then
    print_error "AgentCore CLI not found"
    echo "Install with: pip install bedrock-agentcore"
    exit 1
fi
print_success "AgentCore CLI installed"

# Check if AWS CLI is installed
if ! command_exists aws; then
    print_warning "AWS CLI not found (optional but recommended)"
else
    print_success "AWS CLI installed"
fi

# Check required environment variables
if [ -z "$AGENTCORE_MEMORY_ID" ]; then
    print_error "AGENTCORE_MEMORY_ID environment variable not set"
    echo "Run setup_memory.py first to create the memory resource"
    exit 1
fi
print_success "AGENTCORE_MEMORY_ID set: $AGENTCORE_MEMORY_ID"

if [ -z "$S3_BUCKET_NAME" ]; then
    print_error "S3_BUCKET_NAME environment variable not set"
    exit 1
fi
print_success "S3_BUCKET_NAME set: $S3_BUCKET_NAME"

if [ -z "$DYNAMODB_BANK_TABLE" ]; then
    print_error "DYNAMODB_BANK_TABLE environment variable not set"
    exit 1
fi
print_success "DYNAMODB_BANK_TABLE set: $DYNAMODB_BANK_TABLE"

if [ -z "$DYNAMODB_COUNTERPARTY_TABLE" ]; then
    print_error "DYNAMODB_COUNTERPARTY_TABLE environment variable not set"
    exit 1
fi
print_success "DYNAMODB_COUNTERPARTY_TABLE set: $DYNAMODB_COUNTERPARTY_TABLE"

if [ -z "$DYNAMODB_EXCEPTIONS_TABLE" ]; then
    print_error "DYNAMODB_EXCEPTIONS_TABLE environment variable not set"
    exit 1
fi
print_success "DYNAMODB_EXCEPTIONS_TABLE set: $DYNAMODB_EXCEPTIONS_TABLE"

# Check if agentcore.yaml exists
if [ ! -f "agentcore.yaml" ]; then
    print_error "agentcore.yaml not found in current directory"
    echo "Make sure you're running this script from deployment/swarm_agentcore/"
    exit 1
fi
print_success "agentcore.yaml found"


# Configure the agent
print_header "Configuring Agent"

echo "Agent Name: $AGENT_NAME"
echo "Region: $AWS_REGION"
echo "Actor ID: $ACTOR_ID"
echo ""

# Run agentcore configure
echo "Running: agentcore configure --name $AGENT_NAME"
if agentcore configure --name "$AGENT_NAME"; then
    print_success "Agent configured successfully"
else
    print_error "Agent configuration failed"
    exit 1
fi

# Deploy the agent
print_header "Deploying Agent to AgentCore Runtime"

echo "This may take a few minutes..."
echo ""

# Run agentcore launch
echo "Running: agentcore launch --agent-name $AGENT_NAME"
if agentcore launch --agent-name "$AGENT_NAME"; then
    print_success "Agent deployed successfully"
else
    print_error "Agent deployment failed"
    exit 1
fi

# Verify deployment status
print_header "Verifying Deployment"

echo "Checking agent status..."
if agentcore status --agent-name "$AGENT_NAME"; then
    print_success "Agent is running"
else
    print_warning "Could not verify agent status"
fi

# Get agent endpoint
print_header "Deployment Complete"

echo "Agent Name: $AGENT_NAME"
echo "Region: $AWS_REGION"
echo ""

# Try to get the endpoint URL
if command_exists aws; then
    echo "Retrieving agent endpoint..."
    # Note: The actual command to get the endpoint may vary
    # This is a placeholder - adjust based on actual AgentCore CLI capabilities
    echo "Use 'agentcore info --agent-name $AGENT_NAME' to get endpoint details"
else
    echo "Install AWS CLI to retrieve endpoint URL automatically"
fi

echo ""
print_success "Deployment successful!"
echo ""
echo "To invoke the agent:"
echo "  agentcore invoke --agent-name $AGENT_NAME --payload '{\"document_path\": \"...\", \"source_type\": \"BANK\"}'"
echo ""
echo "To view logs:"
echo "  agentcore logs --agent-name $AGENT_NAME"
echo ""
echo "To update the agent:"
echo "  agentcore update --agent-name $AGENT_NAME"
echo ""

exit 0
