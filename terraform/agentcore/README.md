# AgentCore Infrastructure - Terraform Configuration

This directory contains Terraform configuration for deploying AWS infrastructure for the AgentCore migration of the AI Trade Matching System.

## Overview

This Terraform module provisions all necessary AWS resources for running the trade matching system on Amazon Bedrock AgentCore, including:

- **S3 Buckets**: Document storage with lifecycle policies
- **DynamoDB Tables**: Trade data, exceptions, and agent registry
- **SQS Queues**: Event-driven architecture with dead letter queues
- **IAM Roles & Policies**: Least-privilege access for agents
- **Cognito User Pool**: Authentication and authorization
- **CloudWatch**: Logging, metrics, and alerting
- **X-Ray**: Distributed tracing

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.0 installed
3. **S3 Backend** for Terraform state (bucket: `trade-matching-terraform-state`)
4. **DynamoDB Table** for state locking (table: `terraform-state-lock`)

## Directory Structure

```
terraform/agentcore/
├── main.tf                          # Main configuration
├── variables.tf                     # Variable definitions
├── terraform.tfvars.example         # Example variable values
├── s3.tf                            # S3 bucket configuration
├── dynamodb.tf                      # DynamoDB tables
├── sqs.tf                           # SQS queues
├── iam.tf                           # IAM roles and policies
├── cognito.tf                       # Cognito user pool
├── agentcore_memory.tf              # AgentCore Memory config
├── agentcore_gateway.tf             # AgentCore Gateway config
├── agentcore_observability.tf       # CloudWatch and X-Ray
├── configs/                         # Configuration files
│   ├── agentcore_memory_config.json
│   ├── agentcore_gateway_config.json
│   ├── agentcore_observability_config.json
│   ├── AGENTCORE_MEMORY_README.md
│   ├── AGENTCORE_GATEWAY_README.md
│   ├── AGENTCORE_IDENTITY_README.md
│   └── AGENTCORE_OBSERVABILITY_README.md
├── scripts/                         # Deployment scripts
│   ├── deploy_agentcore_memory.sh
│   └── deploy_agentcore_gateway.sh
└── lambda/                          # Lambda function code
    └── custom_operations.py
```

## Quick Start

### 1. Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review Plan

```bash
terraform plan
```

### 4. Apply Configuration

```bash
terraform apply
```

### 5. Post-Deployment Steps

After Terraform completes, follow the instructions in the output to:
1. Deploy AgentCore Memory resources
2. Deploy AgentCore Gateway
3. Create Cognito users
4. Deploy agents

## Resources Created

### S3 Buckets

| Resource | Purpose | Lifecycle |
|----------|---------|-----------|
| `{project}-agentcore-{env}` | Trade documents and outputs | 30d → IA, 90d → Glacier, 365d → Delete |
| `{project}-agentcore-logs-{env}` | Access logs | 30d → IA, 90d → Glacier, 180d → Delete |

**Folder Structure:**
- `BANK/` - Bank trade PDFs
- `COUNTERPARTY/` - Counterparty trade PDFs
- `extracted/` - Extracted trade data (JSON)
- `reports/` - Matching reports (Markdown)
- `config/` - Configuration files

### DynamoDB Tables

| Table | Purpose | Billing | Encryption |
|-------|---------|---------|------------|
| `BankTradeData-{env}` | Bank trades | On-Demand | KMS |
| `CounterpartyTradeData-{env}` | Counterparty trades | On-Demand | KMS |
| `{project}-exceptions-{env}` | Exception tracking | On-Demand | KMS |
| `{project}-agent-registry-{env}` | Agent registration | On-Demand | KMS |

**Features:**
- Point-in-time recovery enabled
- Global secondary indexes for querying
- TTL enabled for exceptions table

### SQS Queues

| Queue | Type | Purpose | Visibility Timeout |
|-------|------|---------|-------------------|
| `document-upload-events` | FIFO | PDF uploads | 5 min |
| `extraction-events` | Standard | OCR completion | 10 min |
| `matching-events` | Standard | Trade extraction | 15 min |
| `exception-events` | Standard | Error handling | 5 min |
| `hitl-review-queue` | FIFO | Human review | 1 hour |
| `ops-desk-queue` | FIFO | Operations team | 30 min |
| `senior-ops-queue` | FIFO | Senior operations | 30 min |
| `compliance-queue` | FIFO | Compliance team | 1 hour |
| `engineering-queue` | Standard | Engineering team | 1 hour |
| `orchestrator-monitoring-queue` | Standard | Orchestrator | 5 min |

**Features:**
- Dead letter queues for all queues
- Long polling enabled (20s)
- Message retention: 4-14 days

### IAM Roles

| Role | Purpose | Policies |
|------|---------|----------|
| `agentcore-runtime-execution` | AgentCore Runtime | S3, DynamoDB, SQS, Bedrock, CloudWatch |
| `agentcore-gateway` | AgentCore Gateway | S3, DynamoDB |
| `lambda-pdf-adapter` | PDF Adapter Agent | S3, SQS, Bedrock, CloudWatch |
| `lambda-trade-extraction` | Trade Extraction Agent | S3, DynamoDB, SQS, Bedrock, CloudWatch |
| `lambda-trade-matching` | Trade Matching Agent | S3, DynamoDB, SQS, Bedrock, CloudWatch |
| `lambda-exception-mgmt` | Exception Management | DynamoDB, SQS, Bedrock, CloudWatch |
| `lambda-orchestrator` | Orchestrator Agent | DynamoDB, SQS, Bedrock, CloudWatch |

### Cognito User Pool

**Configuration:**
- MFA: Optional (required for Admin)
- Password Policy: 12+ chars, mixed case, numbers, symbols
- Token Validity: 1 hour (access/id), 30 days (refresh)
- Advanced Security: Enabled

**User Groups:**
- **Admin**: Full system access
- **Operator**: View and HITL decisions
- **Auditor**: Read-only audit access

### CloudWatch

**Log Groups:**
- `/aws/agentcore/{project}/pdf-adapter-{env}`
- `/aws/agentcore/{project}/trade-extraction-{env}`
- `/aws/agentcore/{project}/trade-matching-{env}`
- `/aws/agentcore/{project}/exception-management-{env}`
- `/aws/agentcore/{project}/orchestrator-{env}`

**Alarms:**
- PDF Adapter error rate > 5%
- PDF Adapter latency > 30s
- Trade Matching error rate > 5%
- Latency anomaly detection (>2x baseline)

**Dashboard:**
- Processing latency (avg, p95, p99)
- Error rate by agent
- Throughput (trades/hour)
- Recent errors

## Configuration

### Environment Variables

Set these in your shell or CI/CD:

```bash
export AWS_REGION=us-east-1
export AWS_PROFILE=default
export TF_VAR_environment=production
export TF_VAR_alert_emails='["ops@example.com"]'
```

### Terraform Variables

Key variables in `terraform.tfvars`:

```hcl
aws_region  = "us-east-1"
environment = "production"
project_name = "trade-matching-system"

# Alert emails
alert_emails = ["ops@example.com"]

# Web Portal URLs
web_portal_callback_urls = ["https://portal.example.com/callback"]
web_portal_logout_urls = ["https://portal.example.com/logout"]
```

## Deployment

### Development Environment

```bash
terraform workspace new dev
terraform workspace select dev
terraform apply -var="environment=dev"
```

### Production Environment

```bash
terraform workspace new production
terraform workspace select production
terraform apply -var="environment=production"
```

## Post-Deployment

### 1. Deploy AgentCore Memory

```bash
cd scripts
./deploy_agentcore_memory.sh
```

### 2. Deploy AgentCore Gateway

```bash
cd scripts
./deploy_agentcore_gateway.sh
```

### 3. Create Admin User

```bash
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com Name=name,Value="Admin User" \
  --temporary-password "TempPass123!" \
  --region us-east-1

aws cognito-idp admin-add-user-to-group \
  --user-pool-id <USER_POOL_ID> \
  --username admin@example.com \
  --group-name Admin \
  --region us-east-1
```

### 4. Verify Deployment

```bash
# Check S3 bucket
aws s3 ls s3://<BUCKET_NAME>

# Check DynamoDB tables
aws dynamodb list-tables --region us-east-1

# Check SQS queues
aws sqs list-queues --region us-east-1

# Check Cognito user pool
aws cognito-idp describe-user-pool --user-pool-id <USER_POOL_ID> --region us-east-1
```

## Monitoring

### CloudWatch Dashboard

View the dashboard:
```bash
aws cloudwatch get-dashboard \
  --dashboard-name <DASHBOARD_NAME> \
  --region us-east-1
```

Or visit: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards

### Logs

Query logs:
```bash
aws logs tail /aws/agentcore/<PROJECT>/pdf-adapter-<ENV> --follow
```

### Metrics

Get metrics:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AgentCore/<PROJECT> \
  --metric-name ProcessingLatency \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z \
  --period 3600 \
  --statistics Average \
  --region us-east-1
```

## Maintenance

### Update Infrastructure

```bash
# Pull latest changes
git pull

# Review changes
terraform plan

# Apply updates
terraform apply
```

### Rotate Secrets

```bash
# Rotate Cognito client secret
aws cognito-idp update-user-pool-client \
  --user-pool-id <USER_POOL_ID> \
  --client-id <CLIENT_ID> \
  --generate-secret \
  --region us-east-1
```

### Backup

DynamoDB tables have point-in-time recovery enabled. To create on-demand backup:

```bash
aws dynamodb create-backup \
  --table-name BankTradeData-production \
  --backup-name BankTradeData-backup-$(date +%Y%m%d) \
  --region us-east-1
```

## Cleanup

### Destroy Infrastructure

**WARNING**: This will delete all resources and data!

```bash
# Review what will be destroyed
terraform plan -destroy

# Destroy resources
terraform destroy
```

### Selective Cleanup

To remove specific resources, use `terraform state rm`:

```bash
# Remove a specific resource from state
terraform state rm aws_s3_bucket.agentcore_trade_documents

# Then destroy it manually
aws s3 rb s3://<BUCKET_NAME> --force
```

## Troubleshooting

### Terraform State Lock

If state is locked:

```bash
# Force unlock (use with caution)
terraform force-unlock <LOCK_ID>
```

### Resource Already Exists

If a resource already exists:

```bash
# Import existing resource
terraform import aws_s3_bucket.agentcore_trade_documents <BUCKET_NAME>
```

### Permission Denied

Ensure your AWS credentials have sufficient permissions:
- S3: Full access
- DynamoDB: Full access
- SQS: Full access
- IAM: Create/update roles and policies
- Cognito: Full access
- CloudWatch: Full access

## Cost Estimation

Estimated monthly costs (us-east-1):

| Service | Cost |
|---------|------|
| S3 | $50-100 |
| DynamoDB (On-Demand) | $100-200 |
| SQS | $10-20 |
| Cognito | $0-50 |
| CloudWatch | $50-100 |
| X-Ray | $10-20 |
| **Total** | **$220-490/month** |

*Costs vary based on usage. AgentCore Runtime costs are additional.*

### Billing Alarms Configured

This infrastructure includes comprehensive billing alarms:
- **Total monthly budget alarm** (configurable threshold)
- **Warning alarm** at 80% of budget
- **Daily spending alarm**
- **Per-service alarms** (S3, DynamoDB, Bedrock, CloudWatch)
- **AWS Budget** with forecasting
- **Cost Anomaly Detection** (optional)

**See**: `COST_SUMMARY.md` and `BILLING_GUIDE.md` for detailed cost information and monitoring setup.

## Support

For issues or questions:
1. Check the README files in `configs/` directory
2. Review CloudWatch logs
3. Check AWS service health dashboard
4. Contact the platform team

## References

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Amazon Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [AWS CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
