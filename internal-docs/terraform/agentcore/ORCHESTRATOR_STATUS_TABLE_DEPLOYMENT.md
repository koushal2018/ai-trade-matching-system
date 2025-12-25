# Orchestrator Status Table Deployment Guide

## Overview

This guide covers the deployment of the `ai-trade-matching-processing-status` DynamoDB table for real-time workflow status tracking.

## Table Specifications

- **Table Name**: `ai-trade-matching-processing-status`
- **Partition Key**: `sessionId` (String)
- **Billing Mode**: On-demand (PAY_PER_REQUEST)
- **TTL**: Enabled on `expiresAt` attribute (90 days retention)
- **Encryption**: Server-side encryption with KMS
- **Point-in-Time Recovery**: Enabled

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed (version >= 1.0)
3. Access to the `trade-matching-system` AWS account
4. Permissions to create DynamoDB tables and IAM policies

## Deployment Steps

### Option 1: Automated Deployment (Recommended)

Run the deployment script:

```bash
cd terraform/agentcore
./scripts/deploy_status_table.sh
```

This script will:
1. Initialize Terraform if needed
2. Validate the configuration
3. Show a plan of changes
4. Apply the changes after confirmation
5. Verify the table was created successfully
6. Check TTL configuration

### Option 2: Manual Deployment

1. Navigate to the terraform directory:
```bash
cd terraform/agentcore
```

2. Initialize Terraform (if not already done):
```bash
terraform init
```

3. Plan the deployment:
```bash
terraform plan -target=aws_dynamodb_table.orchestrator_status
```

4. Apply the changes:
```bash
terraform apply -target=aws_dynamodb_table.orchestrator_status
```

5. Verify the table:
```bash
aws dynamodb describe-table \
  --table-name ai-trade-matching-processing-status \
  --region us-east-1
```

### Option 3: AWS CLI Direct Creation

If you need to create the table without Terraform:

```bash
aws dynamodb create-table \
  --table-name ai-trade-matching-processing-status \
  --attribute-definitions AttributeName=sessionId,AttributeType=S \
  --key-schema AttributeName=sessionId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 \
  --tags Key=Name,Value="Orchestrator Processing Status" \
         Key=Component,Value=AgentCore \
         Key=Environment,Value=production \
         Key=Purpose,Value="Real-time workflow status tracking"

# Enable TTL
aws dynamodb update-time-to-live \
  --table-name ai-trade-matching-processing-status \
  --time-to-live-specification "Enabled=true, AttributeName=expiresAt" \
  --region us-east-1

# Enable Point-in-Time Recovery
aws dynamodb update-continuous-backups \
  --table-name ai-trade-matching-processing-status \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
  --region us-east-1
```

## IAM Permissions Update

After creating the table, update IAM permissions to allow the orchestrator to write:

```bash
cd terraform/agentcore
terraform apply
```

This will update the `agentcore_dynamodb_access` policy to include permissions for the new status table.

## Verification

### 1. Check Table Status

```bash
aws dynamodb describe-table \
  --table-name ai-trade-matching-processing-status \
  --region us-east-1 \
  --query 'Table.[TableName,TableStatus,BillingModeSummary.BillingMode]' \
  --output table
```

Expected output:
```
-------------------------------------------------
|              DescribeTable                    |
+-----------------------------------------------+
|  ai-trade-matching-processing-status          |
|  ACTIVE                                       |
|  PAY_PER_REQUEST                              |
+-----------------------------------------------+
```

### 2. Verify TTL Configuration

```bash
aws dynamodb describe-time-to-live \
  --table-name ai-trade-matching-processing-status \
  --region us-east-1
```

Expected output:
```json
{
    "TimeToLiveDescription": {
        "TimeToLiveStatus": "ENABLED",
        "AttributeName": "expiresAt"
    }
}
```

### 3. Test Write Access

Create a test item:

```bash
aws dynamodb put-item \
  --table-name ai-trade-matching-processing-status \
  --item '{
    "sessionId": {"S": "test-session-123"},
    "correlationId": {"S": "test-corr-123"},
    "overallStatus": {"S": "initializing"},
    "createdAt": {"S": "2025-12-24T12:00:00Z"},
    "expiresAt": {"N": "1735123200"}
  }' \
  --region us-east-1
```

Verify the item was created:

```bash
aws dynamodb get-item \
  --table-name ai-trade-matching-processing-status \
  --key '{"sessionId": {"S": "test-session-123"}}' \
  --region us-east-1
```

Clean up test item:

```bash
aws dynamodb delete-item \
  --table-name ai-trade-matching-processing-status \
  --key '{"sessionId": {"S": "test-session-123"}}' \
  --region us-east-1
```

## Table Schema

### Primary Key
- `sessionId` (String) - Unique session identifier for each workflow execution

### Attributes
- `correlationId` (String) - Correlation ID from orchestrator
- `documentId` (String) - S3 document identifier
- `sourceType` (String) - BANK or COUNTERPARTY
- `overallStatus` (String) - initializing, processing, completed, failed
- `pdfAdapter` (Map) - PDF Adapter agent status
- `tradeExtraction` (Map) - Trade Extraction agent status
- `tradeMatching` (Map) - Trade Matching agent status
- `exceptionManagement` (Map) - Exception Management agent status
- `totalTokenUsage` (Map) - Aggregated token usage
- `totalDuration` (Number) - Total processing time in seconds
- `createdAt` (String) - ISO 8601 timestamp
- `lastUpdated` (String) - ISO 8601 timestamp
- `expiresAt` (Number) - Unix timestamp for TTL (90 days)

### Agent Status Object Structure
```json
{
  "status": "pending|in-progress|success|error",
  "activity": "Human-readable description",
  "startedAt": "ISO 8601 timestamp",
  "completedAt": "ISO 8601 timestamp",
  "duration": 17.095,
  "tokenUsage": {
    "inputTokens": 11689,
    "outputTokens": 2480,
    "totalTokens": 14169
  },
  "error": "Error message if failed"
}
```

## Cost Estimation

- **Billing Mode**: On-demand (no provisioned capacity)
- **Write Cost**: $1.25 per million write request units
- **Read Cost**: $0.25 per million read request units
- **Storage**: $0.25 per GB-month
- **TTL**: No additional cost

### Estimated Monthly Cost (1000 workflows/day)
- Writes: ~8 writes per workflow × 30,000 workflows = 240,000 writes = $0.30/month
- Reads: ~10 reads per workflow × 30,000 workflows = 300,000 reads = $0.08/month
- Storage: ~1 KB per item × 30,000 items = 30 MB = $0.01/month
- **Total**: ~$0.39/month

## Troubleshooting

### Table Creation Failed

If table creation fails, check:
1. AWS credentials are configured correctly
2. You have permissions to create DynamoDB tables
3. The table name doesn't already exist
4. The region is set to us-east-1

### TTL Not Enabled

TTL enablement can take a few minutes. Check status:
```bash
aws dynamodb describe-time-to-live \
  --table-name ai-trade-matching-processing-status \
  --region us-east-1
```

If status is "ENABLING", wait a few minutes and check again.

### IAM Permission Errors

If the orchestrator can't write to the table:
1. Verify the IAM policy was updated
2. Check the orchestrator's execution role has the policy attached
3. Verify the KMS key permissions for encryption

## Next Steps

After deploying the table:

1. **Implement StatusWriter**: Create the `status_writer.py` module (Task 2)
2. **Integrate with Orchestrator**: Update `http_agent_orchestrator.py` (Task 3)
3. **Update Agents**: Standardize agent response formats (Task 5)
4. **Update Web Portal**: Implement DynamoDB query endpoint (Task 7)
5. **Test End-to-End**: Upload a test PDF and verify status tracking

## Rollback

To remove the table:

```bash
cd terraform/agentcore
terraform destroy -target=aws_dynamodb_table.orchestrator_status
```

Or using AWS CLI:

```bash
aws dynamodb delete-table \
  --table-name ai-trade-matching-processing-status \
  --region us-east-1
```

## Support

For issues or questions:
1. Check CloudWatch Logs: `/aws/dynamodb/ai-trade-matching-processing-status`
2. Review Terraform state: `terraform show`
3. Check AWS Console: DynamoDB → Tables → ai-trade-matching-processing-status
