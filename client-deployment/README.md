# Trade Reconciliation System - Client Deployment Guide

This repository contains all the necessary code and instructions to deploy the Trade Reconciliation System on your own AWS account. The system helps financial institutions automatically reconcile trades between internal (bank) records and external (counterparty) records.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Instructions](#deployment-instructions)
4. [Usage Guide](#usage-guide)
5. [File Structure](#file-structure)
6. [Lambda Functions](#lambda-functions)
7. [Troubleshooting](#troubleshooting)

## Architecture Overview

The Trade Reconciliation System is built on AWS serverless technologies and consists of the following components:

- **S3 Buckets**: For storing trade documents and reconciliation reports
- **Lambda Functions**: For processing documents, reconciling trades, and handling API requests
- **DynamoDB Tables**: For storing trade data and reconciliation results
- **API Gateway**: For exposing RESTful APIs to the frontend application

![Architecture Diagram](architecture-diagram.png)

The system workflow is as follows:

1. Users upload trade documents (CSV or Excel files) for both bank and counterparty records
2. The Document Processor Lambda function extracts trade data and stores it in DynamoDB
3. Users initiate a reconciliation process through the API
4. The Reconciliation Engine Lambda function compares bank and counterparty trades
5. Results are stored in DynamoDB and reports are generated in S3
6. Users view reconciliation results through the frontend application

## Prerequisites

Before deploying the system, ensure you have the following:

1. **AWS Account**: You need an AWS account with permissions to create the resources defined in the CloudFormation template
2. **AWS CLI**: Install and configure the AWS CLI on your local machine
   ```bash
   pip install awscli
   aws configure
   ```
3. **Node.js and npm**: For packaging Lambda functions
   ```bash
   # Check if installed
   node --version
   npm --version
   
   # Install if needed (using NVM is recommended)
   # https://github.com/nvm-sh/nvm#install--update-script
   ```

## Deployment Instructions

### Step 1: Clone the Repository

Clone this repository to your local machine:

```bash
git clone <repository-url>
cd trade-reconciliation-system/client-deployment
```

### Step 2: Package Lambda Functions

Navigate to the lambda directory and install dependencies:

```bash
cd lambda
npm install
npm run package
```

This creates a `lambda-package.zip` file containing all necessary code and dependencies.

### Step 3: Deploy with CloudFormation

You can deploy using either the AWS Management Console or AWS CLI.

#### Option 1: AWS Management Console

1. Open the [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation)
2. Click "Create stack" > "With new resources (standard)"
3. Select "Upload a template file" and upload `cloudformation.yaml`
4. Follow the wizard, providing values for parameters as needed
5. Review and click "Create stack"

#### Option 2: AWS CLI

```bash
# Create an S3 bucket for deployment artifacts (if you don't have one already)
aws s3 mb s3://your-deployment-bucket

# Package the CloudFormation template
aws cloudformation package \
    --template-file cloudformation.yaml \
    --s3-bucket your-deployment-bucket \
    --output-template-file packaged-template.yaml

# Deploy the stack
aws cloudformation deploy \
    --template-file packaged-template.yaml \
    --stack-name trade-reconciliation-system \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --parameter-overrides Stage=dev
```

### Step 4: Deploy the Frontend

Follow the instructions in the frontend README to deploy the React application.

The API endpoint URL for the frontend configuration can be found in the CloudFormation stack outputs:

```bash
aws cloudformation describe-stacks \
    --stack-name trade-reconciliation-system \
    --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
    --output text
```

## Usage Guide

### Preparing Trade Documents

1. **Format Requirements**:
   - Supported formats: CSV, Excel (.xlsx, .xls)
   - Required columns: tradeId, amount, currency, valueDate, direction
   - Optional columns: product, trader, rate

2. **File Organization**:
   - Bank files should be uploaded to the 'bank/' prefix in the document bucket
   - Counterparty files should be uploaded to the 'counterparty/' prefix

### Uploading Documents

Documents can be uploaded via:

1. **Direct S3 Upload**: Using the AWS Management Console or AWS CLI
   ```bash
   aws s3 cp your-bank-file.csv s3://your-document-bucket/bank/
   aws s3 cp your-counterparty-file.csv s3://your-document-bucket/counterparty/
   ```

2. **Frontend Application**: Using the document upload interface

### Running Reconciliations

1. **Via Frontend**: Select the documents to reconcile and click "Start Reconciliation"

2. **Via API**: Make a POST request to the API endpoint
   ```bash
   curl -X POST https://your-api-endpoint/api/reconciliations \
       -H "Content-Type: application/json" \
       -d '{"bankDocumentIds": ["bank/file1.csv"], "counterpartyDocumentIds": ["counterparty/file1.csv"]}'
   ```

### Viewing Results

1. **Reconciliation Reports**: Overall statistics and summary
2. **Match Details**: Detailed information about each matched or unmatched trade
3. **Discrepancy Analysis**: Information about fields that don't match between bank and counterparty records

## File Structure

```
client-deployment/
│
├── cloudformation.yaml        # CloudFormation template for AWS resources
├── README.md                  # This file
│
└── lambda/                    # Lambda functions
    ├── package.json           # Node.js package file
    │
    ├── document_processor/    # Document processor Lambda function
    │   └── index.js           # Main function code
    │
    ├── reconciliation_engine/ # Reconciliation engine Lambda function
    │   └── index.js           # Main function code
    │
    └── api_handler/           # API handler Lambda function
        └── index.js           # Main function code
```

## Lambda Functions

### Document Processor

This function is triggered when new documents are uploaded to S3. It processes CSV or Excel files and extracts trade data into DynamoDB tables.

Key features:
- File type detection and appropriate parsing
- Field normalization for consistent trade data
- Batch writing to DynamoDB for performance

### Reconciliation Engine

This function performs the actual trade reconciliation between bank and counterparty records.

Key features:
- Exact matching by trade ID
- Fuzzy matching by other attributes
- Discrepancy analysis
- Report generation

### API Handler

This function serves as the backend for the frontend application, handling API requests.

Key features:
- Document listing and upload
- Reconciliation initiation
- Results retrieval

## Troubleshooting

### Common Issues

1. **Permission Errors**:
   - Ensure your AWS user has sufficient permissions
   - Check IAM role policies in the CloudFormation template

2. **Document Processing Errors**:
   - Verify file format (CSV or Excel)
   - Check required columns are present
   - Review CloudWatch logs for the Document Processor Lambda function

3. **Reconciliation Errors**:
   - Ensure both bank and counterparty documents are processed
   - Check for valid trade IDs
   - Review CloudWatch logs for the Reconciliation Engine Lambda function

4. **API Errors**:
   - Check CORS configuration
   - Verify API Gateway deployment
   - Review CloudWatch logs for the API Handler Lambda function

### Viewing Logs

All Lambda functions log to CloudWatch Logs. To view logs:

1. Open the [AWS CloudWatch Console](https://console.aws.amazon.com/cloudwatch)
2. Navigate to "Log groups"
3. Find the log group for your Lambda function (e.g., `/aws/lambda/trade-reconciliation-document-processor-dev`)
4. Review the log streams for errors and diagnostic information

### Getting Support

If you encounter issues that you cannot resolve using this guide, please contact our support team at support@example.com.

---

© 2025 Trade Reconciliation Team
