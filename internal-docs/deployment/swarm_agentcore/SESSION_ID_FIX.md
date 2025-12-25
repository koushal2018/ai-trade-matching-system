# Session ID Synchronization Fix - Dec 24, 2025

## Problem

Frontend was not showing agent status updates because:
1. Upload API created `session_id = f"session-{random_uuid}"`
2. Orchestrator created `session_id = f"session-{correlation_id}"`
3. These were **different values**, so frontend couldn't find the status

## Root Cause

Bedrock AgentCore runtime creates its own session_id automatically - we can't control it from the upload API. The upload API and orchestrator were creating independent session IDs with no way to link them.

## Solution

Use `document_id` as the basis for `session_id` in both places:

### Upload API (`web-portal-api/app/routers/upload.py`)
```python
upload_id = str(uuid.uuid4())
session_id = f"session-{upload_id}"  # upload_id becomes document_id
```

The `upload_id` is embedded in the S3 key: `{sourceType}/{upload_id}-{filename}`

### Orchestrator (`deployment/swarm_agentcore/http_agent_orchestrator.py`)
```python
# document_id is extracted from S3 key (contains upload_id)
session_id = f"session-{document_id}"  # Same format as upload API
```

### Status Tracker
Writes to DynamoDB with key `processing_id = session_id`

### Frontend
Queries DynamoDB with `processing_id = session_id` (from upload response)

## Flow

1. User uploads file → Upload API generates `upload_id`
2. Upload API returns `sessionId = f"session-{upload_id}"`
3. File saved to S3 as `{sourceType}/{upload_id}-{filename}`
4. S3 event triggers orchestrator with S3 key
5. Orchestrator extracts `document_id` from S3 key (contains `upload_id`)
6. Orchestrator creates `session_id = f"session-{document_id}"` (same value!)
7. Orchestrator writes status to DynamoDB with `processing_id = session_id`
8. Frontend queries DynamoDB with `processing_id = sessionId` from upload response
9. ✅ Frontend gets real-time status updates!

## Files Changed

- `deployment/swarm_agentcore/http_agent_orchestrator.py` - Use document_id for session_id
- `web-portal-api/app/routers/upload.py` - Use upload_id for session_id
- `deployment/swarm_agentcore/status_tracker.py` - Use processing_id as partition key

## Testing

After redeployment:
1. Upload a file via web portal
2. Note the `sessionId` in the response
3. Check DynamoDB table `trade-matching-system-processing-status`
4. Verify item exists with `processing_id = sessionId`
5. Frontend should show real-time agent status updates

## Notes

- This assumes `document_id` in orchestrator matches `upload_id` from upload API
- If document_id is generated differently, this won't work
- Verify by checking S3 event payload structure
