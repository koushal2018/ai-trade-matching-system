# Quick Deploy: Orchestrator Status Table

## TL;DR

```bash
# Deploy the table
cd terraform/agentcore
chmod +x scripts/deploy_status_table.sh
./scripts/deploy_status_table.sh

# Validate deployment
chmod +x scripts/validate_status_table.sh
./scripts/validate_status_table.sh

# Update IAM permissions
terraform apply
```

## What Gets Created

- **Table**: `ai-trade-matching-processing-status`
- **Key**: `sessionId` (partition key)
- **Billing**: On-demand (pay per request)
- **TTL**: 90 days on `expiresAt` attribute
- **Encryption**: KMS with auto-rotation
- **Backup**: Point-in-time recovery enabled

## IAM Permissions

The orchestrator and all agents get permissions to:
- `dynamodb:PutItem` - Write status updates
- `dynamodb:UpdateItem` - Update existing status
- `dynamodb:GetItem` - Read status (web portal)
- `kms:Encrypt/Decrypt` - Use KMS encryption

## Cost

~$0.39/month for 1,000 workflows/day

## Verification

```bash
# Check table exists
aws dynamodb describe-table \
  --table-name ai-trade-matching-processing-status \
  --region us-east-1 \
  --query 'Table.[TableName,TableStatus,BillingModeSummary.BillingMode]'

# Check TTL
aws dynamodb describe-time-to-live \
  --table-name ai-trade-matching-processing-status \
  --region us-east-1 \
  --query 'TimeToLiveDescription.[TimeToLiveStatus,AttributeName]'
```

## Next Steps

1. Implement StatusWriter class (Task 2)
2. Integrate with orchestrator (Task 3)
3. Update agent responses (Task 5)
4. Update web portal backend (Task 7)

## Rollback

```bash
terraform destroy -target=aws_dynamodb_table.orchestrator_status
```

## Full Documentation

See `ORCHESTRATOR_STATUS_TABLE_DEPLOYMENT.md` for complete details.
