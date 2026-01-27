#!/bin/bash

# Frontend Deployment Script for CloudFront
# This script builds and deploys the React frontend to S3 and invalidates CloudFront cache

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/../terraform/frontend"
WEB_PORTAL_DIR="${SCRIPT_DIR}/../web-portal"

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Frontend Deployment Script${NC}"
echo -e "${GREEN}Environment: ${ENVIRONMENT}${NC}"
echo -e "${GREEN}=====================================${NC}"

# Check if required tools are installed
command -v aws >/dev/null 2>&1 || { echo -e "${RED}AWS CLI is required but not installed. Aborting.${NC}" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo -e "${RED}jq is required but not installed. Aborting.${NC}" >&2; exit 1; }

# Get S3 bucket and CloudFront distribution from Terraform outputs
echo -e "\n${YELLOW}Getting deployment targets from Terraform...${NC}"
cd "${TERRAFORM_DIR}"

S3_BUCKET=$(terraform output -raw frontend_s3_bucket 2>/dev/null)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null)
CLOUDFRONT_URL=$(terraform output -raw frontend_url 2>/dev/null)

if [ -z "$S3_BUCKET" ] || [ -z "$CLOUDFRONT_ID" ]; then
  echo -e "${RED}Error: Could not get Terraform outputs. Make sure infrastructure is deployed.${NC}"
  echo -e "${YELLOW}Run: cd terraform && terraform apply${NC}"
  exit 1
fi

echo -e "${GREEN}✓ S3 Bucket: ${S3_BUCKET}${NC}"
echo -e "${GREEN}✓ CloudFront Distribution: ${CLOUDFRONT_ID}${NC}"
echo -e "${GREEN}✓ Frontend URL: ${CLOUDFRONT_URL}${NC}"

# Build the frontend
echo -e "\n${YELLOW}Building frontend...${NC}"
cd "${WEB_PORTAL_DIR}"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo -e "${YELLOW}Installing dependencies...${NC}"
  npm install
fi

# Build the application
echo -e "${YELLOW}Running production build...${NC}"
npm run build

if [ ! -d "dist" ]; then
  echo -e "${RED}Error: Build directory 'dist' not found${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Build completed successfully${NC}"

# Upload to S3
echo -e "\n${YELLOW}Uploading files to S3...${NC}"

# Sync dist directory to S3
aws s3 sync dist/ "s3://${S3_BUCKET}/" \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html" \
  --exclude "*.map"

# Upload index.html with no-cache to ensure SPA routing works
aws s3 cp dist/index.html "s3://${S3_BUCKET}/index.html" \
  --cache-control "public, max-age=0, must-revalidate" \
  --content-type "text/html"

echo -e "${GREEN}✓ Files uploaded to S3${NC}"

# Invalidate CloudFront cache
echo -e "\n${YELLOW}Invalidating CloudFront cache...${NC}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
  --distribution-id "${CLOUDFRONT_ID}" \
  --paths "/*" \
  --query 'Invalidation.Id' \
  --output text)

echo -e "${GREEN}✓ CloudFront invalidation created: ${INVALIDATION_ID}${NC}"
echo -e "${YELLOW}  Waiting for invalidation to complete (this may take a few minutes)...${NC}"

# Wait for invalidation to complete (optional - comment out if you don't want to wait)
aws cloudfront wait invalidation-completed \
  --distribution-id "${CLOUDFRONT_ID}" \
  --id "${INVALIDATION_ID}" || true

echo -e "\n${GREEN}=====================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Frontend URL: ${CLOUDFRONT_URL}${NC}"
echo -e "${YELLOW}Note: CloudFront propagation may take 5-10 minutes${NC}"
