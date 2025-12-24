---
inclusion: fileMatch
fileMatchPattern: ['terraform/**/*.tf', 'deployment/**/*.sh', '**/*deploy*.sh', '**/*aws*.py']
---

# AWS Infrastructure Guidelines

## ⚠️ CRITICAL: Infrastructure Deployment Method

**Terraform is NOT used for actual deployment.** All AWS infrastructure was deployed manually via AWS Console and AWS CLI. The `terraform/` folder contains reference configurations only - do NOT assume Terraform state exists or that `terraform apply` was ever run.

**When investigating AWS resource issues:**
1. Query AWS directly using AWS CLI commands
2. Do NOT look in terraform files for current configuration
3. Check AWS Console or use `aws` CLI to verify actual resource settings

## Core Infrastructure

### Region and Environment
- **Primary Region**: us-east-1 (hardcoded in most resources)
- **Production S3 Bucket**: `trade-matching-system-agentcore-production`

### Terraform Structure (REFERENCE ONLY - NOT DEPLOYED)
```
terraform/
├── main.tf           # Provider config, backend (REFERENCE ONLY)
├── variables.tf      # Input variables (REFERENCE ONLY)
├── dynamodb.tf       # Core DynamoDB tables (REFERENCE ONLY)
├── s3.tf             # S3 buckets (REFERENCE ONLY)
└── agentcore/        # AgentCore platform resources (REFERENCE ONLY)
```

## DynamoDB Tables

### Core Tables (PAY_PER_REQUEST billing)
- **BankTradeData**: hash_key=`trade_id`, range_key=`internal_reference`
- **CounterpartyTradeData**: hash_key=`trade_id`, range_key=`internal_reference`
- **ai-trade-matching-processing-status**: hash_key=`sessionId`, workflow status tracking (Dec 2025)
- **ExceptionsTable**: hash_key=`exception_id`, range_key=`timestamp`
- **AgentRegistry**: hash_key=`agent_id`, stores agent metadata and endpoints

### Table Requirements
- Enable point-in-time recovery (`point_in_time_recovery.enabled = true`)
- Enable server-side encryption (`server_side_encryption.enabled = true`)
- Use PAY_PER_REQUEST billing mode (no capacity planning needed)
- All attributes used in keys must be explicitly defined

### Example Pattern
```hcl
resource "aws_dynamodb_table" "example" {
  name         = "TableName"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "primary_key"
  range_key    = "sort_key"  # Optional

  attribute {
    name = "primary_key"
    type = "S"
  }

  point_in_time_recovery { enabled = true }
  server_side_encryption { enabled = true }

  tags = {
    Environment = var.environment
    Project     = "trade-matching-system"
    ManagedBy   = "terraform"
  }
}
```

### Status Table Pattern (Dec 2025)
```hcl
resource "aws_dynamodb_table" "processing_status" {
  name         = "ai-trade-matching-processing-status"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "sessionId"

  attribute {
    name = "sessionId"
    type = "S"
  }

  ttl {
    attribute_name = "expiresAt"
    enabled        = true
  }

  point_in_time_recovery { enabled = true }
  server_side_encryption { enabled = true }

  tags = {
    Environment = var.environment
    Project     = "trade-matching-system"
    Purpose     = "workflow-status-tracking"
    ManagedBy   = "terraform"
  }
}
```

## S3 Bucket Structure

### Production Bucket Layout
```
trade-matching-system-agentcore-production/
├── BANK/                    # Bank trade confirmation PDFs
├── COUNTERPARTY/            # Counterparty trade confirmation PDFs
├── canonical-outputs/       # Structured JSON outputs from extraction
├── reports/                 # Matching reports and summaries
└── exceptions/              # Exception reports
```

### S3 Security Requirements
- Enable versioning for audit trail
- Enable server-side encryption (AES256 or KMS)
- Block public access (all four settings enabled)
- Enable access logging to separate audit bucket
- Use bucket policies for cross-account access if needed

## IAM and Security

### Agent Execution Role Pattern
AgentCore agents require an execution role with these permissions:

**S3 Access**:
- `s3:GetObject`, `s3:PutObject` on specific prefixes
- `s3:ListBucket` on bucket root

**DynamoDB Access**:
- `dynamodb:PutItem`, `dynamodb:GetItem`, `dynamodb:Query`, `dynamodb:Scan`
- `dynamodb:DescribeTable` for table metadata
- `dynamodb:UpdateItem` for status updates

**Bedrock Access**:
- `bedrock:InvokeModel` for Claude Sonnet 4 (`anthropic.claude-3-5-sonnet-20241022-v2:0`)
- `bedrock:InvokeModel` for Amazon Nova Pro (`amazon.nova-pro-v1:0`)

**SQS Access**:
- `sqs:SendMessage`, `sqs:ReceiveMessage`, `sqs:DeleteMessage`
- `sqs:GetQueueAttributes` for queue metadata

**CloudWatch Logs**:
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

### Security Best Practices
- Never use IAM access keys; always use IAM roles
- Apply least-privilege principle (scope permissions to specific resources)
- Enable CloudTrail for all API calls
- Use VPC endpoints for private AWS service access (optional but recommended)
- Rotate credentials regularly if any are used
- Enable MFA for console access

### Required Resource Tags
```hcl
default_tags {
  tags = {
    Environment = var.environment
    Project     = "trade-matching-system"
    ManagedBy   = "terraform"
  }
}
```

## AgentCore Deployment

### Agent Configuration Files
- **Location**: `deployment/<agent_name>/agentcore.yaml`
- **Key Fields**: `name`, `description`, `model_id`, `system_prompt`, `tools`, `execution_role_arn`

### Model IDs
- **Claude Sonnet 4**: `anthropic.claude-3-5-sonnet-20241022-v2:0` (reasoning, extraction, matching)
- **Amazon Nova Pro**: `amazon.nova-pro-v1:0` (document processing, OCR)
- **Temperature**: 0.1 (deterministic outputs)

### Deployment Pattern
```bash
# From deployment/<agent_name>/ directory
./deploy.sh  # Builds Docker image, pushes to ECR, deploys to AgentCore
```

### Common Deployment Issues
- **Execution role missing permissions**: Add required policies to execution role
- **Model ID not found**: Verify model is available in us-east-1 and ID is correct
- **Docker build fails**: Check Dockerfile and dependencies in requirements.txt
- **AgentCore timeout**: Increase timeout in agentcore.yaml (default 30s)

## SQS Queue Naming
- Use FIFO queues for ordered processing: `<queue-name>.fifo`
- Enable content-based deduplication for idempotency
- Set visibility timeout based on agent processing time (30-300 seconds)
- Use dead-letter queues for failed messages

## CloudWatch and Observability

### Log Groups
- Agent logs: `/aws/bedrock/agentcore/<agent-name>`
- API logs: `/aws/apigateway/<api-name>`
- Lambda logs: `/aws/lambda/<function-name>`

### Metrics to Monitor
- Agent invocation count and duration
- DynamoDB read/write capacity (if provisioned)
- S3 request count and error rate
- SQS queue depth and age of oldest message
- Bedrock token usage and throttling

### Cost Optimization
- Use PAY_PER_REQUEST for DynamoDB (no idle capacity costs)
- Set S3 lifecycle policies to transition old objects to Glacier
- Monitor Bedrock token usage (Claude Sonnet 4 is expensive)
- Use billing alarms (see `terraform/agentcore/billing_alarms.tf`)

## Python AWS SDK (boto3) Patterns

### Resource Initialization
```python
import boto3

# Use default credential chain (IAM role)
s3_client = boto3.client('s3', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
```

### Error Handling
```python
from botocore.exceptions import ClientError

try:
    response = s3_client.get_object(Bucket=bucket, Key=key)
except ClientError as e:
    if e.response['Error']['Code'] == 'NoSuchKey':
        # Handle missing object
        pass
    else:
        raise
```

### DynamoDB Best Practices
- Use `batch_write_item` for bulk writes (up to 25 items)
- Use `query` instead of `scan` when possible (more efficient)
- Handle `ProvisionedThroughputExceededException` with exponential backoff
- Use consistent reads only when necessary (costs 2x read capacity)

## Troubleshooting Commands

### Check Agent Status
```bash
aws bedrock-agent list-agents --region us-east-1
aws bedrock-agent get-agent --agent-id <agent-id> --region us-east-1
```

### View CloudWatch Logs
```bash
aws logs tail /aws/bedrock/agentcore/<agent-name> --follow --region us-east-1
```

### Test S3 Access
```bash
aws s3 ls s3://trade-matching-system-agentcore-production/ --region us-east-1
```

### Query DynamoDB
```bash
aws dynamodb scan --table-name BankTradeData --region us-east-1 --max-items 10
```

### Check IAM Role Permissions
```bash
aws iam get-role --role-name <role-name>
aws iam list-attached-role-policies --role-name <role-name>
```
