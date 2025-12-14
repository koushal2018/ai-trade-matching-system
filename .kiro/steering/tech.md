# Technology Stack

## Frontend
- **Framework**: React 18.2.0 with TypeScript
- **Styling**: Tailwind CSS 3.3.3 with Headless UI components
- **State Management**: React hooks and context
- **HTTP Client**: Axios for API communication
- **Charts**: Chart.js with react-chartjs-2
- **File Upload**: react-dropzone
- **Routing**: React Router DOM 6.15.0
- **Testing**: Jest with React Testing Library

## Backend
- **Runtime**: Node.js with AWS Lambda
- **Language**: JavaScript (ES6+)
- **AWS SDK**: aws-sdk v2.1450.0
- **Data Processing**: csv-parser, xlsx, json2csv
- **Utilities**: uuid, moment.js

## AI/ML Framework
- **Framework**: Strands Agents SDK Framework for AI agent orchestration
- **Language**: Python 3.9+
- **AI Providers**: Amazon Bedrock, HuggingFace, SageMaker
- **Document Processing** : Use AI Vision Models

## AWS Infrastructure
- **Compute**: AWS Lambda functions
- **API**: Amazon API Gateway
- **Storage**: Amazon S3, DynamoDB
- **Authentication**: AWS Cognito (optional)
- **Hosting**: AWS Amplify
- **Infrastructure**: CloudFormation templates

## Common Commands

### Frontend Development
```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

### Backend Development
```bash
# Install Python dependencies
pip install boto3 flask strands

# Run AI agents locally
python run_enhanced_reconciliation.py

# Test Strands integration
python test_strands_integration.py
```

### AWS Deployment
```bash
# Deploy infrastructure
./deploy.sh

# Validate CloudFormation templates
./client-deployment/validate_and_upload.sh

# Deploy frontend to Amplify
./client-deployment/deploy-frontend.sh
```

### Environment Setup
```bash
# Required environment variables
export AWS_REGION=us-east-1
export BANK_TRADES_TABLE=BankTradeData
export COUNTERPARTY_TRADES_TABLE=CounterpartyTradeData
export TRADE_MATCHES_TABLE=TradeMatches
export BUCKET_NAME=fab-otc-reconciliation-deployment
```