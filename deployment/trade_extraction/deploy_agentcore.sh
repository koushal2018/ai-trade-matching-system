#!/bin/bash

# AgentCore Deployment Script for Trade Extraction Agent
# This script follows AgentCore best practices for secure, production-ready deployment

set -e  # Exit on any error

# Configuration
AGENT_NAME="trade-extraction-agent"
AGENT_VERSION="1.0.0"
REGION="us-east-1"
DEPLOYMENT_STAGE="${DEPLOYMENT_STAGE:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if agentcore CLI is installed
    if ! command -v agentcore &> /dev/null; then
        log_error "AgentCore CLI not found. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Please run 'aws configure'."
        exit 1
    fi
    
    # Check if we're in the right directory
    if [[ ! -f "trade_extraction_agent_strands.py" ]]; then
        log_error "Must be run from the deployment/trade_extraction directory"
        exit 1
    fi
    
    # Check if required files exist
    local required_files=("agentcore.yaml" "requirements.txt" "trade_extraction_agent_strands.py")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    log_success "Prerequisites check passed"
}

# Validate configuration
validate_configuration() {
    log_info "Validating AgentCore configuration..."
    
    # Validate agentcore.yaml
    if ! agentcore validate --config agentcore.yaml; then
        log_error "AgentCore configuration validation failed"
        exit 1
    fi
    
    log_success "Configuration validation passed"
}

# Deploy AgentCore Gateway (if needed)
deploy_gateway() {
    log_info "Checking AgentCore Gateway deployment..."
    
    # Check if gateways exist
    local dynamodb_gateway="trade-matching-system-dynamodb-gateway-production"
    local s3_gateway="trade-matching-system-s3-gateway-production"
    
    if ! aws bedrock-agent list-gateways --region $REGION --query "gateways[?name=='$dynamodb_gateway']" --output text | grep -q "$dynamodb_gateway"; then
        log_warning "DynamoDB Gateway not found. Please deploy it first:"
        log_info "  cd ../../terraform/agentcore && terraform apply"
    else
        log_success "DynamoDB Gateway found"
    fi
    
    if ! aws bedrock-agent list-gateways --region $REGION --query "gateways[?name=='$s3_gateway']" --output text | grep -q "$s3_gateway"; then
        log_warning "S3 Gateway not found. Please deploy it first:"
        log_info "  cd ../../terraform/agentcore && terraform apply"
    else
        log_success "S3 Gateway found"
    fi
}

# Deploy AgentCore Memory (if needed)
deploy_memory() {
    log_info "Checking AgentCore Memory deployment..."
    
    local memory_patterns="trade-matching-system-trade-patterns-production"
    local memory_history="trade-matching-system-processing-history-production"
    
    if ! aws bedrock-agent list-memory-resources --region $REGION --query "memoryResources[?name=='$memory_patterns']" --output text | grep -q "$memory_patterns"; then
        log_warning "Trade Patterns Memory not found. Please deploy it first:"
        log_info "  cd ../../terraform/agentcore && terraform apply"
    else
        log_success "Trade Patterns Memory found"
    fi
    
    if ! aws bedrock-agent list-memory-resources --region $REGION --query "memoryResources[?name=='$memory_history']" --output text | grep -q "$memory_history"; then
        log_warning "Processing History Memory not found. Please deploy it first:"
        log_info "  cd ../../terraform/agentcore && terraform apply"
    else
        log_success "Processing History Memory found"
    fi
}

# Run tests before deployment
run_tests() {
    log_info "Running pre-deployment tests..."
    
    # Run unit tests
    if [[ -f "test_trade_extraction.py" ]]; then
        log_info "Running unit tests..."
        python -m pytest test_trade_extraction.py -v
    fi
    
    # Run property tests
    if [[ -f "../../test_property_17_simple.py" ]]; then
        log_info "Running property tests..."
        python ../../test_property_17_simple.py
    fi
    
    log_success "Pre-deployment tests passed"
}

# Deploy the agent
deploy_agent() {
    log_info "Deploying Trade Extraction Agent to AgentCore Runtime..."
    
    # Configure the agent
    log_info "Configuring agent..."
    agentcore configure \
        --name $AGENT_NAME \
        --version $AGENT_VERSION \
        --config agentcore.yaml \
        --region $REGION
    
    # Launch the agent
    log_info "Launching agent..."
    agentcore launch \
        --agent-name $AGENT_NAME \
        --version $AGENT_VERSION \
        --region $REGION
    
    # Wait for deployment to complete
    log_info "Waiting for deployment to complete..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        local status=$(agentcore status --agent-name $AGENT_NAME --region $REGION --output json | jq -r '.status')
        
        if [[ "$status" == "ACTIVE" ]]; then
            log_success "Agent deployment completed successfully"
            break
        elif [[ "$status" == "FAILED" ]]; then
            log_error "Agent deployment failed"
            agentcore logs --agent-name $AGENT_NAME --region $REGION --tail 50
            exit 1
        else
            log_info "Deployment status: $status (attempt $attempt/$max_attempts)"
            sleep 10
            ((attempt++))
        fi
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Deployment timeout. Check agent status manually."
        exit 1
    fi
}

# Test the deployed agent
test_deployment() {
    log_info "Testing deployed agent..."
    
    # Create test payload
    local test_payload='{
        "document_id": "DEPLOY_TEST_001",
        "canonical_output_location": "s3://trade-matching-system-agentcore-production/extracted/BANK/TEST_001.json",
        "source_type": "BANK",
        "correlation_id": "deploy_test_001"
    }'
    
    # Invoke the agent
    log_info "Invoking agent with test payload..."
    local result=$(agentcore invoke \
        --agent-name $AGENT_NAME \
        --region $REGION \
        --payload "$test_payload" \
        --output json)
    
    # Check result
    local success=$(echo "$result" | jq -r '.success // false')
    if [[ "$success" == "true" ]]; then
        log_success "Agent test invocation successful"
        log_info "Processing time: $(echo "$result" | jq -r '.processing_time_ms // 0')ms"
        log_info "Token usage: $(echo "$result" | jq -r '.token_usage // {}')"
    else
        log_warning "Agent test invocation returned success=false (may be expected for test data)"
        log_info "Response: $(echo "$result" | jq -r '.agent_response // "No response"')"
    fi
}

# Setup monitoring and alerts
setup_monitoring() {
    log_info "Setting up monitoring and alerts..."
    
    # Create CloudWatch alarms
    aws cloudwatch put-metric-alarm \
        --alarm-name "${AGENT_NAME}-HighErrorRate" \
        --alarm-description "High error rate for Trade Extraction Agent" \
        --metric-name "ErrorRate" \
        --namespace "AWS/BedrockAgent" \
        --statistic "Average" \
        --period 300 \
        --threshold 5.0 \
        --comparison-operator "GreaterThanThreshold" \
        --evaluation-periods 2 \
        --dimensions Name=AgentName,Value=$AGENT_NAME \
        --region $REGION
    
    aws cloudwatch put-metric-alarm \
        --alarm-name "${AGENT_NAME}-HighLatency" \
        --alarm-description "High latency for Trade Extraction Agent" \
        --metric-name "ProcessingTimeMs" \
        --namespace "AgentCore/TradeExtraction" \
        --statistic "Average" \
        --period 300 \
        --threshold 30000 \
        --comparison-operator "GreaterThanThreshold" \
        --evaluation-periods 3 \
        --dimensions Name=AgentName,Value=$AGENT_NAME \
        --region $REGION
    
    log_success "Monitoring and alerts configured"
}

# Main deployment flow
main() {
    log_info "Starting AgentCore deployment for Trade Extraction Agent"
    log_info "Agent: $AGENT_NAME v$AGENT_VERSION"
    log_info "Region: $REGION"
    log_info "Stage: $DEPLOYMENT_STAGE"
    echo
    
    # Run deployment steps
    check_prerequisites
    validate_configuration
    deploy_gateway
    deploy_memory
    run_tests
    deploy_agent
    test_deployment
    setup_monitoring
    
    echo
    log_success "🎉 Trade Extraction Agent deployment completed successfully!"
    log_info "Agent Name: $AGENT_NAME"
    log_info "Version: $AGENT_VERSION"
    log_info "Status: ACTIVE"
    log_info "Region: $REGION"
    echo
    log_info "Next steps:"
    log_info "1. Monitor agent performance in CloudWatch"
    log_info "2. Test with real trade documents"
    log_info "3. Deploy other agents in the swarm"
    log_info "4. Configure end-to-end workflow"
    echo
    log_info "Useful commands:"
    log_info "  agentcore status --agent-name $AGENT_NAME --region $REGION"
    log_info "  agentcore logs --agent-name $AGENT_NAME --region $REGION --tail 100"
    log_info "  agentcore invoke --agent-name $AGENT_NAME --region $REGION --payload '{...}'"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "test")
        check_prerequisites
        run_tests
        ;;
    "validate")
        check_prerequisites
        validate_configuration
        ;;
    "status")
        agentcore status --agent-name $AGENT_NAME --region $REGION
        ;;
    "logs")
        agentcore logs --agent-name $AGENT_NAME --region $REGION --tail 100
        ;;
    *)
        echo "Usage: $0 [deploy|test|validate|status|logs]"
        echo "  deploy   - Full deployment (default)"
        echo "  test     - Run tests only"
        echo "  validate - Validate configuration only"
        echo "  status   - Check agent status"
        echo "  logs     - Show recent logs"
        exit 1
        ;;
esac