#!/bin/bash

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

# Set environment variables
STACK_NAME="trade-reconciliation-system"
S3_BUCKET="trade-reconciliation-system-us-west-2"  # Verified correct bucket name for us-west-2 region
S3_PREFIX="cloudformation-templates"
REGION="us-west-2"  # Replace with your preferred region

# Use AWS CLI command
AWS_CMD="aws"

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
$AWS_CMD s3 cp ./client-deployment/infrastructure/cloudformation/ s3://$S3_BUCKET/$S3_PREFIX/ --recursive

# Verify all templates were uploaded
echo "Verifying template uploads..."
TEMPLATES=("master-template.yaml" "core-infrastructure.yaml" "api-lambda.yaml" "frontend-amplify.yaml")
for template in "${TEMPLATES[@]}"; do
  if ! $AWS_CMD s3api head-object --bucket $S3_BUCKET --key $S3_PREFIX/$template &>/dev/null; then
    echo "Error: Template $template was not uploaded to S3."
    exit 1
  fi
done

# Validate all templates
echo "Validating CloudFormation templates..."
for template in "${TEMPLATES[@]}"; do
  echo "Validating $template..."
  echo "Template URL: https://$S3_BUCKET.s3.$REGION.amazonaws.com/$S3_PREFIX/$template"
  $AWS_CMD cloudformation validate-template \
    --template-url https://$S3_BUCKET.s3.$REGION.amazonaws.com/$S3_PREFIX/$template
  
  if [ $? -ne 0 ]; then
    echo "Error validating $template. Exiting."
    exit 1
  fi
done

echo "All templates validated successfully."

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
  echo "Deploying new CloudFormation stack..."
  $AWS_CMD cloudformation create-stack \
    --stack-name $STACK_NAME \
    --template-url https://$S3_BUCKET.s3.$REGION.amazonaws.com/$S3_PREFIX/master-template.yaml \
    --parameters \
        ParameterKey=S3BucketForTemplates,ParameterValue=$S3_BUCKET \
        ParameterKey=S3PrefixForTemplates,ParameterValue=$S3_PREFIX \
        ParameterKey=Environment,ParameterValue=dev \
        ParameterKey=ApiGatewayStageName,ParameterValue=api \
        ParameterKey=CreateCustomCFNS3NotificationFunction,ParameterValue=false \
        ParameterKey=RepositoryUrl,ParameterValue=https://github.com/username/trade-reconciliation-frontend.git \
        ParameterKey=RepositoryBranch,ParameterValue=main \
        ParameterKey=AccessToken,ParameterValue="" \
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
  echo "Updating existing CloudFormation stack..."
  $AWS_CMD cloudformation update-stack \
    --stack-name $STACK_NAME \
    --template-url https://$S3_BUCKET.s3.$REGION.amazonaws.com/$S3_PREFIX/master-template.yaml \
    --parameters \
        ParameterKey=S3BucketForTemplates,ParameterValue=$S3_BUCKET \
        ParameterKey=S3PrefixForTemplates,ParameterValue=$S3_PREFIX \
        ParameterKey=Environment,ParameterValue=dev \
        ParameterKey=ApiGatewayStageName,ParameterValue=api \
        ParameterKey=CreateCustomCFNS3NotificationFunction,ParameterValue=false \
        ParameterKey=RepositoryUrl,ParameterValue=https://github.com/username/trade-reconciliation-frontend.git \
        ParameterKey=RepositoryBranch,ParameterValue=main \
        ParameterKey=AccessToken,ParameterValue="" \
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

echo "Deployment process completed. Check the AWS CloudFormation console for stack details."
echo "Stack outputs:"
$AWS_CMD cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs" --output table