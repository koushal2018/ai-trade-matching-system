# AgentCore Setup Guide - Before Deployment

This guide walks you through setting up the prerequisites before deploying agents to AgentCore Runtime.

## Step 1: Install Required Tools (2 minutes)

### Install AgentCore SDK

```bash
pip install bedrock-agentcore
```

### Verify Installation

```bash
python -c "from bedrock_agentcore.memory import MemoryClient; print('✅ AgentCore SDK installed')"
```

## Step 2: Configure AWS Credentials (2 minutes)

### Option 1: AWS CLI Configuration

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

### Option 2: Environment Variables

```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1
```

### Verify Credentials

```bash
aws sts get-caller-identity
```

You should see your AWS account ID and user ARN.

## Step 3: Create AgentCore Memory Resources (5 minutes)

AgentCore Memory is required for agents to maintain context and learn from past interactions.

### Option 1: Automated Setup (Recommended)

Run the provided setup script:

```bash
cd deployment
python setup_memory.py
```

This will:
1. Create a memory resource with semantic strategy
2. Wait for it to become ACTIVE
3. Output the memory ARN
4. Save the ARN to `.memory_arn` file

### Option 2: Manual Setup

If you prefer to create memory manually:

```python
from bedrock_agentcore.memory import MemoryClient

# Initialize client
client = MemoryClient(region_name="us-east-1")

# Create memory with semantic strategy
memory = client.create_memory_and_wait(
    name="trade-matching-trade-patterns",
    description="Semantic memory for trade patterns",
    strategies=[
        {
            "semanticMemoryStrategy": {
                "name": "trade-patterns-strategy",
                "description": "Store and retrieve trade patterns",
                "namespaces": ["trade/patterns/{actorId}/{sessionId}"]
            }
        }
    ],
    event_expiry_days=90
)

print(f"Memory ID: {memory['memoryId']}")
print(f"Status: {memory['status']}")
```

### Get the Memory ARN

After creating the memory, you'll need its ARN:

```bash
# If you used the automated script
cat deployment/.memory_arn

# Or get it from AWS
aws bedrock-agentcore-control get-memory \
  --memory-id <memory-id-from-above> \
  --region us-east-1 \
  --query 'memory.arn' \
  --output text
```

The ARN format is:
```
arn:aws:bedrock:us-east-1:ACCOUNT_ID:memory/MEMORY_ID
```

## Step 4: Set Environment Variables (1 minute)

```bash
# Set the memory ARN (from Step 3)
export AGENTCORE_MEMORY_ARN="arn:aws:bedrock:us-east-1:123456789012:memory/abc123"

# Set S3 bucket name
export S3_BUCKET_NAME="trade-matching-bucket"

# Verify
echo $AGENTCORE_MEMORY_ARN
echo $S3_BUCKET_NAME
```

### Make Environment Variables Persistent

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export AGENTCORE_MEMORY_ARN="arn:aws:bedrock:us-east-1:123456789012:memory/abc123"' >> ~/.zshrc
echo 'export S3_BUCKET_NAME="trade-matching-bucket"' >> ~/.zshrc
source ~/.zshrc
```

## Step 5: Verify Infrastructure (3 minutes)

Before deploying agents, verify that the required AWS infrastructure exists:

### Check S3 Bucket

```bash
aws s3 ls s3://trade-matching-bucket --region us-east-1
```

If the bucket doesn't exist, create it:

```bash
aws s3 mb s3://trade-matching-bucket --region us-east-1
aws s3api put-bucket-encryption \
  --bucket trade-matching-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### Check DynamoDB Tables

```bash
# Check if tables exist
aws dynamodb describe-table --table-name BankTradeData --region us-east-1
aws dynamodb describe-table --table-name CounterpartyTradeData --region us-east-1
aws dynamodb describe-table --table-name ExceptionsTable --region us-east-1
aws dynamodb describe-table --table-name AgentRegistry --region us-east-1
```

If tables don't exist, you need to run the Terraform infrastructure setup first (Task 1.2).

### Check SQS Queues

```bash
# List queues
aws sqs list-queues --region us-east-1 | grep -E "(document-upload|extraction|matching|exception|hitl)"
```

If queues don't exist, you need to run the Terraform infrastructure setup first (Task 1.3).

## Step 6: Ready to Deploy! (0 minutes)

Once all prerequisites are met, you're ready to deploy agents:

```bash
cd deployment
chmod +x deploy_all.sh
./deploy_all.sh
```

## Troubleshooting

### Issue: "bedrock-agentcore not found"

**Solution:**
```bash
pip install bedrock-agentcore
# Or if using virtual environment:
source .venv/bin/activate
pip install bedrock-agentcore
```

### Issue: "AWS credentials not configured"

**Solution:**
```bash
aws configure
# Or check if credentials are set:
env | grep AWS
```

### Issue: "Memory creation failed"

**Possible causes:**
1. Insufficient IAM permissions
2. Region not supported
3. Service quota exceeded

**Solution:**
```bash
# Check IAM permissions
aws iam get-user

# Verify region supports AgentCore
aws bedrock-agentcore-control list-memories --region us-east-1

# Check service quotas
aws service-quotas get-service-quota \
  --service-code bedrock \
  --quota-code L-XXXXX \
  --region us-east-1
```

### Issue: "Infrastructure not found (S3, DynamoDB, SQS)"

**Solution:**

You need to complete tasks 1.1-1.3 first:
- Task 1.1: Create S3 bucket
- Task 1.2: Create DynamoDB tables
- Task 1.3: Set up SQS queues

These can be created using Terraform:

```bash
cd terraform/agentcore
terraform init
terraform plan
terraform apply
```

## Checklist

Before running `deploy_all.sh`, ensure:

- [ ] AgentCore SDK installed (`pip install bedrock-agentcore`)
- [ ] AWS credentials configured and verified
- [ ] AgentCore Memory resource created
- [ ] `AGENTCORE_MEMORY_ARN` environment variable set
- [ ] `S3_BUCKET_NAME` environment variable set
- [ ] S3 bucket exists in us-east-1
- [ ] DynamoDB tables exist (BankTradeData, CounterpartyTradeData, ExceptionsTable, AgentRegistry)
- [ ] SQS queues exist (document-upload-events, extraction-events, matching-events, etc.)

## Next Steps

After completing this setup:

1. Run `./deploy_all.sh` to deploy all agents
2. Run `./validate_deployment.sh` to verify deployment
3. Test end-to-end workflow with a sample PDF

## Support

For help:
- Check [README.md](README.md) for detailed documentation
- Review [QUICK_START.md](QUICK_START.md) for quick start guide
- Check AWS documentation for AgentCore Memory
- Contact AWS Support for service-specific issues
