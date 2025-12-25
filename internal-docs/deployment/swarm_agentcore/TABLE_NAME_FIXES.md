# DynamoDB Table Name Fixes - Dec 24, 2025

## ⚠️ CRITICAL RECURRING ISSUE - PARTITION KEY NAME

**THIS HAS BEEN MISSED 10-20+ TIMES - READ CAREFULLY**

The actual deployed table `trade-matching-system-processing-status` uses:
- **Partition Key:** `processing_id` (NOT `sessionId`)

Verify with:
```bash
aws dynamodb describe-table --table-name trade-matching-system-processing-status --region us-east-1 --query 'Table.KeySchema'
```

Output:
```json
[{"AttributeName": "processing_id", "KeyType": "HASH"}]
```

## Issues Fixed

### 1. Status Tracking Table Name Mismatch
**Problem:** Code was looking for `ai-trade-matching-processing-status` but actual table is `trade-matching-system-processing-status`

**Actual Table ARN:** `arn:aws:dynamodb:us-east-1:401552979575:table/trade-matching-system-processing-status`

**Files Updated:**
- `deployment/swarm_agentcore/http_agent_orchestrator.py` - Line ~318
- `deployment/swarm_agentcore/status_tracker.py` - Line ~18

**Fix:** Changed default table name to `trade-matching-system-processing-status`

### 2. Partition Key Name Mismatch ⚠️ CRITICAL
**Problem:** Code was using `sessionId` as partition key but actual table uses `processing_id`

**Files Updated:**
- `deployment/swarm_agentcore/status_tracker.py` - Lines ~48, ~130, ~158

**Fix:** Changed all DynamoDB operations to use `processing_id`:
```python
# CORRECT
Key={"processing_id": {"S": session_id}}

# WRONG - DO NOT USE
Key={"sessionId": {"S": session_id}}  # ❌ This causes ValidationException
```

### 3. WorkflowIdempotency Table
**Problem:** Code was trying to use `WorkflowIdempotency` table which doesn't exist and is not in the design

**Fix:** Disabled idempotency caching entirely by:
- Setting `self.idempotency_cache = None` in orchestrator initialization
- Adding null checks before all `idempotency_cache` method calls
- Added comments indicating it's disabled

**Files Updated:**
- `deployment/swarm_agentcore/http_agent_orchestrator.py` - Lines ~318, ~332, ~593, ~618

## Next Steps

After these fixes, you need to redeploy:
```bash
cd deployment/swarm_agentcore
agentcore launch --auto-update-on-conflict
```

## Notes

- Status tracking is now enabled and will write to the correct table with correct key
- Idempotency is disabled (not in design) - duplicate workflows will re-execute
- Both changes are non-breaking - workflow continues even if tables are missing
- **ALWAYS verify partition key name when working with this table**
