#!/bin/bash

# Enhanced Trade Reconciliation Solution Deployment Script
# Supports AI provider configuration and regional deployments

set -e  # Exit immediately if a command exits with a non-zero status

# Function to check CloudFormation events for errors
check_stack_events() {
  local stack_name=$1
  local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S")
  
  echo "\nChecking recent CloudFormation events for errors..."
  $AWS_CMD cloudformation describe-stack-events \
    --stack-name $stack_name \
    --query "StackEvents[?ResourceStatus=='CREATE_FAILED' || ResourceStatus=='UPDATE_FAILED' || ResourceStatus=='DELETE_FAILED'].{Time:Timestamp,Resource:LogicalResourceId,Status:ResourceStatus,Reason:ResourceStatusReason}" \
    --output table
  
  echo "\nMost recent events:"
  $AWS_CMD cloudformation describe-stack-events \
    --stack-name $stack_name \
    --query "StackEvents[0:5].{Time:Timestamp,Resource:LogicalResourceId,Status:ResourceStatus,Reason:ResourceStatusReason}" \
    --output table
}

# Default configuration - can be overridden by environment variables or command line
STACK_NAME="${STACK_NAME:-trade-reconciliation-enhanced}"
S3_BUCKET="${S3_BUCKET:-trade-reconciliation-system-us-west-2}"
S3_PREFIX="${S3_PREFIX:-cloudformation-templates}"
REGION="${REGION:-us-west-2}"
ENVIRONMENT="${ENVIRONMENT:-dev}"

# AI Provider Configuration (new parameters)
AI_PROVIDER_TYPE="${AI_PROVIDER_TYPE:-bedrock}"
DECISION_MODE="${DECISION_MODE:-deterministic}"
AI_PROVIDER_REGION="${AI_PROVIDER_REGION:-$REGION}"
BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID:-anthropic.claude-3-sonnet-20240229-v1:0}"
SAGEMAKER_ENDPOINT_NAME="${SAGEMAKER_ENDPOINT_NAME:-}"
HUGGINGFACE_MODEL_NAME="${HUGGINGFACE_MODEL_NAME:-microsoft/DialoGPT-medium}"
HUGGINGFACE_API_TOKEN="${HUGGINGFACE_API_TOKEN:-}"
CONFIDENCE_THRESHOLD="${CONFIDENCE_THRESHOLD:-0.8}"
SEMANTIC_THRESHOLD="${SEMANTIC_THRESHOLD:-0.85}"
ENABLE_PERFORMANCE_OPTIMIZATION="${ENABLE_PERFORMANCE_OPTIMIZATION:-true}"

# Regional template selection
USE_REGIONAL_TEMPLATE="${USE_REGIONAL_TEMPLATE:-true}"

# Use AWS CLI command
AWS_CMD="aws"

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Enhanced Trade Reconciliation Solution Deployment

OPTIONS:
    --stack-name NAME           CloudFormation stack name (default: trade-reconciliation-enhanced)
    --bucket BUCKET             S3 bucket for templates (default: trade-reconciliation-system-us-west-2)
    --region REGION             AWS region (default: us-west-2)
    --environment ENV           Environment: dev, test, prod (default: dev)
    --ai-provider PROVIDER      AI provider: bedrock, sagemaker, huggingface, none (default: bedrock)
    --decision-mode MODE        Decision mode: deterministic, llm, hybrid (default: deterministic)
    --ai-region REGION          AI provider region (default: same as deployment region)
    --bedrock-model MODEL       Bedrock model ID (default: anthropic.claude-3-sonnet-20240229-v1:0)
    --sagemaker-endpoint NAME   SageMaker endpoint name (required for sagemaker provider)
    --huggingface-model MODEL   HuggingFace model name (default: microsoft/DialoGPT-medium)
    --huggingface-token TOKEN   HuggingFace API token (required for huggingface provider)
    --confidence-threshold NUM  AI confidence threshold (default: 0.8)
    --semantic-threshold NUM    Semantic similarity threshold (default: 0.85)
    --no-regional-template      Use generic template instead of regional template
    --validate-only             Only validate configuration, don't deploy
    --help                      Show this help message

EXAMPLES:
    # Deploy with Bedrock in US region
    $0 --region us-east-1 --ai-provider bedrock --decision-mode hybrid

    # Deploy with SageMaker in UAE region
    $0 --region me-central-1 --ai-provider sagemaker --sagemaker-endpoint my-endpoint --decision-mode llm

    # Deploy deterministic mode (no AI)
    $0 --region eu-west-1 --ai-provider none --decision-mode deterministic

EOF
}

# Function to get regional template
get_regional_template() {
    local region=$1
    
    if [[ "$USE_REGIONAL_TEMPLATE" == "false" ]]; then
        echo "master-template.yaml"
        return
    fi
    
    case $region in
        us-east-1|us-west-2)
            echo "regional/us-master-template.yaml"
            ;;
        eu-west-1|eu-central-1)
            echo "regional/eu-master-template.yaml"
            ;;
        me-central-1|me-south-1)
            echo "regional/uae-master-template.yaml"
            ;;
        *)
            echo "master-template.yaml"
            ;;
    esac
}

# Function to validate AI provider configuration
validate_ai_config() {
    echo "Validating AI provider configuration..."
    
    # Check AI provider availability by region
    case $REGION in
        me-central-1|me-south-1)
            if [[ "$AI_PROVIDER_TYPE" == "bedrock" ]]; then
                echo "Error: Bedrock is not available in UAE regions. Use 'sagemaker' or 'huggingface' instead."
                exit 1
            fi
            ;;
    esac
    
    # Check required parameters for each provider
    case $AI_PROVIDER_TYPE in
        sagemaker)
            if [[ -z "$SAGEMAKER_ENDPOINT_NAME" ]]; then
                echo "Error: SageMaker endpoint name is required when using sagemaker provider."
                echo "Use --sagemaker-endpoint parameter or set SAGEMAKER_ENDPOINT_NAME environment variable."
                exit 1
            fi
            ;;
        huggingface)
            if [[ -z "$HUGGINGFACE_API_TOKEN" ]]; then
                echo "Error: HuggingFace API token is required when using huggingface provider."
                echo "Use --huggingface-token parameter or set HUGGINGFACE_API_TOKEN environment variable."
                exit 1
            fi
            ;;
    esac
    
    # Check decision mode compatibility
    if [[ "$DECISION_MODE" == "llm" || "$DECISION_MODE" == "hybrid" ]]; then
        if [[ "$AI_PROVIDER_TYPE" == "none" ]]; then
            echo "Error: Decision mode '$DECISION_MODE' requires an AI provider, but 'none' was specified."
            exit 1
        fi
    fi
    
    echo "AI configuration validation passed."
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --bucket)
            S3_BUCKET="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            AI_PROVIDER_REGION="${AI_PROVIDER_REGION:-$2}"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --ai-provider)
            AI_PROVIDER_TYPE="$2"
            shift 2
            ;;
        --decision-mode)
            DECISION_MODE="$2"
            shift 2
            ;;
        --ai-region)
            AI_PROVIDER_REGION="$2"
            shift 2
            ;;
        --bedrock-model)
            BEDROCK_MODEL_ID="$2"
            shift 2
            ;;
        --sagemaker-endpoint)
            SAGEMAKER_ENDPOINT_NAME="$2"
            shift 2
            ;;
        --huggingface-model)
            HUGGINGFACE_MODEL_NAME="$2"
            shift 2
            ;;
        --huggingface-token)
            HUGGINGFACE_API_TOKEN="$2"
            shift 2
            ;;
        --confidence-threshold)
            CONFIDENCE_THRESHOLD="$2"
            shift 2
            ;;
        --semantic-threshold)
            SEMANTIC_THRESHOLD="$2"
            shift 2
            ;;
        --no-regional-template)
            USE_REGIONAL_TEMPLATE="false"
            shift
            ;;
        --validate-only)
            VALIDATE_ONLY="true"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate AI configuration
validate_ai_config

# Exit if validate-only mode
if [[ "$VALIDATE_ONLY" == "true" ]]; then
    echo "Configuration validation completed successfully."
    echo "Configuration summary:"
    echo "  Stack Name: $STACK_NAME"
    echo "  Region: $REGION"
    echo "  Environment: $ENVIRONMENT"
    echo "  AI Provider: $AI_PROVIDER_TYPE"
    echo "  Decision Mode: $DECISION_MODE"
    echo "  AI Region: $AI_PROVIDER_REGION"
    echo "  Template: $(get_regional_template $REGION)"
    exit 0
fi

# Check if S3 bucket exists
echo "Checking if S3 bucket exists..."
# Set default region for all AWS commands
export AWS_DEFAULT_REGION=$REGION
if ! $AWS_CMD s3api head-bucket --bucket $S3_BUCKET 2>/dev/null; then
  echo "Error: S3 bucket '$S3_BUCKET' does not exist or you don't have access to it."
  echo "Please create the bucket or update the S3_BUCKET variable."
  exit 1
fi

# First, upload the templates to S3
echo "Uploading CloudFormation templates to S3..."
$AWS_CMD s3 cp ./client-deployment/cloudformation/ s3://$S3_BUCKET/$S3_PREFIX/ --recursive

# Determine which template to use
TEMPLATE_FILE=$(get_regional_template $REGION)
echo "Using template: $TEMPLATE_FILE"

# Verify main template was uploaded
echo "Verifying template uploads..."
if ! $AWS_CMD s3api head-object --bucket $S3_BUCKET --key $S3_PREFIX/$TEMPLATE_FILE &>/dev/null; then
    echo "Error: Template $TEMPLATE_FILE was not uploaded to S3."
    exit 1
fi

# Verify core templates exist
CORE_TEMPLATES=("core-infrastructure.yaml" "api-lambda.yaml")
for template in "${CORE_TEMPLATES[@]}"; do
  if ! $AWS_CMD s3api head-object --bucket $S3_BUCKET --key $S3_PREFIX/$template &>/dev/null; then
    echo "Error: Core template $template was not uploaded to S3."
    exit 1
  fi
done

# Validate main template
echo "Validating CloudFormation template: $TEMPLATE_FILE"
TEMPLATE_URL="https://$S3_BUCKET.s3.$REGION.amazonaws.com/$S3_PREFIX/$TEMPLATE_FILE"
echo "Template URL: $TEMPLATE_URL"

$AWS_CMD cloudformation validate-template --template-url $TEMPLATE_URL

if [ $? -ne 0 ]; then
  echo "Error validating $TEMPLATE_FILE. Exiting."
  exit 1
fi

echo "Template validation successful."

# Check if stack already exists
STACK_EXISTS=$($AWS_CMD cloudformation describe-stacks --stack-name $STACK_NAME 2>/dev/null || echo "")

# Check if stack exists but is in a failed state
if [ -n "$STACK_EXISTS" ]; then
  STACK_STATUS=$($AWS_CMD cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].StackStatus" --output text)
  echo "Current stack status: $STACK_STATUS"
  
  if [[ $STACK_STATUS == *FAILED* || $STACK_STATUS == *ROLLBACK* ]]; then
    echo "Warning: Stack exists but is in a failed state: $STACK_STATUS"
    echo "You may need to delete the stack before retrying: $AWS_CMD cloudformation delete-stack --stack-name $STACK_NAME"
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Exiting deployment process."
      exit 1
    fi
  fi
fi

if [ -z "$STACK_EXISTS" ]; then
  # Create new stack
  echo "Deploying new CloudFormation stack with AI enhancements..."
  echo "Configuration:"
  echo "  AI Provider: $AI_PROVIDER_TYPE"
  echo "  Decision Mode: $DECISION_MODE"
  echo "  AI Region: $AI_PROVIDER_REGION"
  
  # Build parameters array
  PARAMETERS=(
    "ParameterKey=TemplateS3Bucket,ParameterValue=$S3_BUCKET"
    "ParameterKey=TemplateS3Path,ParameterValue=$S3_PREFIX"
    "ParameterKey=EnvironmentName,ParameterValue=$ENVIRONMENT"
    "ParameterKey=ApiStageName,ParameterValue=api"
    "ParameterKey=AIProviderType,ParameterValue=$AI_PROVIDER_TYPE"
    "ParameterKey=DecisionMode,ParameterValue=$DECISION_MODE"
    "ParameterKey=AIProviderRegion,ParameterValue=$AI_PROVIDER_REGION"
    "ParameterKey=ConfidenceThreshold,ParameterValue=$CONFIDENCE_THRESHOLD"
    "ParameterKey=SemanticThreshold,ParameterValue=$SEMANTIC_THRESHOLD"
    "ParameterKey=EnablePerformanceOptimization,ParameterValue=$ENABLE_PERFORMANCE_OPTIMIZATION"
  )
  
  # Add provider-specific parameters
  if [[ "$AI_PROVIDER_TYPE" == "bedrock" ]]; then
    PARAMETERS+=("ParameterKey=BedrockModelId,ParameterValue=$BEDROCK_MODEL_ID")
  elif [[ "$AI_PROVIDER_TYPE" == "sagemaker" ]]; then
    PARAMETERS+=("ParameterKey=SagemakerEndpointName,ParameterValue=$SAGEMAKER_ENDPOINT_NAME")
  elif [[ "$AI_PROVIDER_TYPE" == "huggingface" ]]; then
    PARAMETERS+=("ParameterKey=HuggingfaceModelName,ParameterValue=$HUGGINGFACE_MODEL_NAME")
    if [[ -n "$HUGGINGFACE_API_TOKEN" ]]; then
      PARAMETERS+=("ParameterKey=HuggingfaceApiToken,ParameterValue=$HUGGINGFACE_API_TOKEN")
    fi
  fi
  
  $AWS_CMD cloudformation create-stack \
    --stack-name $STACK_NAME \
    --template-url $TEMPLATE_URL \
    --parameters "${PARAMETERS[@]}" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
    
  echo "Stack creation initiated. Waiting for stack to complete..."
  $AWS_CMD cloudformation wait stack-create-complete --stack-name $STACK_NAME
  
  if [ $? -eq 0 ]; then
    echo "Stack creation completed successfully."
  else
    echo "Stack creation failed or timed out."
    check_stack_events $STACK_NAME
    exit 1
  fi
else
  # Update existing stack
  echo "Updating existing CloudFormation stack with AI enhancements..."
  echo "Configuration:"
  echo "  AI Provider: $AI_PROVIDER_TYPE"
  echo "  Decision Mode: $DECISION_MODE"
  echo "  AI Region: $AI_PROVIDER_REGION"
  
  # Build parameters array
  PARAMETERS=(
    "ParameterKey=TemplateS3Bucket,ParameterValue=$S3_BUCKET"
    "ParameterKey=TemplateS3Path,ParameterValue=$S3_PREFIX"
    "ParameterKey=EnvironmentName,ParameterValue=$ENVIRONMENT"
    "ParameterKey=ApiStageName,ParameterValue=api"
    "ParameterKey=AIProviderType,ParameterValue=$AI_PROVIDER_TYPE"
    "ParameterKey=DecisionMode,ParameterValue=$DECISION_MODE"
    "ParameterKey=AIProviderRegion,ParameterValue=$AI_PROVIDER_REGION"
    "ParameterKey=ConfidenceThreshold,ParameterValue=$CONFIDENCE_THRESHOLD"
    "ParameterKey=SemanticThreshold,ParameterValue=$SEMANTIC_THRESHOLD"
    "ParameterKey=EnablePerformanceOptimization,ParameterValue=$ENABLE_PERFORMANCE_OPTIMIZATION"
  )
  
  # Add provider-specific parameters
  if [[ "$AI_PROVIDER_TYPE" == "bedrock" ]]; then
    PARAMETERS+=("ParameterKey=BedrockModelId,ParameterValue=$BEDROCK_MODEL_ID")
  elif [[ "$AI_PROVIDER_TYPE" == "sagemaker" ]]; then
    PARAMETERS+=("ParameterKey=SagemakerEndpointName,ParameterValue=$SAGEMAKER_ENDPOINT_NAME")
  elif [[ "$AI_PROVIDER_TYPE" == "huggingface" ]]; then
    PARAMETERS+=("ParameterKey=HuggingfaceModelName,ParameterValue=$HUGGINGFACE_MODEL_NAME")
    if [[ -n "$HUGGINGFACE_API_TOKEN" ]]; then
      PARAMETERS+=("ParameterKey=HuggingfaceApiToken,ParameterValue=$HUGGINGFACE_API_TOKEN")
    fi
  fi
  
  $AWS_CMD cloudformation update-stack \
    --stack-name $STACK_NAME \
    --template-url $TEMPLATE_URL \
    --parameters "${PARAMETERS[@]}" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
    
  echo "Stack update initiated. Waiting for stack to complete..."
  $AWS_CMD cloudformation wait stack-update-complete --stack-name $STACK_NAME
  
  if [ $? -eq 0 ]; then
    echo "Stack update completed successfully."
  else
    echo "Stack update failed or timed out."
    check_stack_events $STACK_NAME
    exit 1
  fi
fi

echo "Enhanced deployment process completed. Check the AWS CloudFormation console for stack details."
echo ""
echo "Deployment Summary:"
echo "  Stack Name: $STACK_NAME"
echo "  Region: $REGION"
echo "  Environment: $ENVIRONMENT"
echo "  AI Provider: $AI_PROVIDER_TYPE"
echo "  Decision Mode: $DECISION_MODE"
echo "  Template Used: $TEMPLATE_FILE"
echo ""
echo "Stack outputs:"
$AWS_CMD cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs" --output table

echo ""
echo "Next steps:"
echo "1. Test AI provider connectivity using the validation script"
echo "2. Upload sample trade documents to test the enhanced reconciliation"
echo "3. Monitor CloudWatch logs for AI provider performance"
echo "4. Review the AI Enhanced Deployment Guide for additional configuration options"