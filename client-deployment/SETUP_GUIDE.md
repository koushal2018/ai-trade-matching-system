# Trade Reconciliation System - Setup Guide

This guide provides instructions for setting up the Trade Reconciliation System after deployment.

## Prerequisites

Ensure that you have successfully deployed:
1. Core Infrastructure (DynamoDB tables and S3 buckets)
2. API Layer (Lambda functions and API Gateway)
3. Frontend (S3 static website)

## Initial Configuration

### 1. Configure API Endpoint in Frontend

After deploying the frontend, you need to configure it to use your API endpoint:

1. Locate the configuration file in your frontend code:
   ```
   trade-reconciliation-frontend/src/config.js
   ```

2. Update the API endpoint URL:
   ```javascript
   export const API_ENDPOINT = 'https://your-api-endpoint.execute-api.us-west-2.amazonaws.com/v1';
   ```

3. Rebuild and redeploy the frontend:
   ```bash
   cd trade-reconciliation-frontend
   npm run build
   aws s3 sync ./build/ s3://your-frontend-bucket --acl public-read
   ```

### 2. Set Up Sample Data

To test the system with sample data:

1. Create a sample bank trade file (`bank_trades.csv`):
   ```csv
   tradeId,amount,currency,valueDate,counterparty
   T001,10000,USD,2025-07-20,ACME Corp
   T002,15000,EUR,2025-07-21,XYZ Ltd
   T003,5000,GBP,2025-07-22,ABC Inc
   ```

2. Create a sample counterparty trade file (`counterparty_trades.csv`):
   ```csv
   tradeId,amount,currency,valueDate,counterparty
   T001,10000,USD,2025-07-20,ACME Corp
   T002,15000,EUR,2025-07-21,XYZ Ltd
   T004,7500,JPY,2025-07-23,DEF Co
   ```

3. Upload the sample files to the document bucket:
   ```bash
   aws s3 cp bank_trades.csv s3://your-document-bucket/bank/
   aws s3 cp counterparty_trades.csv s3://your-document-bucket/counterparty/
   ```

## User Setup

### 1. Create Admin User

For production environments, it's recommended to set up proper user authentication. This can be done using Amazon Cognito:

1. Create a user pool:
   ```bash
   aws cognito-idp create-user-pool \
     --pool-name TradeReconciliationUserPool \
     --auto-verify-attributes email \
     --schema Name=email,Required=true,Mutable=true \
     --region us-west-2
   ```

2. Create a user pool client:
   ```bash
   aws cognito-idp create-user-pool-client \
     --user-pool-id YOUR_USER_POOL_ID \
     --client-name TradeReconciliationClient \
     --no-generate-secret \
     --region us-west-2
   ```

3. Create an admin user:
   ```bash
   aws cognito-idp admin-create-user \
     --user-pool-id YOUR_USER_POOL_ID \
     --username admin@example.com \
     --user-attributes Name=email,Value=admin@example.com \
     --region us-west-2
   ```

### 2. Configure Access Permissions

Set up appropriate IAM policies for users:

1. Create a policy for read-only users:
   ```bash
   aws iam create-policy \
     --policy-name TradeReconciliationReadOnly \
     --policy-document '{
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": [
             "dynamodb:GetItem",
             "dynamodb:Query",
             "dynamodb:Scan",
             "s3:GetObject",
             "s3:ListBucket"
           ],
           "Resource": [
             "arn:aws:dynamodb:us-west-2:*:table/trade-reconciliation-*",
             "arn:aws:s3:::your-document-bucket/*",
             "arn:aws:s3:::your-report-bucket/*"
           ]
         }
       ]
     }' \
     --region us-west-2
   ```

2. Create a policy for admin users:
   ```bash
   aws iam create-policy \
     --policy-name TradeReconciliationAdmin \
     --policy-document '{
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": [
             "dynamodb:*",
             "s3:*",
             "lambda:InvokeFunction"
           ],
           "Resource": [
             "arn:aws:dynamodb:us-west-2:*:table/trade-reconciliation-*",
             "arn:aws:s3:::your-document-bucket/*",
             "arn:aws:s3:::your-report-bucket/*",
             "arn:aws:lambda:us-west-2:*:function:trade-reconciliation-*"
           ]
         }
       ]
     }' \
     --region us-west-2
   ```

## System Verification

### 1. Verify API Connectivity

Test the API endpoint:

```bash
curl -s https://your-api-endpoint.execute-api.us-west-2.amazonaws.com/v1 | jq
```

You should see a response with the API information.

### 2. Verify Frontend Access

Open the frontend URL in a web browser:

```
http://your-frontend-bucket.s3-website-us-west-2.amazonaws.com
```

Or if using CloudFront:

```
https://your-cloudfront-distribution.cloudfront.net
```

### 3. Verify Data Processing

1. Upload a trade file to the document bucket
2. Check the DynamoDB tables to verify that the data was processed
3. Initiate a reconciliation process through the API
4. Verify that the results are stored in the matches table

## Next Steps

After completing the initial setup:

1. **Configure Monitoring**: Set up CloudWatch alarms for critical metrics
2. **Set Up Logging**: Configure centralized logging for troubleshooting
3. **Implement Backup Strategy**: Enable point-in-time recovery for DynamoDB tables
4. **Schedule Regular Reconciliations**: Set up EventBridge rules to trigger reconciliations on a schedule

## Additional Resources

- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [AWS API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)