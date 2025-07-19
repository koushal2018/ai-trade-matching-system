# Updating Your CloudFormation Templates in S3

Since you already have the templates in S3 and need to update them with the fixed version, follow these steps:

## Option 1: Update Only the Master Template

If you prefer minimal changes, you can just upload the updated master template:

```bash
# Upload only the fixed master-template.yaml
aws s3 cp ./client-deployment/cloudformation/master-template.yaml s3://your-company-deployment-bucket/trade-reconciliation/master-template.yaml
```

This approach works because we've only modified the master template to properly reference the nested templates that are already in your S3 bucket.

## Option 2: Update All Templates (Recommended)

For completeness, you might want to update all templates to ensure consistency:

```bash
# Upload all CloudFormation templates
aws s3 cp ./client-deployment/cloudformation/ s3://your-company-deployment-bucket/trade-reconciliation/ --recursive
```

Replace `your-company-deployment-bucket` with your actual S3 bucket name.

## Deploying with the Updated Templates

### Using AWS Management Console:

1. Navigate to CloudFormation in the AWS Console
2. Click "Create stack" > "With new resources (standard)"
3. For the template URL, use the same S3 URL as before:
   ```
   https://your-company-deployment-bucket.s3.amazonaws.com/trade-reconciliation/master-template.yaml
   ```
4. Provide the required parameters:
   - **TemplateS3Bucket**: Your S3 bucket name (e.g., `your-company-deployment-bucket`)
   - **TemplateS3Path**: The path in your bucket (e.g., `trade-reconciliation`)
   - Other parameters as needed

### Using AWS CLI:

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

## If You've Already Created a Stack That Failed

If you already have a failed stack, you can either:

1. **Delete the failed stack** and create a new one:
   ```bash
   aws cloudformation delete-stack --stack-name q
   Then create a new stack as shown above.

2. **Update the existing stack**:
   ```bash
   aws cloudformation update-stack \
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

## Verifying the Update

After updating the templates in S3, you can verify they're correctly uploaded:

```bash
aws s3 ls s3://your-company-deployment-bucket/trade-reconciliation/
```

This will list all the templates in your S3 path and confirm the update was successful.
