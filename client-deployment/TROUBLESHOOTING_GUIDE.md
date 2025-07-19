# Trade Reconciliation System - Troubleshooting Guide

This guide provides solutions for common issues that may arise during the deployment and operation of the Trade Reconciliation System.

## Deployment Issues

### CloudFormation Stack Creation Failures

#### Issue: "TemplateURL must be a supported URL"

**Cause**: The S3 URL for the nested templates is incorrect or inaccessible.

**Solution**:
1. Verify that all templates are uploaded to the correct S3 bucket and path
2. Ensure the S3 bucket name and path parameters are correct
3. Check that the S3 bucket is in the same region as the CloudFormation stack
4. Verify that the IAM user/role has permission to access the S3 bucket

#### Issue: "Resource creation failed" for S3 buckets

**Cause**: S3 bucket names must be globally unique across all AWS accounts.

**Solution**:
1. Use a more unique bucket name by adding a suffix like your account ID
2. For the core infrastructure template, remove hardcoded bucket names and let CloudFormation generate names
3. Check if the bucket already exists from a previous deployment attempt

#### Issue: "Resource creation failed" for Lambda functions

**Cause**: Issues with Lambda function code or permissions.

**Solution**:
1. Check the CloudWatch Logs for the Lambda function
2. Verify that the IAM role has the necessary permissions
3. Ensure the Lambda function code is valid and doesn't contain syntax errors
4. Check that the environment variables are correctly set

### API Gateway Issues

#### Issue: "Missing Authentication Token" error when accessing API

**Cause**: Incorrect API path or API Gateway configuration.

**Solution**:
1. Ensure you're using the correct API endpoint URL
2. Verify that the API Gateway deployment was successful
3. Check that the API Gateway stage is correctly configured
4. Ensure the Lambda function permissions allow API Gateway to invoke the function

#### Issue: CORS errors when accessing API from frontend

**Cause**: Missing or incorrect CORS configuration.

**Solution**:
1. Add appropriate CORS headers to API Gateway responses
2. Ensure the API Gateway has OPTIONS methods configured for CORS preflight requests
3. Verify that the Lambda function returns the correct CORS headers

## Runtime Issues

### Data Processing Issues

#### Issue: Files uploaded to S3 are not processed

**Cause**: S3 event notifications or Lambda function issues.

**Solution**:
1. Check that S3 event notifications are correctly configured
2. Verify that the Lambda function has permission to be invoked by S3
3. Check CloudWatch Logs for the Lambda function for errors
4. Ensure the file format matches what the Lambda function expects

#### Issue: DynamoDB operations failing

**Cause**: Permission issues or incorrect table configuration.

**Solution**:
1. Verify that the Lambda functions have the correct IAM permissions for DynamoDB
2. Check that the DynamoDB table names are correct in the Lambda environment variables
3. Ensure the DynamoDB tables have the expected schema (key attributes, indexes)

### Frontend Issues

#### Issue: Frontend cannot connect to API

**Cause**: API endpoint configuration or CORS issues.

**Solution**:
1. Check that the API endpoint URL is correctly configured in the frontend code
2. Verify that the API Gateway CORS configuration allows requests from the frontend origin
3. Ensure the frontend is making requests to the correct API paths

#### Issue: Frontend shows blank page or JavaScript errors

**Cause**: Build or deployment issues.

**Solution**:
1. Check the browser console for JavaScript errors
2. Verify that all frontend files were correctly uploaded to the S3 bucket
3. Ensure the frontend build process completed successfully
4. Check that the S3 bucket is configured for static website hosting

## Monitoring and Debugging

### CloudWatch Logs

To view logs for Lambda functions:

```bash
aws logs get-log-events \
  --log-group-name /aws/lambda/trade-reconciliation-api-handler-v2-dev \
  --log-stream-name [LOG_STREAM_NAME]
```

### CloudFormation Stack Events

To view events for a CloudFormation stack:

```bash
aws cloudformation describe-stack-events \
  --stack-name trade-reconciliation-api \
  --region us-west-2
```

### API Gateway Testing

To test the API directly:

```bash
# Test the root endpoint
curl -s https://your-api-endpoint.execute-api.us-west-2.amazonaws.com/v1

# Test with verbose output for debugging
curl -v https://your-api-endpoint.execute-api.us-west-2.amazonaws.com/v1
```

## Recovery Procedures

### Rolling Back a Deployment

If you need to roll back to a previous version:

```bash
# Delete the problematic stack
aws cloudformation delete-stack --stack-name trade-reconciliation-api --region us-west-2

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name trade-reconciliation-api --region us-west-2

# Redeploy using a previous template version
aws cloudformation create-stack \
  --stack-name trade-reconciliation-api \
  --template-url https://your-company-name-trade-reconciliation-deployment.s3.us-west-2.amazonaws.com/cloudformation-templates/previous-version/minimal-api-lambda-v2.yaml \
  --parameters [...] \
  --capabilities CAPABILITY_IAM \
  --region us-west-2
```

### Data Recovery

If you need to recover data:

1. S3 buckets have versioning enabled, so you can restore previous versions of objects
2. DynamoDB tables can be restored from backups if point-in-time recovery was enabled

## Contact Support

If you continue to experience issues after trying these troubleshooting steps, please contact your system administrator or AWS support.