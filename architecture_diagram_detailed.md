# Trade Reconciliation System - AWS Architecture

## Components

### Frontend
- **AWS Amplify**
  - Hosts the React.js frontend application
  - Provides CI/CD pipeline for automatic deployments
  - Serves static assets through CloudFront CDN
  - Environment variables configured for backend connectivity

### API Layer
- **Amazon API Gateway**
  - REST API endpoints for the application
  - Routes requests to appropriate Lambda functions
  - Handles authentication and authorization
  - Implements CORS for frontend-backend communication

### Backend Processing
- **AWS Lambda**
  - Hosts the Flask API application
  - Processes API requests from the frontend
  - Interacts with DynamoDB for data storage
  - Triggers document processing workflows
  - Implements reconciliation logic

### Data Storage
- **Amazon DynamoDB**
  - **BankTradeData**: Stores trade data from bank sources - arn:aws:dynamodb:us-east-1:401552979575:table/BankTradeData
  - **CounterpartyTradeData**: Stores trade data from counterparty sources - arn:aws:dynamodb:us-east-1:401552979575:table/CounterpartyTradeData
  - **TradeMatches**: Stores match data between bank and counterparty trades - arn:aws:dynamodb:us-east-1:401552979575:table/TradeMatches
  - On-demand capacity for cost optimization

- **Amazon S3**
  - Single bucket: **fab-otc-reconciliation-deployment**
  - **BANK/** folder: Stores uploaded bank trade documents - s3://fab-otc-reconciliation-deployment/BANK/
  - **COUNTERPARTY/** folder: Stores uploaded counterparty trade documents - s3://fab-otc-reconciliation-deployment/COUNTERPARTY/
  - Lifecycle policies for cost optimization 

### AI Document Processing
- **AWS Lambda (Document Processor)** - arn:aws:lambda:us-east-1:401552979575:function:trade-pdf-processor
  - Triggered when documents are uploaded to S3
  - Calls AI vision services for document processing
  - Extracts structured data from documents
  - Stores extracted data in appropriate DynamoDB tables



### Monitoring and Logging
- **Amazon CloudWatch**
  - Logs for all Lambda functions
  - Metrics for API Gateway and Lambda
  - Alarms for error conditions
  - Dashboards for system health

## Data Flow

1. **Document Upload Flow**
   - User uploads document through frontend
   - Frontend sends document to API Gateway
   - API Gateway routes to Lambda function
   - Lambda stores document in S3 bucket (fab-otc-reconciliation-deployment)
     - Bank documents go to the BANK/ folder
     - Counterparty documents go to the COUNTERPARTY/ folder
   - S3 event triggers Document Processor Lambda
   - Document Processor calls Textract/Rekognition
   - Extracted data stored in appropriate DynamoDB table:
     - Bank data goes to BankTradeData table
     - Counterparty data goes to CounterpartyTradeData table

2. **Trade Matching Flow**
   - User initiates reconciliation process
   - API Gateway routes to Lambda function
   - Lambda queries DynamoDB for trades from both BankTradeData and CounterpartyTradeData
   - Matching algorithm identifies potential matches between bank and counterparty trades
   - Match results stored in TradeMatches DynamoDB table

3. **Report Generation Flow**
   - User requests reconciliation report
   - API Gateway routes to Lambda function
   - Lambda queries DynamoDB for match data
   - Report generated and displayed in the frontend
   - User can download or view the reconciliation results

## Security

- **IAM Roles and Policies**
  - Least privilege access for all components
  - Service roles for Lambda functions
  - Bucket policies for S3 access

- **API Security**
  - API Gateway authorization
  - CORS configuration
  - HTTPS for all communications

## Scalability

- **Lambda Auto-scaling**
  - Functions scale automatically with load
  - Concurrent execution limits set appropriately

- **DynamoDB On-demand Capacity**
  - Scales automatically with traffic
  - No need to provision capacity in advance

- **S3 Performance**
  - Highly scalable object storage
  - No performance limits for document storage