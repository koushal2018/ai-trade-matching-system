# Orchestrator Deployment Instructions

## Overview
This document provides instructions for deploying the HTTP Agent Orchestrator with status tracking capabilities.

## Prerequisites
- AWS CLI configured with appropriate credentials
- AgentCore CLI installed (`pip install bedrock-agentcore-starter-toolkit`)
- Docker installed and running
- Access to AWS account 401552979575

## Files Updated
1. **Dockerfile** - Added `status_writer.py` to the Docker image
2. **status_writer.py** - Updated default table name to `trade-matching-system-processing-status` and TTL attribute to `ttl`
3. **requirements.txt** - Already includes boto3>=1.34.0 (no changes needed)

## Deployment Steps

### Step 1: Verify Prerequisites
```bash
# Check agentcore CLI
which agentcore

# Check Docker
docker --version

# Check AWS credentials
aws sts get-caller-identity
```

### Step 2: Navigate to Orchestrator Directory
```bash
cd deployment/swarm_agentcore
```

### Step 3: Deploy the Orchestrator
```bash
# Deploy using agentcore CLI
agentcore deploy --agent http_agent_orchestrator

# This will:
# 1. Build a new Docker image with status_writer.py included
# 2. Push the image to ECR
# 3. Update the AgentCore runtime
# 4. Deploy the new version
```

### Step 4: Verify Deployment
```bash
# Check agent status
agentcore status --agent http_agent_orchestrator

# Expected output should show:
# - Agent ID: http_agent_orchestrator-lKzrI47Hgd
# - Status: ACTIVE
# - Runtime: Container
```

### Step 5: Test Status Tracking

#### Option A: Upload a Test PDF
```bash
# Upload a test PDF to trigger the workflow
aws s3 cp test.pdf s3://trade-matching-system-agentcore-production/BANK/test_$(date +%s).pdf
```

#### Option B: Manual Test with Sample Payload
```bash
# Create test payload
cat > test_payload.json <<EOF
{
  "document_path": "s3://trade-matching-system-agentcore-production/BANK/test.pdf",
  "source_type": "BANK",
  "document_id": "test_001",
  "correlation_id": "test_corr_$(date +%s)"
}
EOF

# Invoke orchestrator
agentcore invoke --agent http_agent_orchestrator --payload-file test_payload.json
```

### Step 6: Verify Status Writes

After running a test workflow, check the status table:

```bash
# Query the status table (replace SESSION_ID with actual session ID from test)
aws dynamodb get-item \
  --table-name trade-matching-system-processing-status \
  --key '{"processing_id": {"S": "session-test_corr_XXXXX"}}' \
  --region us-east-1
```

Expected response should include:
- `overallStatus`: "completed" or "failed"
- `pdfAdapter`: Status object with token usage
- `tradeExtraction`: Status object with token usage
- `tradeMatching`: Status object with token usage
- `lastUpdated`: Recent timestamp

## Troubleshooting

### Deployment Fails
If deployment fails, check:
1. Docker is running: `docker ps`
2. AWS credentials are valid: `aws sts get-caller-identity`
3. ECR repository exists: `aws ecr describe-repositories --repository-names bedrock-agentcore-http_agent_orchestrator --region us-east-1`

### Status Writes Not Working
If status writes fail:
1. Check CloudWatch Logs: `/aws/bedrock-agentcore/http_agent_orchestrator`
2. Verify IAM permissions: The orchestrator execution role should have DynamoDB PutItem/UpdateItem permissions
3. Check table exists: `aws dynamodb describe-table --table-name trade-matching-system-processing-status --region us-east-1`

### Agent Not Responding
If the agent doesn't respond:
1. Check agent status: `agentcore status --agent http_agent_orchestrator -v`
2. Review CloudWatch Logs for errors
3. Verify network configuration (PUBLIC mode)

## IAM Permissions

The orchestrator execution role already has the required permissions:
- `dynamodb:PutItem` - Initialize status
- `dynamodb:UpdateItem` - Update agent status
- `dynamodb:GetItem` - Read status (for web portal)

These permissions are configured in `terraform/agentcore/iam.tf` via the `agentcore_dynamodb_access` policy.

## Configuration

### Environment Variables

The orchestrator uses these environment variables:
- `AWS_REGION`: us-east-1 (default)
- `STATUS_TABLE_NAME`: trade-matching-system-processing-status (default) - **CRITICAL: Must match actual table name**
- `IDEMPOTENCY_TABLE_NAME`: WorkflowIdempotency (optional - disables idempotency if table doesn't exist)
- `PDF_ADAPTER_AGENT_ARN`: ARN of PDF Adapter agent
- `TRADE_EXTRACTION_AGENT_ARN`: ARN of Trade Extraction agent
- `TRADE_MATCHING_AGENT_ARN`: ARN of Trade Matching agent
- `EXCEPTION_MANAGEMENT_AGENT_ARN`: ARN of Exception Management agent

**Note**: The `STATUS_TABLE_NAME` is now set in `agentcore.yaml` and will be automatically injected during deployment.

### Table Configuration
- **Table Name**: trade-matching-system-processing-status
- **Partition Key**: processing_id (String)
- **TTL Attribute**: ttl (90 days retention)
- **Billing Mode**: On-demand

## Rollback

If you need to rollback to the previous version:

```bash
# Get previous deployment
agentcore status --agent http_agent_orchestrator -v

# Rollback (if supported by agentcore CLI)
# Or redeploy from a previous commit
git checkout <previous-commit>
agentcore deploy --agent http_agent_orchestrator
```

## Next Steps

After successful deployment:
1. Monitor CloudWatch Logs for any errors
2. Test with real PDF uploads
3. Verify web portal displays real-time status
4. Monitor DynamoDB metrics (read/write capacity)
5. Review cost allocation (on-demand billing)

## Support

For issues or questions:
- Check CloudWatch Logs: `/aws/bedrock-agentcore/http_agent_orchestrator`
- Review AgentCore documentation: https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html
- Check DynamoDB table metrics in AWS Console

## Deployment Checklist

- [ ] Dockerfile updated with status_writer.py
- [ ] status_writer.py table name corrected
- [ ] status_writer.py TTL attribute corrected
- [ ] boto3 in requirements.txt (already present)
- [ ] IAM permissions verified
- [ ] DynamoDB table exists and is ACTIVE
- [ ] TTL enabled on table
- [ ] Orchestrator deployed successfully
- [ ] Test workflow executed
- [ ] Status writes verified in DynamoDB
- [ ] Web portal displays real-time status

