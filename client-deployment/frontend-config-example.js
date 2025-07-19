/**
 * Trade Reconciliation Frontend Configuration Example
 * 
 * This file shows how to configure the frontend to connect to the AWS backend services.
 * Copy this file to your React application's src directory and modify the values as needed.
 */

// Replace these values with the outputs from your CloudFormation stack
const config = {
  // API Gateway endpoint URL from CloudFormation output
  apiEndpoint: 'https://your-api-id.execute-api.your-region.amazonaws.com/prod',
  
  // Amazon Cognito User Pool configuration (if you add authentication)
  cognito: {
    userPoolId: 'your-region_yourUserPoolId',
    userPoolWebClientId: 'your-client-id',
    region: 'your-region',
  },
  
  // S3 bucket names from CloudFormation output
  documentBucket: 'trade-reconciliation-documents',
  reportBucket: 'trade-reconciliation-reports',
  
  // Default pagination settings
  pagination: {
    defaultPageSize: 10,
    maxPageSize: 50,
  },
  
  // Feature flags
  features: {
    enableDocumentUpload: true,
    enableReconciliation: true,
    enableReports: true,
    enableMultipleDocumentSelect: true,
  }
};

export default config;

/**
 * How to use this configuration:
 * 
 * 1. Copy this file to your React app's src directory
 * 2. Import it in your API service or components:
 *    import config from './config';
 * 
 * 3. Use the configuration values:
 *    fetch(`${config.apiEndpoint}/api/documents`)
 * 
 * 4. Update the values with the actual outputs from your CloudFormation stack
 */
