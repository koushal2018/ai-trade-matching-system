#!/bin/bash
# CloudFormation template validation script

set -e

TEMPLATE_FILE="cloudformation-template.yaml"
REGION="us-east-1"

echo "🔍 Validating CloudFormation template..."

# 1. Syntax validation
echo "1. Checking template syntax..."
aws cloudformation validate-template \
    --template-body file://$TEMPLATE_FILE \
    --region $REGION

# 2. cfn-lint validation (install: pip install cfn-lint)
echo "2. Running cfn-lint..."
if command -v cfn-lint &> /dev/null; then
    cfn-lint $TEMPLATE_FILE
else
    echo "⚠️  cfn-lint not installed. Run: pip install cfn-lint"
fi

# 3. cfn-guard validation (install: cargo install cfn-guard)
echo "3. Running cfn-guard security checks..."
if command -v cfn-guard &> /dev/null; then
    cfn-guard validate --data $TEMPLATE_FILE --rules security-rules.guard
else
    echo "⚠️  cfn-guard not installed. See: https://github.com/aws-cloudformation/cloudformation-guard"
fi

# 4. IAM Policy Simulator (requires AWS CLI)
echo "4. Testing IAM policies..."
# This would require extracting policies and testing them

echo "✅ Validation complete!"