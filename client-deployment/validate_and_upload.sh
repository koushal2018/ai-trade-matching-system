#!/bin/bash
# CloudFormation Template Validation & Upload Script
# This script validates a CloudFormation template and uploads it to S3 if valid

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
TEMPLATE_FILE="client-deployment/cloudformation/fixed-master-template.yaml"
S3_BUCKET="trade-reconciliation-system-us-west-2"
S3_KEY="master-template.yaml"
REGION="us-west-2"

# Help function
function show_help {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -t, --template  Template file path (default: $TEMPLATE_FILE)"
  echo "  -b, --bucket    S3 bucket name (default: $S3_BUCKET)"
  echo "  -k, --key       S3 key/path (default: $S3_KEY)"
  echo "  -r, --region    AWS region (default: $REGION)"
  echo "  -h, --help      Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -t|--template)
      TEMPLATE_FILE="$2"
      shift
      shift
      ;;
    -b|--bucket)
      S3_BUCKET="$2"
      shift
      shift
      ;;
    -k|--key)
      S3_KEY="$2"
      shift
      shift
      ;;
    -r|--region)
      REGION="$2"
      shift
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

echo -e "${YELLOW}CloudFormation Template Validation & Upload${NC}"
echo "Template: $TEMPLATE_FILE"
echo "S3 Bucket: $S3_BUCKET"
echo "S3 Key: $S3_KEY"
echo "Region: $REGION"
echo "---------------------------------------"

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo -e "${RED}Error: Template file not found: $TEMPLATE_FILE${NC}"
  exit 1
fi

# Step 1: Validate the template locally
echo -e "${YELLOW}Step 1: Validating template...${NC}"
VALIDATION_OUTPUT=$(aws cloudformation validate-template --template-body file://$TEMPLATE_FILE 2>&1)
VALIDATION_STATUS=$?

if [ $VALIDATION_STATUS -eq 0 ]; then
  echo -e "${GREEN}Validation successful!${NC}"
  
  # Print template parameters
  echo "Template Parameters:"
  echo "$VALIDATION_OUTPUT" | grep -A 1 "ParameterKey"
  
else
  echo -e "${RED}Validation failed:${NC}"
  echo "$VALIDATION_OUTPUT"
  exit 1
fi

# Step 2: Upload the template to S3
echo -e "\n${YELLOW}Step 2: Uploading template to S3...${NC}"
UPLOAD_OUTPUT=$(aws s3 cp $TEMPLATE_FILE s3://$S3_BUCKET/$S3_KEY 2>&1)
UPLOAD_STATUS=$?

if [ $UPLOAD_STATUS -eq 0 ]; then
  echo -e "${GREEN}Upload successful!${NC}"
  TEMPLATE_URL="https://$S3_BUCKET.s3.$REGION.amazonaws.com/$S3_KEY"
  echo "Template URL: $TEMPLATE_URL"
else
  echo -e "${RED}Upload failed:${NC}"
  echo "$UPLOAD_OUTPUT"
  exit 1
fi

# Step 3: Provide deployment command
echo -e "\n${YELLOW}Step 3: Deploy the template${NC}"
echo "You can now deploy the template using the AWS CloudFormation Console or CLI:"
echo -e "${GREEN}AWS CLI Command:${NC}"
echo "aws cloudformation create-stack \\"
echo "  --stack-name trade-reconciliation-system \\"
echo "  --template-url $TEMPLATE_URL \\"
echo "  --parameters \\"
echo "      ParameterKey=TemplateS3Bucket,ParameterValue=$S3_BUCKET \\"
echo "      ParameterKey=TemplateS3Path,ParameterValue=\"\" \\"
echo "      ParameterKey=EnvironmentName,ParameterValue=dev \\"
echo "      ParameterKey=ApiStageName,ParameterValue=api \\"
echo "      ParameterKey=EnableAuth,ParameterValue=false \\"
echo "  --capabilities CAPABILITY_IAM \\"
echo "  --region $REGION"

echo -e "\n${GREEN}Done! The template is ready for deployment.${NC}"
