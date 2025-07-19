# Trade Reconciliation System - Deployment Instructions

This guide provides step-by-step instructions for deploying the Trade Reconciliation System on AWS. The system consists of three main components:

1. **Core Infrastructure** - DynamoDB tables and S3 buckets
2. **API Layer** - Lambda functions and API Gateway
3. **Frontend** - Static website hosted on S3 (to be deployed separately)

## Prerequisites

Before you begin, ensure you have:

1. AWS CLI installed and configured with appropriate permissions
2. An AWS account with permissions to create:
   - CloudFormation stacks
   - IAM roles and policies
   - DynamoDB tables
   - S3 buckets
   - Lambda functions
   - API Gateway resources

## Deployment Steps

### Step 1: Create a Deployment Bucket

First, create an S3 bucket to store the CloudFormation templates:

```bash
# Replace 'your-company-name' with an appropriate identifier
aws s3 mb s3://your-company-name-trade-reconciliation-deployment --region us-west-2
```

### Step 2: Upload CloudFormation Templates

Upload the CloudFormation templates to the deployment bucket:

```bash
# Upload the templates
aws s3 cp client-deployment/infrastructure/cloudformation/fixed-core-infrastructure.yaml s3://your-company-name-trade-reconciliation-deployment/cloudformation-templates/
aws s3 cp client-deployment/infrastructure/cloudformation/minimal-api-lambda-v2.yaml s3://your-company-name-trade-reconciliation-deployment/cloudformation-templates/
aws s3 cp client-deployment/infrastructure/cloudformation/s3-frontend-hosting.yaml s3://your-company-name-trade-reconciliation-deployment/cloudformation-templates/
```

### Step 3: Deploy Core Infrastructure

Deploy the core infrastructure stack:

```bash
aws cloudformation create-stack \
  --stack-name trade-reconciliation-core \
  --template-url https://your-company-name-trade-reconciliation-deployment.s3.us-west-2.amazonaws.com/cloudformation-templates/fixed-core-infrastructure.yaml \
  --parameters \
      ParameterKey=Environment,ParameterValue=dev \
  --capabilities CAPABILITY_IAM \
  --region us-west-2
```

Wait for the stack creation to complete:

```bash
aws cloudformation wait stack-create-complete --stack-name trade-reconciliation-core --region us-west-2
```

Get the outputs from the core infrastructure stack:

```bash
aws cloudformation describe-stacks --stack-name trade-reconciliation-core --query "Stacks[0].Outputs" --region us-west-2
```

Note down the following values from the output:
- DocumentBucketName
- ReportBucketName
- BankTableName
- CounterpartyTableName
- MatchesTableName

### Step 4: Deploy API Layer

Deploy the API Lambda stack:

```bash
aws cloudformation create-stack \
  --stack-name trade-reconciliation-api \
  --template-url https://your-company-name-trade-reconciliation-deployment.s3.us-west-2.amazonaws.com/cloudformation-templates/minimal-api-lambda-v2.yaml \
  --parameters \
      ParameterKey=Environment,ParameterValue=dev \
      ParameterKey=BankTableName,ParameterValue=[BankTableName from Step 3] \
      ParameterKey=CounterpartyTableName,ParameterValue=[CounterpartyTableName from Step 3] \
      ParameterKey=MatchesTableName,ParameterValue=[MatchesTableName from Step 3] \
      ParameterKey=DocumentBucketName,ParameterValue=[DocumentBucketName from Step 3] \
      ParameterKey=ReportBucketName,ParameterValue=[ReportBucketName from Step 3] \
  --capabilities CAPABILITY_IAM \
  --region us-west-2
```

Wait for the stack creation to complete:

```bash
aws cloudformation wait stack-create-complete --stack-name trade-reconciliation-api --region us-west-2
```

Get the outputs from the API stack:

```bash
aws cloudformation describe-stacks --stack-name trade-reconciliation-api --query "Stacks[0].Outputs" --region us-west-2
```

Note down the API endpoint URL from the output.

### Step 5: Deploy Frontend (S3 Static Website)

Deploy the S3 frontend hosting stack:

```bash
aws cloudformation create-stack \
  --stack-name trade-reconciliation-frontend \
  --template-url https://your-company-name-trade-reconciliation-deployment.s3.us-west-2.amazonaws.com/cloudformation-templates/s3-frontend-hosting.yaml \
  --parameters \
      ParameterKey=Environment,ParameterValue=dev \
      ParameterKey=ApiEndpointUrl,ParameterValue=[API Endpoint URL from Step 4] \
      ParameterKey=CreateCloudFront,ParameterValue=true \
  --region us-west-2
```

Wait for the stack creation to complete:

```bash
aws cloudformation wait stack-create-complete --stack-name trade-reconciliation-frontend --region us-west-2
```

Get the outputs from the frontend stack:

```bash
aws cloudformation describe-stacks --stack-name trade-reconciliation-frontend --query "Stacks[0].Outputs" --region us-west-2
```

Note down the S3 bucket name and website URL from the output.

### Step 6: Build and Deploy Frontend Code

1. Extract the frontend code from the provided ZIP file
2. Update the API endpoint configuration in the frontend code:

   Edit `trade-reconciliation-frontend/src/config.js` (or similar file) to point to your API endpoint:

   ```javascript
   export const API_ENDPOINT = 'https://your-api-endpoint.execute-api.us-west-2.amazonaws.com/v1';
   ```

3. Build the frontend application:

   ```bash
   cd trade-reconciliation-frontend
   npm install
   npm run build
   ```

4. Upload the built frontend to the S3 bucket:

   ```bash
   aws s3 sync ./build/ s3://[WebsiteBucketName from Step 5] --acl public-read
   ```

5. Access your website at the URL provided in the frontend stack outputs.

## Verification

### Test the API

Test the API endpoint to ensure it's working correctly:

```bash
curl -s https://your-api-endpoint.execute-api.us-west-2.amazonaws.com/v1 | jq
```

You should see a response similar to:

```json
{
  "message": "Welcome to Trade Reconciliation API",
  "version": "1.0.0",
  "timestamp": "2025-07-19T17:38:35.296Z",
  "environment": "AWS_Lambda_nodejs18.x"
}
```

### Test the Frontend

Open the website URL in a browser to verify that the frontend is working correctly.

## Troubleshooting

### Common Issues

1. **CloudFormation Stack Creation Fails**:
   - Check the stack events to identify the specific resource that failed
   - Verify that you have the necessary permissions to create all resources
   - Ensure that the S3 bucket names are globally unique

2. **API Returns 5XX Errors**:
   - Check the CloudWatch Logs for the Lambda function
   - Verify that the Lambda function has the correct permissions

3. **Frontend Cannot Connect to API**:
   - Check that the API endpoint URL is correctly configured in the frontend code
   - Verify that CORS is properly configured on the API Gateway

### CloudFormation Stack Deletion

If you need to delete the stacks, use the following commands:

```bash
# Delete the stacks in reverse order
aws cloudformation delete-stack --stack-name trade-reconciliation-frontend --region us-west-2
aws cloudformation delete-stack --stack-name trade-reconciliation-api --region us-west-2
aws cloudformation delete-stack --stack-name trade-reconciliation-core --region us-west-2
```

## Next Steps

After successful deployment, you can:

1. Upload trade data files to the Document S3 bucket
2. Use the API to trigger reconciliation processes
3. View reconciliation results through the frontend interface

## Support

For any issues or questions, please contact your system administrator or refer to the system documentation.