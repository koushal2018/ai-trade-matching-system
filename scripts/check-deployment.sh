#!/bin/bash

# Script to check CloudFront deployment status and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}CloudFront Deployment Status${NC}"
echo -e "${BLUE}=====================================${NC}"

# Change to terraform frontend directory
cd "$(dirname "$0")/../terraform/frontend"

# Check if Terraform state exists
if [ ! -f ".terraform/terraform.tfstate" ] && [ ! -f "terraform.tfstate" ]; then
  echo -e "${RED}❌ Terraform not initialized or no state found${NC}"
  echo -e "${YELLOW}Run: terraform init && terraform apply${NC}"
  exit 1
fi

# Get Terraform outputs
echo -e "\n${YELLOW}Fetching deployment information...${NC}\n"

CLOUDFRONT_URL=$(terraform output -raw frontend_url 2>/dev/null || echo "")
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")
S3_BUCKET=$(terraform output -raw frontend_s3_bucket 2>/dev/null || echo "")

if [ -z "$CLOUDFRONT_URL" ]; then
  echo -e "${RED}❌ CloudFront distribution not found${NC}"
  echo -e "${YELLOW}Deploy infrastructure first: terraform apply${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Frontend URL:${NC} ${CLOUDFRONT_URL}"
echo -e "${GREEN}✓ Distribution ID:${NC} ${CLOUDFRONT_ID}"
echo -e "${GREEN}✓ S3 Bucket:${NC} ${S3_BUCKET}"

# Get CloudFront distribution status
echo -e "\n${YELLOW}CloudFront Distribution Status:${NC}"
DISTRIBUTION_STATUS=$(aws cloudfront get-distribution --id "${CLOUDFRONT_ID}" --query 'Distribution.Status' --output text 2>/dev/null || echo "Unknown")

if [ "$DISTRIBUTION_STATUS" == "Deployed" ]; then
  echo -e "${GREEN}✓ Status: Deployed${NC}"
else
  echo -e "${YELLOW}⚠ Status: ${DISTRIBUTION_STATUS}${NC}"
fi

# Check for active invalidations
echo -e "\n${YELLOW}Checking for active invalidations...${NC}"
INVALIDATIONS=$(aws cloudfront list-invalidations --distribution-id "${CLOUDFRONT_ID}" --query 'InvalidationList.Items[?Status==`InProgress`]' --output json 2>/dev/null || echo "[]")
INVALIDATION_COUNT=$(echo "$INVALIDATIONS" | jq length)

if [ "$INVALIDATION_COUNT" -eq 0 ]; then
  echo -e "${GREEN}✓ No active invalidations${NC}"
else
  echo -e "${YELLOW}⚠ ${INVALIDATION_COUNT} invalidation(s) in progress${NC}"
fi

# Check S3 bucket contents
echo -e "\n${YELLOW}S3 Bucket Contents:${NC}"
FILE_COUNT=$(aws s3 ls "s3://${S3_BUCKET}/" --recursive 2>/dev/null | wc -l | tr -d ' ')
if [ "$FILE_COUNT" -gt 0 ]; then
  echo -e "${GREEN}✓ ${FILE_COUNT} files in bucket${NC}"

  # Check if index.html exists
  if aws s3 ls "s3://${S3_BUCKET}/index.html" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ index.html found${NC}"
  else
    echo -e "${RED}❌ index.html not found - deploy may be incomplete${NC}"
  fi
else
  echo -e "${YELLOW}⚠ No files in bucket - frontend not deployed yet${NC}"
fi

# Get last modified date of index.html
if aws s3 ls "s3://${S3_BUCKET}/index.html" >/dev/null 2>&1; then
  LAST_MODIFIED=$(aws s3api head-object --bucket "${S3_BUCKET}" --key "index.html" --query 'LastModified' --output text 2>/dev/null || echo "Unknown")
  echo -e "${GREEN}✓ Last deployment:${NC} ${LAST_MODIFIED}"
fi

# Test if CloudFront is responding
echo -e "\n${YELLOW}Testing CloudFront endpoint...${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${CLOUDFRONT_URL}" 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" == "200" ]; then
  echo -e "${GREEN}✓ CloudFront is responding (HTTP ${HTTP_STATUS})${NC}"
elif [ "$HTTP_STATUS" == "000" ]; then
  echo -e "${RED}❌ Cannot reach CloudFront (network error)${NC}"
else
  echo -e "${YELLOW}⚠ CloudFront returned HTTP ${HTTP_STATUS}${NC}"
fi

# Show production environment config
echo -e "\n${YELLOW}Production Configuration:${NC}"
ENV_FILE="../web-portal/.env.production"
if [ -f "$ENV_FILE" ]; then
  API_URL=$(grep VITE_API_URL "$ENV_FILE" | cut -d'=' -f2)
  if [ "$API_URL" == "https://your-api-endpoint.amazonaws.com" ]; then
    echo -e "${YELLOW}⚠ API URL not configured yet${NC}"
    echo -e "${YELLOW}  Edit: web-portal/.env.production${NC}"
  else
    echo -e "${GREEN}✓ API URL: ${API_URL}${NC}"
  fi
else
  echo -e "${RED}❌ .env.production not found${NC}"
fi

# Summary
echo -e "\n${BLUE}=====================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}=====================================${NC}"

if [ "$DISTRIBUTION_STATUS" == "Deployed" ] && [ "$FILE_COUNT" -gt 0 ] && [ "$HTTP_STATUS" == "200" ]; then
  echo -e "${GREEN}✅ Frontend is deployed and accessible${NC}"
  echo -e "${GREEN}   Access at: ${CLOUDFRONT_URL}${NC}"
else
  echo -e "${YELLOW}⚠ Deployment incomplete or issues detected${NC}"
  echo -e "${YELLOW}   Run: ./deploy-frontend.sh${NC}"
fi

echo ""
