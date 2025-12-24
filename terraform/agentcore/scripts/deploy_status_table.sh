#!/bin/bash

# Script to deploy the Orchestrator Status Tracking DynamoDB table
# This script creates the ai-trade-matching-processing-status table with TTL enabled

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Deploying Orchestrator Status Table"
echo "=========================================="
echo ""

# Change to terraform directory
cd "$TERRAFORM_DIR"

# Initialize terraform if needed
if [ ! -d ".terraform" ]; then
    echo "Initializing Terraform..."
    terraform init
    echo ""
fi

# Validate terraform configuration
echo "Validating Terraform configuration..."
terraform validate
if [ $? -ne 0 ]; then
    echo "ERROR: Terraform validation failed"
    exit 1
fi
echo "✓ Terraform configuration is valid"
echo ""

# Plan the changes
echo "Planning Terraform changes..."
terraform plan \
    -target=aws_dynamodb_table.orchestrator_status \
    -out=tfplan-status-table
echo ""

# Ask for confirmation
read -p "Do you want to apply these changes? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled"
    rm -f tfplan-status-table
    exit 0
fi

# Apply the changes
echo ""
echo "Applying Terraform changes..."
terraform apply tfplan-status-table
echo ""

# Clean up plan file
rm -f tfplan-status-table

# Verify the table was created
echo "Verifying table creation..."
TABLE_NAME="ai-trade-matching-processing-status"
aws dynamodb describe-table --table-name "$TABLE_NAME" --region us-east-1 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Table '$TABLE_NAME' created successfully"
    
    # Check TTL status
    echo ""
    echo "Checking TTL configuration..."
    TTL_STATUS=$(aws dynamodb describe-time-to-live --table-name "$TABLE_NAME" --region us-east-1 --query 'TimeToLiveDescription.TimeToLiveStatus' --output text)
    echo "TTL Status: $TTL_STATUS"
    
    if [ "$TTL_STATUS" == "ENABLED" ]; then
        echo "✓ TTL is enabled on expiresAt attribute"
    else
        echo "⚠ TTL status: $TTL_STATUS (may take a few minutes to enable)"
    fi
else
    echo "ERROR: Failed to verify table creation"
    exit 1
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update IAM permissions by running: terraform apply"
echo "2. Deploy the orchestrator agent with StatusWriter integration"
echo "3. Test status tracking with a sample workflow"
echo ""
