# Trade Reconciliation System - Deployment Package

This package contains all the necessary files and instructions for deploying the Trade Reconciliation System on AWS.

## Directory Structure

- **cloudformation.yaml**: Main CloudFormation template (legacy)
- **infrastructure/**: Contains infrastructure-as-code files
  - **cloudformation/**: CloudFormation templates for deploying the system
- **lambda/**: Contains Lambda function code
- **deploy-frontend.sh**: Script for deploying the frontend
- **validate_and_upload.sh**: Script for validating and uploading CloudFormation templates

## Documentation

- **UPDATED_DEPLOYMENT_INSTRUCTIONS.md**: Step-by-step instructions for deploying the system
- **API_DOCUMENTATION.md**: Documentation for the API endpoints
- **SETUP_GUIDE.md**: Guide for setting up the system after deployment
- **TROUBLESHOOTING_GUIDE.md**: Solutions for common issues
- **USER_GUIDE.md**: Guide for using the system
- **VALIDATE_CLOUDFORMATION.md**: Instructions for validating CloudFormation templates

## Deployment Overview

The Trade Reconciliation System consists of three main components:

1. **Core Infrastructure**: DynamoDB tables and S3 buckets
2. **API Layer**: Lambda functions and API Gateway
3. **Frontend**: Static website hosted on S3

These components can be deployed together using the master template or separately using individual templates.

## Quick Start

For a quick deployment, follow these steps:

1. Create an S3 bucket for CloudFormation templates:
   ```bash
   aws s3 mb s3://your-company-name-trade-reconciliation-deployment --region us-west-2
   ```

2. Upload the CloudFormation templates:
   ```bash
   ./validate_and_upload.sh \
     --template infrastructure/cloudformation/fixed-core-infrastructure.yaml \
     --bucket your-company-name-trade-reconciliation-deployment \
     --key cloudformation-templates/fixed-core-infrastructure.yaml \
     --region us-west-2
   ```

3. Deploy the core infrastructure:
   ```bash
   aws cloudformation create-stack \
     --stack-name trade-reconciliation-core \
     --template-url https://your-company-name-trade-reconciliation-deployment.s3.us-west-2.amazonaws.com/cloudformation-templates/fixed-core-infrastructure.yaml \
     --parameters ParameterKey=Environment,ParameterValue=dev \
     --capabilities CAPABILITY_IAM \
     --region us-west-2
   ```

4. Continue with the API and frontend deployment as described in the deployment instructions.

## Prerequisites

- AWS CLI installed and configured
- AWS account with appropriate permissions
- Basic knowledge of AWS services (CloudFormation, Lambda, API Gateway, S3, DynamoDB)

## Support

For any issues or questions, please refer to the troubleshooting guide or contact your system administrator.

## License

This software is proprietary and confidential. Unauthorized copying, transfer, or use is strictly prohibited.

## Version History

- **1.0.0**: Initial release
- **1.1.0**: Added S3 static website hosting option for frontend
- **1.2.0**: Fixed CloudFormation template issues and improved documentation