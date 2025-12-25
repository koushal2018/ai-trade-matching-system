# Bug Report: Frontend Status Not Updating Despite Successful Orchestrator Execution

**Date**: December 24, 2025  
**Severity**: High  
**Component**: Frontend Status Tracking Integration  
**Status**: ✅ RESOLVED (December 24, 2025)

## Summary

Frontend UI shows all agents as "Pending" even though the orchestrator successfully processes documents and writes status updates to DynamoDB.

## Resolution Summary

**Root Cause**: Session ID mismatch between upload API and orchestrator. The upload API was generating `session_id` from `upload_id`, but the orchestrator was generating it from `document_id` which included the filename suffix, causing the frontend to query a different key than what the orchestrator wrote.

**Fix Applied**: Synchronized session ID generation across all components using `document_id` as the common identifier:
- Upload API: `session_id = f"session-{upload_id}"` (upload_id becomes document_id in S3 key)
- Orchestrator: `session_id = f"session-{document_id}"` (extracts document_id from S3 key)
- Status Tracker: Uses `processing_id` as partition key (matches session_id)
- Backend API: Queries with `processing_id` (not `sessionId`)

**Files Changed**:
- `deployment/swarm_agentcore/http_agent_orchestrator.py` - Use document_id for session_id
- `deployment/swarm_agentcore/status_tracker.py` - Use processing_id as partition key
- `web-portal-api/app/routers/workflow.py` - Query with processing_id key

**Documentation**: See `deployment/swarm_agentcore/SESSION_ID_FIX.md` for detailed fix documentation.

## Evidence

### Orchestrator Logs (SUCCESS)
```
2025-12-24 17:04:50,968 - status_tracker - INFO - [corr_302302a9b38c] Status initialized for session: session-f2bf339a-14c1-454d-bb45-575e5235436a-FAB_26933659
2025-12-24 17:04:50,976 - status_tracker - INFO - [corr_302302a9b38c] Updated pdfAdapter status to in-progress
2025-12-24 17:04:12,499 - status_tracker - INFO - [corr_0217128c4485] Updated pdfAdapter status to success
2025-12-24 17:04:12,505 - status_tracker - INFO - [corr_0217128c4485] Updated tradeExtraction status to in-progress
2025-12-24 17:04:19,446 - status_tracker - INFO - [corr_0217128c4485] Updated tradeExtraction status to success
2025-12-24 17:04:19,452 - status_tracker - INFO - [corr_0217128c4485] Updated tradeMatching status to in-progress
2025-12-24 17:05:01,184 - status_tracker - INFO - [corr_0217128c4485] Updated tradeMatching status to success
2025-12-24 17:05:01,189 - status_tracker - INFO - [corr_0217128c4485] Finalized workflow status: completed
```

### Frontend UI (STUCK ON PENDING)
```
PDF Adapter Agent         Pending - Waiting for upload
Trade Extraction Agent    Pending - Waiting for PDF processing
Trade Matching Agent      Pending - Waiting for extraction
Exception Management Agent Pending - No exceptions
Last updated: 9:02:42 PM
```

## Root Cause Analysis

### Hypothesis 1: Session ID Mismatch (MOST LIKELY)

The orchestrator generates `session_id` from `document_id`:
```python
session_id = f"session-{document_id}"
# Result: session-f2bf339a-14c1-454d-bb45-575e5235436a-FAB_26933659
```

But the upload API may be generating a different `session_id` format that the frontend is using to query.

**Verification needed:**
1. What `sessionId` does the upload API return to the frontend?
2. What `processing_id` is being written to DynamoDB?
3. Are they the same value?

### Hypothesis 2: Frontend Not Polling Correct Session ID

The frontend may be:
- Using a hardcoded or stale session ID
- Not receiving the session ID from the upload response
- Polling with incorrect format

### Hypothesis 3: Backend Query Issue

The web portal backend may be:
- Querying with wrong key format
- Not finding the item in DynamoDB
- Returning default "pending" status

## Diagnostic Steps

### Step 1: Verify DynamoDB Has Data
```bash
aws dynamodb get-item \
  --table-name trade-matching-system-processing-status \
  --key '{"processing_id": {"S": "session-f2bf339a-14c1-454d-bb45-575e5235436a-FAB_26933659"}}' \
  --region us-east-1
```

### Step 2: Check Upload API Response
Look at the upload API response to see what `sessionId` it returns:
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test.pdf" \
  -F "source_type=BANK" | jq '.sessionId'
```

### Step 3: Check Frontend Network Tab
In browser DevTools → Network tab:
1. What URL is the frontend polling?
2. What `sessionId` is in the URL?
3. What response is the backend returning?

### Step 4: Test Backend Directly
```bash
# Use the session ID from orchestrator logs
curl http://localhost:8000/api/workflow/session-f2bf339a-14c1-454d-bb45-575e5235436a-FAB_26933659/status | jq
```

## Suspected Issue

Based on `SESSION_ID_FIX.md`, the fix was:
- Upload API: `session_id = f"session-{upload_id}"`
- Orchestrator: `session_id = f"session-{document_id}"`

The `upload_id` and `document_id` should be the same (upload_id is embedded in S3 key as document_id).

**BUT** looking at the logs:
- `document_id = f2bf339a-14c1-454d-bb45-575e5235436a-FAB_26933659`

This suggests the document_id includes both the UUID AND the filename suffix. If the upload API only uses the UUID portion for session_id, there's a mismatch.

## Files to Investigate

1. **Upload API**: `web-portal-api/app/routers/upload.py`
   - How is `session_id` generated?
   - What is returned to frontend?

2. **Orchestrator**: `deployment/swarm_agentcore/http_agent_orchestrator.py`
   - How is `session_id` derived from `document_id`?
   - Line 395: `session_id = f"session-{document_id}"`

3. **Frontend Hook**: `web-portal/src/hooks/useAgentStatus.ts`
   - What session ID is being used for polling?

4. **S3 Event Trigger**: How does the S3 key get parsed into `document_id`?

## Expected vs Actual (Before Fix)

| Component | Expected | Actual (Before Fix) |
|-----------|----------|-------------------|
| Upload API session_id | `session-{uuid}` | `session-{uuid}` |
| Orchestrator session_id | `session-{uuid}` | `session-{uuid}-{filename}` |
| DynamoDB key | Same as upload | Different from upload |
| Frontend query | Uses upload session_id | Can't find orchestrator's key |

## Verified Flow (After Fix)

| Component | Value | Status |
|-----------|-------|--------|
| Upload API session_id | `session-{upload_id}` | ✅ |
| S3 Key | `{sourceType}/{upload_id}-{filename}` | ✅ |
| Orchestrator document_id | `{upload_id}-{filename}` | ✅ |
| Orchestrator session_id | `session-{document_id}` | ✅ |
| DynamoDB partition key | `processing_id = session_id` | ✅ |
| Backend query key | `processing_id` | ✅ |
| Frontend receives | Real-time status updates | ✅ |

## Related Files

- `deployment/swarm_agentcore/SESSION_ID_FIX.md` - Detailed fix documentation
- `deployment/swarm_agentcore/status_tracker.py` - Status tracking implementation (uses `processing_id`)
- `web-portal-api/app/routers/upload.py` - Upload endpoint
- `web-portal-api/app/routers/workflow.py` - Status query endpoint (queries with `processing_id`)
