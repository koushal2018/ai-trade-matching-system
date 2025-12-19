# Development Environment Setup

This guide helps you set up your local development environment to work with production AWS resources.

## ⚠️ Important Warning

**You will be connecting to PRODUCTION AWS resources!**
- Be careful when testing - you're working with live data
- Consider using read-only operations during development
- Always backup data before making changes
- Test thoroughly in development before deploying to production

## Quick Setup

### 1. Run the Setup Script

```bash
python scripts/setup_dev_environment.py
```

This will:
- Create `.env` symlink to `.env.dev`
- Install Python and Node.js dependencies
- Create data directories for local testing
- Setup git hooks for development workflow

### 2. Configure AWS Credentials

Make sure your AWS credentials are configured:

```bash
aws configure
```

Or verify existing credentials:

```bash
aws sts get-caller-identity
```

### 3. Verify Production Connection

Test connectivity to all production resources:

```bash
python scripts/verify_production_connection.py
```

This will check:
- AWS credentials
- S3 bucket access
- DynamoDB table access
- Bedrock model access

### 4. Start Development Servers

**Backend (FastAPI):**
```bash
cd web-portal-api
source ../.venv_new/bin/activate  # On Windows: ..\.venv_new\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (React):**
```bash
cd web-portal
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Production Resources

Your development environment connects to these production resources:

### DynamoDB Tables
- `BankTradeData` - Bank trade data
- `CounterpartyTradeData` - Counterparty trade data
- `TradeMatches` - Matched trades
- `ExceptionsTable` - Processing exceptions
- `AgentRegistry` - Agent monitoring data
- `HITLReviews` - Human-in-the-loop reviews
- `AuditTrail` - Audit logs
- `ai-trade-matching-processing-status` - Processing status

### S3 Bucket
- `trade-matching-bucket` - Document storage

### Bedrock Model
- `anthropic.claude-sonnet-4-20250514-v1:0` - AI model for processing

## Development Workflow

### Branch Strategy
- **`dev`** - Development branch (you're here)
- **`main`** - Production branch

### Making Changes
1. Work on the `dev` branch
2. Test locally with production data (carefully!)
3. Commit and push to `dev` branch
4. CI/CD will run tests automatically
5. Create merge request from `dev` to `main` when ready

### Testing
```bash
# Backend tests
cd web-portal-api
pytest

# Frontend tests
cd web-portal
npm test

# Linting
flake8 web-portal-api/ --max-line-length=100
cd web-portal && npm run lint
```

## Environment Variables

Key environment variables in `.env.dev`:

```bash
# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=trade-matching-bucket

# DynamoDB Tables
DYNAMODB_BANK_TABLE=BankTradeData
DYNAMODB_COUNTERPARTY_TABLE=CounterpartyTradeData
DYNAMODB_MATCHED_TABLE=TradeMatches
# ... (see .env.dev for complete list)

# Application
ENVIRONMENT=development
DEBUG=true
API_PORT=8000
```

## Troubleshooting

### AWS Credentials Issues
```bash
# Check credentials
aws sts get-caller-identity

# Reconfigure if needed
aws configure
```

### DynamoDB Access Issues
- Ensure your AWS user has DynamoDB permissions
- Check table names match production resources
- Verify region is set to `us-east-1`

### S3 Access Issues
- Ensure your AWS user has S3 permissions
- Check bucket name and region
- Verify bucket exists: `aws s3 ls s3://trade-matching-bucket`

### Bedrock Access Issues
- Ensure Bedrock is enabled in your AWS account
- Check model access permissions
- Verify model ID is correct

## Safety Guidelines

### Read-Only Development
For safer development, consider using read-only operations:

```python
# Good: Read data
trades = dynamodb.scan(TableName='BankTradeData')

# Caution: Write operations affect production
# dynamodb.put_item(TableName='BankTradeData', Item=item)
```

### Data Backup
Before making changes that affect data:

```bash
# Backup DynamoDB table
aws dynamodb create-backup \
  --table-name BankTradeData \
  --backup-name dev-backup-$(date +%Y%m%d)
```

### Testing with Sample Data
Use the `data/` directory for local testing:

```bash
# Create test files
echo "test data" > data/COUNTERPARTY/test-trade.pdf
```

## Getting Help

- Check the [main README](README.md) for project overview
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Check AWS documentation for service-specific issues
- Contact the development team for code-related questions

## Next Steps

Once your environment is set up:

1. Explore the codebase structure
2. Review existing trade data in production (read-only)
3. Test the web portal functionality
4. Make your first development changes
5. Follow the git workflow for contributions

Happy coding! 🚀