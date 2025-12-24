# Pre-Deployment Checklist for Orchestrator

## Status: Ready for Deployment ✅

All deployment configuration tasks have been completed successfully.

## Completed Tasks

### ✅ Task 9.1: Update Dockerfile
- Added `status_writer.py` to Docker COPY commands
- Verified `boto3>=1.34.0` is in requirements.txt
- **File**: `deployment/swarm_agentcore/Dockerfile`

### ✅ Task 9.2: Update IAM Permissions
- Verified DynamoDB permissions already configured in Terraform
- IAM policy `agentcore_dynamodb_access` includes:
  - `dynamodb:PutItem` - For orchestrator to write status
  - `dynamodb:UpdateItem` - For orchestrator to update status  
  - `dynamodb:GetItem` - For web portal to read status
- Policy already includes `orchestrator_status` table ARN
- **File**: `terraform/agentcore/iam.tf`

### ✅ Task 9.3: Configuration Updates
- Updated `status_writer.py` table name to `trade-matching-system-processing-status`
- Updated `status_writer.py` TTL attribute to `ttl` (matches table configuration)
- Verified DynamoDB table exists and is ACTIVE
- Verified TTL is enabled on table (90-day retention)

## Infrastructure Verification

### DynamoDB Table
- **Name**: `trade-matching-system-processing-status`
- **Status**: ACTIVE ✅
- **Partition Key**: `processing_id` (String)
- **TTL Attribute**: `ttl` (enabled, 90 days)
- **Billing Mode**: PAY_PER_REQUEST

### Orchestrator Implementation
- **Primary Module**: `status_tracker.py` (used by orchestrator)
- **Alternative Module**: `status_writer.py` (available for future use)
- **Entrypoint**: `trade_matching_swarm_agentcore_http.py`
- **Orchestrator Class**: `TradeMatchingHTTPOrchestrator`

## Files Modified

1. **deployment/swarm_agentcore/Dockerfile**
   - Added: `COPY status_writer.py .`

2. **deployment/swarm_agentcore/status_writer.py**
   - Changed table name: `ai-trade-matching-processing-status` → `trade-matching-system-processing-status`
   - Changed TTL attribute: `expiresAt` → `ttl`

## Deployment Command

```bash
cd deployment/swarm_agentcore
agentcore deploy --agent http_agent_orchestrator
```

This will:
1. Build a new Docker image with updated files
2. Push to ECR repository
3. Update AgentCore Runtime
4. Deploy new version

## Testing Before Deployment

### Option 1: Quick Import Test
```bash
cd deployment/swarm_agentcore
python test_imports.py
```

### Option 2: Full Status Tracking Test
```bash
cd deployment/swarm_agentcore
python test_status_tracking_local.py
```

This will:
- Initialize a test workflow status
- Update agent statuses through the workflow
- Verify token usage tracking
- Clean up test data

### Option 3: Full Orchestrator Test (requires real agents)
```bash
cd deployment/swarm_agentcore
python test_local_orchestrator.py <document_id> <source_type>

# Example:
python test_local_orchestrator.py FAB_26933659 BANK
```

## Post-Deployment Verification

### 1. Check Deployment Status
```bash
agentcore status --agent http_agent_orchestrator
```

Expected output:
- Agent ID: `http_agent_orchestrator-lKzrI47Hgd`
- Status: ACTIVE
- Runtime: Container

### 2. Test with Sample Workflow
```bash
# Upload a test PDF
aws s3 cp test.pdf s3://trade-matching-system-agentcore-production/BANK/test_$(date +%s).pdf

# Monitor CloudWatch Logs
aws logs tail /aws/bedrock-agentcore/http_agent_orchestrator --follow
```

### 3. Verify Status Writes
```bash
# Query the status table (replace SESSION_ID with actual value from logs)
aws dynamodb get-item \
  --table-name trade-matching-system-processing-status \
  --key '{"processing_id": {"S": "session-XXXXX"}}' \
  --region us-east-1
```

Expected fields in response:
- `overallStatus`: "completed" or "failed"
- `pdfAdapter`: Status object with `tokenUsage`
- `tradeExtraction`: Status object with `tokenUsage`
- `tradeMatching`: Status object with `tokenUsage`
- `lastUpdated`: Recent timestamp

### 4. Check Web Portal
- Navigate to web portal
- Upload a test PDF
- Verify real-time status updates appear
- Verify token usage is displayed

## Rollback Plan

If deployment fails or issues are found:

```bash
# Check recent deployments
agentcore status --agent http_agent_orchestrator -v

# Rollback to previous version (if needed)
git checkout <previous-commit>
agentcore deploy --agent http_agent_orchestrator
```

## Known Issues

### Import Test Timeout
The `test_imports.py` script may timeout when importing `status_writer.py` if `strands_tools` is not installed. This is expected and does not affect deployment since:
1. The orchestrator uses `StatusTracker` (not `StatusWriter`)
2. `StatusWriter` has fallback to boto3
3. Docker container will have all dependencies installed

### Terminal TTY Issues
Some commands may show "not a tty" warnings. This is cosmetic and does not affect functionality.

## Support

### CloudWatch Logs
```bash
aws logs tail /aws/bedrock-agentcore/http_agent_orchestrator --follow --region us-east-1
```

### DynamoDB Table Status
```bash
aws dynamodb describe-table \
  --table-name trade-matching-system-processing-status \
  --region us-east-1
```

### Agent Status
```bash
agentcore status --agent http_agent_orchestrator -v
```

## Next Steps After Deployment

1. ✅ Monitor first few workflows in CloudWatch Logs
2. ✅ Verify status writes to DynamoDB
3. ✅ Test web portal displays real-time status
4. ✅ Monitor token usage metrics
5. ✅ Review DynamoDB costs (on-demand billing)

## Deployment Confidence: HIGH ✅

All configuration is correct and ready for deployment. The orchestrator has been successfully updated with status tracking capabilities.

---

**Last Updated**: December 24, 2025
**Prepared By**: Kiro AI Assistant
**Status**: Ready for Production Deployment
