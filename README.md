# Trade Reconciliation System

An AI-powered trade reconciliation system built on AWS that automates the matching and reconciliation of trades between bank and counterparty data sources.

## Overview

This system provides:
- **Automated Document Processing**: AI-powered extraction of trade data from PDF documents
- **Intelligent Trade Matching**: Advanced algorithms to match trades between bank and counterparty sources
- **Field-Level Reconciliation**: Detailed comparison of trade attributes with configurable tolerances
- **Interactive Dashboard**: Real-time visualization of reconciliation status and metrics
- **Report Generation**: Comprehensive reconciliation reports with detailed analysis

## Architecture

### Components

- **Frontend**: React TypeScript application with AWS Amplify hosting
- **API Layer**: Amazon API Gateway with AWS Lambda backend
- **AI Agents**: Python-based agents using the Strands framework for trade processing
- **Data Storage**: Amazon DynamoDB for trade data and Amazon S3 for document storage
- **Document Processing**: AWS Lambda with AI services (Textract/Rekognition) for PDF extraction

### AWS Resources

#### DynamoDB Tables
- `BankTradeData`: Stores trade data from bank sources
- `CounterpartyTradeData`: Stores trade data from counterparty sources  
- `TradeMatches`: Stores match relationships and reconciliation results

#### S3 Storage
- Bucket: `fab-otc-reconciliation-deployment`
- `BANK/` folder: Bank trade documents
- `COUNTERPARTY/` folder: Counterparty trade documents

#### Lambda Functions
- **Main API Handler**: Processes API requests from frontend
- **Document Processor** (`trade-pdf-processor`): Extracts data from uploaded documents
- **AI Agents**: Automated trade matching and reconciliation workflows

## Prerequisites

- **AWS Account** with appropriate permissions
- **Node.js** (v16 or higher)
- **Python** (v3.9 or higher)
- **AWS CLI** configured with your credentials

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://gitlab.aws.dev/koushald/agentic-ai-reconcillation.git
cd agentic-ai-reconcillation
```

### 2. Frontend Setup

```bash
cd trade-reconciliation-frontend
npm install
```

Create a `.env` file in the frontend directory:
```bash
REACT_APP_API_GATEWAY_URL=https://your-api-gateway-url.amazonaws.com/dev
REACT_APP_S3_BUCKET=fab-otc-reconciliation-deployment
REACT_APP_AWS_REGION=us-east-1
```

### 3. Backend Setup

Install Python dependencies:
```bash
pip install boto3 flask strands
```

Set up environment variables:
```bash
export BANK_TABLE=BankTradeData
export COUNTERPARTY_TABLE=CounterpartyTradeData
export MATCHES_TABLE=TradeMatches
export BUCKET_NAME=fab-otc-reconciliation-deployment
```

### 4. AWS Resources

Deploy the required AWS infrastructure:
- DynamoDB tables with appropriate schemas
- S3 bucket with proper folder structure
- Lambda functions with correct IAM roles
- API Gateway endpoints

## Usage

### 1. Start the Frontend

```bash
cd trade-reconciliation-frontend
npm start
```

The application will be available at `http://localhost:3000`

### 2. Document Upload

1. Navigate to the "Upload Documents" section
2. Select document source (Bank or Counterparty)
3. Upload PDF trade documents
4. The system automatically extracts trade data using AI

### 3. Trade Matching

The AI agents automatically:
1. Fetch unmatched trades from both sources
2. Apply similarity algorithms to find potential matches
3. Score matches based on configurable weights
4. Update match status in the database

### 4. Reconciliation

For matched trades, the system:
1. Performs field-level comparison
2. Applies tolerance thresholds for numeric fields
3. Uses fuzzy matching for string fields
4. Generates detailed reconciliation reports

### 5. Dashboard

View real-time metrics including:
- Match statistics (matched, partially matched, unmatched)
- Processing trends over time
- Trade volume analysis
- Reconciliation status breakdown

## API Endpoints

### Dashboard
- `GET /dashboard` - Get dashboard summary data

### Document Management
- `POST /documents` - Generate pre-signed URL for document upload

### Trade Management
- `GET /trades` - Get trades with optional filtering
- `GET /trades/{tradeId}` - Get specific trade details

### Match Management
- `GET /matches` - Get matches with optional filtering
- `GET /matches/{matchId}` - Get specific match details
- `PUT /matches/{matchId}/status` - Update match status

### Reconciliation
- `GET /reconciliation/{matchId}` - Get detailed reconciliation results

### Reporting
- `GET /reports` - Get list of reports
- `GET /reports/{reportId}` - Get specific report
- `POST /reports` - Generate new report

### Settings
- `GET /settings` - Get system configuration
- `PUT /settings` - Update system settings

## AI Agent Tools

The system includes specialized tools for automated processing:

### Trade Matching Tools
- `fetch_unmatched_trades()` - Retrieve trades pending matching
- `find_potential_matches()` - Identify candidate matches
- `compute_similarity()` - Calculate match confidence scores
- `update_match_status()` - Update matching results

### Reconciliation Tools
- `fetch_matched_trades()` - Get trades ready for reconciliation
- `compare_fields()` - Perform field-level comparison
- `determine_overall_status()` - Calculate reconciliation status
- `generate_reconciliation_report()` - Create detailed reports

## Configuration

### Matching Weights
Configure field importance for matching algorithm:
```python
weights = {
    "trade_date": 0.3,
    "counterparty_name": 0.2,
    "notional": 0.25,
    "currency": 0.15,
    "product_type": 0.1
}
```

### Tolerance Settings
Set numeric field tolerances:
```python
numeric_tolerance = {
    "total_notional_quantity": 0.001,  # 0.1%
    "fixed_price": 0.01,               # 1%
}
```

### Critical Fields
Define fields that trigger critical mismatch status:
```python
critical_fields = [
    "trade_date",
    "currency", 
    "total_notional_quantity"
]
```

## Development

### Running Tests
```bash
# Frontend tests
cd trade-reconciliation-frontend
npm test

# Backend tests (if implemented)
python -m pytest
```

### Code Structure

```
├── agents.py                          # AI agents and tools
├── lambda_function.py                  # Main API handler
├── architecture_diagram_detailed.md   # System architecture
├── trade-reconciliation-frontend/     # React frontend
│   ├── src/
│   │   ├── components/                # React components
│   │   ├── services/                  # API services
│   │   └── config.ts                  # Configuration
├── trade_extracttion/                 # Document processing
└── *.sh                              # Deployment scripts
```

### Adding New Features

1. **Frontend**: Add React components in `trade-reconciliation-frontend/src/components/`
2. **Backend**: Extend `lambda_function.py` with new API endpoints
3. **AI Processing**: Add new tools to `agents.py` using the `@tool` decorator

## Deployment

### Frontend Deployment
```bash
# Build the application
cd trade-reconciliation-frontend
npm run build

# Deploy to AWS Amplify
aws amplify create-app --name trade-reconciliation
# Follow Amplify deployment process
```

### Backend Deployment
```bash
# Package Lambda functions
zip -r trade-api-handler.zip lambda_function.py
zip -r trade-agents.zip agents.py

# Deploy using AWS CLI or infrastructure as code
aws lambda update-function-code --function-name trade-api-handler --zip-file fileb://trade-api-handler.zip
```

## Monitoring

The system includes comprehensive monitoring through:
- **CloudWatch Logs**: All Lambda function logs
- **CloudWatch Metrics**: API Gateway and Lambda metrics
- **DynamoDB Metrics**: Table performance monitoring
- **Custom Dashboard**: Business metrics and KPIs

## Security

- **IAM Roles**: Least privilege access for all components
- **API Gateway**: Authentication and CORS configuration
- **S3 Bucket Policies**: Restricted document access
- **DynamoDB**: Encryption at rest enabled
- **HTTPS**: All communications encrypted in transit

## Support

For issues or questions:
1. Check the logs in CloudWatch
2. Review the architecture documentation
3. Contact the development team

## License

This project is proprietary and confidential.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a merge request
5. Ensure all tests pass

---

## Troubleshooting

### Common Issues

**Frontend won't start**
- Verify Node.js version (v16+)
- Check environment variables in `.env`
- Run `npm install` to ensure dependencies

**API errors**
- Verify AWS credentials are configured
- Check Lambda function logs in CloudWatch
- Ensure DynamoDB tables exist

**Document processing fails**
- Check S3 bucket permissions
- Verify Lambda function has correct IAM roles
- Review document processing Lambda logs

**No matches found**
- Check if trades exist in both sources
- Review matching algorithm weights
- Verify composite key generation logic
