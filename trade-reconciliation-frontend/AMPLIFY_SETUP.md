# AWS Amplify Setup Guide

This guide provides step-by-step instructions for setting up AWS Amplify for the Trade Reconciliation Frontend.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured locally
- Node.js and npm installed
- Amplify CLI installed (`npm install -g @aws-amplify/cli`)

## Step 1: Initialize Amplify

```bash
cd trade-reconciliation-frontend
amplify init
```

Follow the prompts:
- Enter a name for the project (e.g., tradeReconciliationFrontend)
- Choose your default editor
- Choose JavaScript as the type of app you're building
- Choose React as the framework
- Choose TypeScript as the source directory path
- Choose build as the distribution directory path
- Choose npm as the build command
- Choose npm start as the start command
- Choose AWS profile to use

## Step 2: Add Authentication

```bash
amplify add auth
```

Follow the prompts:
- Choose the default configuration with social provider (or customize as needed)
- Select the sign-in method (Username, Email, Phone Number, etc.)
- Configure advanced settings as needed

## Step 3: Add Storage for Document Upload

```bash
amplify add storage
```

Follow the prompts:
- Choose Content (Images, audio, video, etc.)
- Provide a resource name (e.g., tradedocuments)
- Provide a bucket name (or use the default)
- Choose Auth users only for who has access
- Choose read/write for the authenticated user access
- Configure advanced settings as needed

## Step 4: Add API for Backend Connectivity

```bash
amplify add api
```

Follow the prompts:
- Choose REST as the API service
- Provide an API name (e.g., tradeApi)
- Provide a path (e.g., /trades)
- Choose Create a new Lambda function
- Provide a function name (e.g., tradeFunction)
- Choose NodeJS as the runtime
- Choose Hello World as the template
- Configure advanced settings as needed

## Step 5: Configure Lambda Function

Edit the Lambda function code to connect to your backend services:

```bash
amplify function edit tradeFunction
```

Update the function code to interact with DynamoDB tables and implement the necessary API endpoints.

## Step 6: Deploy Amplify Resources

```bash
amplify push
```

This will provision all the configured resources in your AWS account.

## Step 7: Update aws-exports.ts

After deployment, Amplify will generate an `aws-exports.js` file. Copy the contents to your `aws-exports.ts` file.

## Step 8: Configure Amplify in Your React App

Make sure your `App.tsx` has the proper Amplify configuration:

```typescript
import { Amplify } from 'aws-amplify';
import awsconfig from './aws-exports';

Amplify.configure(awsconfig);
```

## Step 9: Set Up Continuous Deployment

1. Push your code to a Git repository
2. Go to the AWS Amplify Console
3. Choose "Connect app"
4. Select your repository provider and repository
5. Configure build settings
6. Deploy the app

## Step 10: Configure Environment Variables

In the Amplify Console:
1. Go to App settings > Environment variables
2. Add any necessary environment variables
3. Redeploy the application

## Troubleshooting

- **Authentication Issues**: Check Cognito User Pool settings
- **API Connection Issues**: Verify API Gateway configuration and Lambda function permissions
- **Storage Issues**: Check S3 bucket permissions and CORS configuration
- **Build Failures**: Review build logs in the Amplify Console

## Additional Resources

- [AWS Amplify Documentation](https://docs.amplify.aws/)
- [AWS Amplify Framework](https://aws.amazon.com/amplify/)
- [AWS Amplify CLI](https://github.com/aws-amplify/amplify-cli)
- [AWS Amplify JS Library](https://github.com/aws-amplify/amplify-js)