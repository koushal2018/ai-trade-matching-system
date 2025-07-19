# Trade Reconciliation System - Step-by-Step Setup Guide

This guide provides detailed instructions for deploying the Trade Reconciliation System in your AWS environment, even if you're not familiar with CloudFormation or AWS deployments.

## Prerequisites

Before beginning the deployment, ensure you have:

1. **AWS Account** with administrator access
2. **AWS Management Console** access
3. **AWS CLI** installed and configured ([Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html))
4. **Git Repository** (optional) for frontend code deployment

## Deployment Steps

### Step 1: Prepare Your Environment

1. **Create a deployment S3 bucket** to store your CloudFormation templates:
   
   ```bash
   aws s3 mb s3://your-company-deployment-bucket --region us-east-1
   ```
   
   Replace `your-company-deployment-bucket` with a globally unique bucket name and `us-east-1` with your preferred region.

2. **Upload the CloudFormation templates** to your S3 bucket:

   ```bash
   aws s3 cp ./client-deployment/infrastructure/cloudformation/ s3://your-company-deployment-bucket/trade-reconciliation/ --recursive
   ```

### Step 2: Deploy via AWS Management Console (Easiest Method)

1. **Sign in to the AWS Management Console** and navigate to the CloudFormation service.

2. **Click "Create stack"** and select "With new resources (standard)".

3. In the "Specify template" section, select **"Amazon S3 URL"** and enter:
   ```
   https://your-company-deployment-bucket.s3.amazonaws.com/trade-reconciliation/master-template.yaml
   ```

4. Click **"Next"** to proceed to stack details.

5. **Enter stack details**:
   - **Stack name**: `trade-reconciliation-system`
   - **Environment**: Choose from `dev`, `test`, or `prod`
   - **BucketNamePrefix**: Enter a unique prefix for your S3 buckets (e.g., `your-company-trade-recon`)
   - **RepositoryUrl**: (Optional) URL to your Git repository with frontend code
   - **RepositoryBranch**: (Optional) Branch to deploy, default is `main`
   - **DomainName**: (Optional) Custom domain if you want to use one
   - **RegionName**: The AWS region you're deploying to (e.g., `us-east-1`)

6. Click **"Next"** to configure stack options.

7. Keep the default settings or adjust as needed, then click **"Next"**.

8. On the review page, **check the acknowledgment** that CloudFormation might create IAM resources, then click **"Create stack"**.

9. **Monitor the stack creation process** in the CloudFormation console. This may take 15-20 minutes to complete.

### Step 3: Deploy Using AWS CLI (Alternative Method)

If you prefer using the command line:

```bash
aws cloudformation create-stack \
  --stack-name trade-reconciliation-system \
  --template-url https://your-company-deployment-bucket.s3.amazonaws.com/trade-reconciliation/master-template.yaml \
  --parameters \
      ParameterKey=Environment,ParameterValue=dev \
      ParameterKey=BucketNamePrefix,ParameterValue=your-company-trade-recon \
      ParameterKey=RepositoryUrl,ParameterValue=https://your-git-repo-url.git \
      ParameterKey=RepositoryBranch,ParameterValue=main \
      ParameterKey=RegionName,ParameterValue=us-east-1 \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

Replace the parameter values with your own configuration.

### Step 4: Verify Your Deployment

Once the stack is successfully created, verify the deployment:

1. **Navigate to the CloudFormation console** and select the `trade-reconciliation-system` stack.

2. Go to the **"Outputs"** tab to find:
   - API Gateway endpoint URL
   - Amplify application URL
   - S3 bucket names
   - DynamoDB table names

3. **Test the API endpoint** by accessing it in a browser or using curl:
   ```bash
   curl https://your-api-gateway-id.execute-api.your-region.amazonaws.com/
   ```

4. **Access the frontend application** using the Amplify URL provided in the outputs.

### Step 5: Configure Frontend Repository (If Using Amplify)

If you're deploying the frontend with AWS Amplify:

1. **Navigate to the AWS Amplify console** and locate your application.

2. If you didn't provide a repository URL during deployment, click on **"Connect repository"** to connect your Git repository.

3. Follow the Amplify wizard to authorize access to your repository and configure build settings.

4. Once connected, Amplify will automatically build and deploy your frontend application.

## Testing the System

After successful deployment, follow these steps to test the system functionality:

### 1. Upload Sample Trade Documents

1. **Access the frontend application** using the Amplify URL.

2. **Log in** using the credentials you created during deployment.

3. **Navigate to "Document Upload"** section.

4. Upload sample bank document and counterparty document PDFs.
   - For testing, create simple PDFs with trade data including:
     - Trade ID
     - Trade date
     - Notional amount
     - Currency
     - Product type

### 2. Verify Document Processing

1. **Wait a few moments** for document processing to complete.

2. **Navigate to "Trades"** section to verify that the trades were extracted from the documents.

3. **Check the DynamoDB tables** directly in the AWS Console to confirm the data was stored correctly:
   - Go to DynamoDB console
   - Select the Bank Trade Data table
   - Verify your trade data appears

### 3. Run Trade Reconciliation

1. **Navigate to "Dashboard"** section.

2. **Click "Run Reconciliation"** to trigger the reconciliation process.

3. **Wait for the process to complete**.

### 4. View Reconciliation Reports

1. **Navigate to "Reports"** section.

2. **Select the generated report** to view the reconciliation results.

3. Verify that the report correctly identifies matches, mismatches, and unmatched trades.

## Troubleshooting

### Common Deployment Issues

1. **Stack Creation Failure**:
   - Check the "Events" tab in CloudFormation for specific error messages
   - Most common issues are related to permissions or naming conflicts
   - If S3 bucket creation fails, try a different bucket name prefix

2. **API Gateway Issues**:
   - If the API returns 403 or 500 errors, check Lambda permissions
   - Verify the API is deployed correctly in the API Gateway console

3. **Lambda Function Errors**:
   - Check CloudWatch Logs for specific error messages
   - Common issues include misconfigured environment variables or permission issues

4. **Amplify Build Failures**:
   - Check the build logs in the Amplify console
   - Ensure your repository contains valid frontend code
   - Verify that environment variables are correctly configured

### Viewing Logs

To view logs for troubleshooting:

1. **Navigate to CloudWatch console**.

2. **Select "Log Groups"**.

3. **Find the log group** for the specific Lambda function:
   - `/aws/lambda/trade-reconciliation-api-handler-dev`
   - `/aws/lambda/trade-reconciliation-document-processor-dev`
   - `/aws/lambda/trade-reconciliation-engine-dev`

4. **Review the log streams** for error messages and stack traces.

## Security Best Practices

1. **Regularly rotate IAM credentials**.

2. **Enable CloudTrail** to monitor API activity.

3. **Review S3 bucket policies** to ensure they're not publicly accessible.

4. **Set up CloudWatch alarms** for suspicious activity.

5. **Update Lambda functions** to patch security vulnerabilities.

## Next Steps

After successful deployment and testing:

1. **Set up monitoring and alerts** for production environments.

2. **Configure backup strategies** for DynamoDB tables.

3. **Implement CI/CD pipelines** for ongoing development.

4. **Document customizations** made to the system for future reference.

## Contact Support

If you encounter issues not addressed in this guide, please contact your administrator or AWS support.

---

## Appendix: Manual Component Deployment

If you need to deploy components individually, refer to the README.md file for detailed instructions.
