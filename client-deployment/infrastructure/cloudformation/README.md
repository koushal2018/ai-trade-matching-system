# CloudFormation Templates for Trade Reconciliation System

This directory contains the CloudFormation templates for deploying the Trade Reconciliation System.

## Template Overview

### Core Infrastructure

- **fixed-core-infrastructure.yaml**: Creates the core infrastructure components including DynamoDB tables and S3 buckets.

### API Layer

- **minimal-api-lambda-v2.yaml**: Creates a simple API Gateway and Lambda function for the Trade Reconciliation API.
- **fixed-api-lambda.yaml**: More comprehensive API with additional features (includes UsagePlan).
- **fixed-api-lambda-with-root.yaml**: API with root method handler for better URL path handling.
- **standalone-api-lambda.yaml**: Independent API stack that can be deployed separately from the core infrastructure.
- **simplified-api-lambda.yaml**: Simplified version of the API without advanced features.

### Frontend

- **s3-frontend-hosting.yaml**: Creates an S3 bucket configured for static website hosting, with optional CloudFront distribution.
- **frontend-amplify.yaml**: Creates an AWS Amplify app for hosting the frontend from a Git repository.

### Master Templates

- **fixed-master-template.yaml**: Master template that deploys all components (core, API, frontend).
- **simplified-master-template.yaml**: Simplified master template with fewer components.
- **minimal-master-template.yaml**: Minimal master template for basic deployments.
- **super-minimal-template.yaml**: Core infrastructure only template.

## Deployment Order

For a complete deployment, the templates should be deployed in the following order:

1. Core Infrastructure
2. API Layer
3. Frontend

## Template Parameters

### Core Infrastructure Parameters

- **Environment**: Environment name (dev, test, prod)

### API Layer Parameters

- **Environment**: Environment name (dev, test, prod)
- **BankTableName**: Name of the DynamoDB table for bank trades
- **CounterpartyTableName**: Name of the DynamoDB table for counterparty trades
- **MatchesTableName**: Name of the DynamoDB table for match records
- **DocumentBucketName**: Name of the S3 bucket for document storage
- **ReportBucketName**: Name of the S3 bucket for report storage
- **ApiGatewayStageName**: Stage name for API Gateway deployment

### Frontend Parameters

- **Environment**: Environment name (dev, test, prod)
- **ApiEndpointUrl**: URL of the API Gateway endpoint
- **CreateCloudFront**: Whether to create a CloudFront distribution (for S3 hosting)
- **RepositoryUrl**: Git repository URL (for Amplify hosting)
- **RepositoryBranch**: Git repository branch (for Amplify hosting)
- **AccessToken**: Personal access token for the Git repository (for Amplify hosting)

## Best Practices

1. **Validate templates** before deployment using the AWS CloudFormation validate-template command.
2. **Use parameter files** for complex deployments to maintain consistency.
3. **Deploy incrementally** starting with core infrastructure, then API, then frontend.
4. **Use stack outputs** to pass values between stacks.
5. **Enable termination protection** for production stacks.

## Template Customization

To customize the templates for your specific needs:

1. Modify the IAM permissions to match your security requirements
2. Adjust the resource configurations (e.g., DynamoDB capacity, Lambda memory)
3. Add additional resources as needed (e.g., CloudWatch alarms, EventBridge rules)
4. Update the API Gateway configuration for custom domain names or authentication

## Troubleshooting

If you encounter issues with the templates:

1. Check the CloudFormation events for specific error messages
2. Verify that all referenced resources exist and are accessible
3. Ensure that the IAM role has the necessary permissions
4. Check for circular dependencies between resources

For more detailed troubleshooting, refer to the Troubleshooting Guide.