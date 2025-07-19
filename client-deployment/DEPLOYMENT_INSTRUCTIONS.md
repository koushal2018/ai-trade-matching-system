# Trade Reconciliation System - Fixed Deployment Instructions

This guide addresses the "TemplateURL must be a supported URL" error you encountered.

## The Issue

The error occurred because the CloudFormation master template was using relative file paths (`./core-infrastructure.yaml`) for nested stack templates, but CloudFormation requires absolute S3 URLs.

## Solution Steps

1. **Upload all templates to an S3 bucket** (if not already done):

   ```bash
   # Create a deployment bucket if needed (replace with your bucket name)
   aws s3 mb s3://your-company-deployment-bucket --region us-west-2
   
   # Upload all CloudFormation templates
   aws s3 cp ./client-deployment/cloudformation/ s3://your-company-deployment-bucket/trade-reconciliation/ --recursive
   ```

2. **Deploy the updated master template** using one of these methods:

### Method 1: AWS Management Console

1. Sign in to the AWS Management Console and navigate to CloudFormation.
2. Click "Create stack" > "With new resources (standard)".
3. Select "Amazon S3 URL" and enter the URL to the master template in your S3 bucket:
   ```
   https://your-company-deployment-bucket.s3.amazonaws.com/trade-reconciliation/master-template.yaml
   ```
4. Click "Next" and provide these parameters:
   - **Stack name**: `trade-reconciliation-system`
   - **TemplateS3Bucket**: `your-company-deployment-bucket` (the bucket you uploaded templates to)
   - **TemplateS3Path**: `trade-reconciliation` (the folder path in your bucket)
   - **Environment**: Choose from `dev`, `test`, or `prod`
   - Fill in any other required parameters
5. Click "Next" to configure stack options.
6. Review settings, check the IAM capabilities acknowledgment, then click "Create stack".

### Method 2: AWS CLI

```bash
aws cloudformation create-stack \
  --stack-name trade-reconciliation-system \
  --template-url https://your-company-deployment-bucket.s3.amazonaws.com/trade-reconciliation/master-template.yaml \
  --parameters \
      ParameterKey=TemplateS3Bucket,ParameterValue=your-company-deployment-bucket \
      ParameterKey=TemplateS3Path,ParameterValue=trade-reconciliation \
      ParameterKey=EnvironmentName,ParameterValue=dev \
      ParameterKey=ApiStageName,ParameterValue=api \
      ParameterKey=EnableAuth,ParameterValue=false \
  --capabilities CAPABILITY_IAM \
  --region us-west-2
```

## Verification

1. Monitor the stack creation in the CloudFormation console.
2. If successful, the "CoreInfrastructureStack" nested stack should create without the URL error.
3. You can check the "Outputs" tab of the stack to get important resources like API endpoints, bucket names, etc.

## Troubleshooting

If you still encounter issues:

1. **Verify S3 bucket permissions**: Ensure the CloudFormation service has read access to your S3 bucket.
2. **Check S3 URLs**: Make sure the bucket name and path are correct in the parameters.
3. **Region consistency**: Ensure you're deploying in the same region as your S3 bucket.
4. **Object versioning**: If you updated templates in S3, the bucket might be serving cached versions. Try adding a version identifier to the S3 key path.

For any persistent issues, check CloudFormation events for specific error messages.
