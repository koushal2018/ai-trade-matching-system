#!/bin/bash

# Backend Deployment Script for ECS Fargate
# This script builds and deploys the FastAPI backend to ECS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/../terraform/frontend"
BACKEND_DIR="${SCRIPT_DIR}/../web-portal-api"

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Backend Deployment Script${NC}"
echo -e "${GREEN}=====================================${NC}"

# Check if required tools are installed
command -v aws >/dev/null 2>&1 || { echo -e "${RED}AWS CLI is required but not installed. Aborting.${NC}" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed. Aborting.${NC}" >&2; exit 1; }

# Get ECR repository from Terraform outputs
echo -e "\n${YELLOW}Getting deployment targets from Terraform...${NC}"
cd "${TERRAFORM_DIR}"

ECR_REPO=$(terraform output -raw ecr_repository_url 2>/dev/null)
AWS_REGION=$(terraform output -json | jq -r '.aws_region.value // "us-east-1"')

if [ -z "$ECR_REPO" ]; then
  echo -e "${RED}Error: Could not get ECR repository. Make sure infrastructure is deployed.${NC}"
  echo -e "${YELLOW}Run: cd terraform/frontend && terraform apply${NC}"
  exit 1
fi

echo -e "${GREEN}✓ ECR Repository: ${ECR_REPO}${NC}"
echo -e "${GREEN}✓ AWS Region: ${AWS_REGION}${NC}"

# Login to ECR
echo -e "\n${YELLOW}Logging in to ECR...${NC}"
aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${ECR_REPO}"

# Build Docker image
echo -e "\n${YELLOW}Building Docker image...${NC}"
cd "${BACKEND_DIR}"

docker build -t trade-matching-backend:latest .

echo -e "${GREEN}✓ Docker image built successfully${NC}"

# Tag image
echo -e "\n${YELLOW}Tagging image for ECR...${NC}"
docker tag trade-matching-backend:latest "${ECR_REPO}:latest"

# Push to ECR
echo -e "\n${YELLOW}Pushing image to ECR...${NC}"
docker push "${ECR_REPO}:latest"

echo -e "${GREEN}✓ Image pushed to ECR${NC}"

# Update ECS service to use new image
echo -e "\n${YELLOW}Updating ECS service...${NC}"
SERVICE_NAME="trade-matching-system-backend-service"
CLUSTER_NAME="trade-matching-system-backend-cluster"

# Force new deployment
aws ecs update-service \
  --cluster "${CLUSTER_NAME}" \
  --service "${SERVICE_NAME}" \
  --force-new-deployment \
  --region "${AWS_REGION}" \
  >/dev/null

echo -e "${GREEN}✓ ECS service update initiated${NC}"

# Wait for service to stabilize
echo -e "\n${YELLOW}Waiting for service to stabilize (this may take a few minutes)...${NC}"
aws ecs wait services-stable \
  --cluster "${CLUSTER_NAME}" \
  --services "${SERVICE_NAME}" \
  --region "${AWS_REGION}" || true

# Get backend URL
cd "${TERRAFORM_DIR}"
BACKEND_URL=$(terraform output -raw backend_url 2>/dev/null)

echo -e "\n${GREEN}=====================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Backend URL: ${BACKEND_URL}${NC}"
echo -e "${YELLOW}Note: It may take 1-2 minutes for the service to be fully available${NC}"

# Test health endpoint
echo -e "\n${YELLOW}Testing health endpoint...${NC}"
sleep 10
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/health" 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" == "200" ]; then
  echo -e "${GREEN}✓ Backend is healthy and responding${NC}"
else
  echo -e "${YELLOW}⚠ Backend returned HTTP ${HTTP_STATUS} (may still be starting up)${NC}"
fi
