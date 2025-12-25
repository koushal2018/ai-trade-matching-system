# Frontend Status Tracking Testing Guide

## Overview
This guide covers testing the real-time workflow status tracking integration between the orchestrator, web portal backend, and frontend UI.

## Prerequisites

1. ✅ Orchestrator deployed with status tracking
2. ✅ DynamoDB table `trade-matching-system-processing-status` exists
3. ✅ Web portal backend running
4. ✅ Web portal frontend running

## Test Scenarios

### Test 1: Backend API Endpoint

**Test the status query endpoint directly:**

```bash
# Replace SESSION_ID with actual session from orchestrator response
SESSION_ID="session-corr_abc123"

curl http://localhost:8000/api/workflow/${SESSION_ID}/status | jq
```

**Expected Response:**
```json
{
  "sessionId": "session-corr_abc123",
  "agents": {
    "pdfAdapter": {
      "status": "success",
      "activity": "Text extraction complete (Tokens: 14,169)",
      "startedAt": "2025-12-24T10:00:00.000Z",
      "completedAt": "2025-12-24T10:00:05.123Z",
      "duration": 5.123,
      "error": null,
      "subSteps": []
    },
    "tradeExtraction": {...},
    "tradeMatching": {...},
    "exceptionManagement": {...}
  },
  "overallStatus": "completed",
  "lastUpdated": "2025-12-24T10:02:30.456Z"
}
```

### Test 2: Non-Existent Session (Graceful Degradation)

```bash
curl http://localhost:8000/api/workflow/nonexistent-session/status | jq
```

**Expected Response:**
```json
{
  "sessionId": "nonexistent-session",
  "agents": {
    "pdfAdapter": {"status": "pending", "activity": "Waiting for upload"},
    "tradeExtraction": {"status": "pending", "activity": "Waiting for PDF processing"},
    "tradeMatching": {"status": "pending", "activity": "Waiting for extraction"},
    "exceptionManagement": {"status": "pending", "activity": "No exceptions"}
  },
  "overallStatus": "pending",
  "lastUpdated": "2025-12-24T10:00:00.000Z"
}
```

### Test 3: Frontend Real-Time Updates

**Steps:**

1. **Start Web Portal Backend:**
   ```bash
   cd web-portal-api
   uvicorn app.main:app --reload --port 8000
   ```

2. **Start Web Portal Frontend:**
   ```bash
   cd web-portal
   npm run dev
   ```

3. **Upload a Test PDF:**
   - Navigate to: http://localhost:3000
   - Upload a PDF file (BANK or COUNTERPARTY)
   - Note the `sessionId` from the upload response

4. **Watch Real-Time Status Updates:**
   - The UI should show agent progress in real-time
   - Status should update every 30 seconds while processing
   - Token usage should be displayed for completed agents

**Expected UI Behavior:**

```
Initial State:
┌─────────────────────────────────────┐
│ PDF Adapter         ⏳ Pending      │
│ Trade Extraction    ⏳ Pending      │
│ Trade Matching      ⏳ Pending      │
│ Exception Mgmt      ⏳ Pending      │
└─────────────────────────────────────┘

After 30s (PDF Adapter running):
┌─────────────────────────────────────┐
│ PDF Adapter         🔄 In Progress  │
│ Trade Extraction    ⏳ Pending      │
│ Trade Matching      ⏳ Pending      │
│ Exception Mgmt      ⏳ Pending      │
└─────────────────────────────────────┘

After 60s (PDF Adapter complete):
┌─────────────────────────────────────┐
│ PDF Adapter         ✅ Complete     │
│   Tokens: 14,169 | Duration: 5.1s  │
│ Trade Extraction    🔄 In Progress  │
│ Trade Matching      ⏳ Pending      │
│ Exception Mgmt      ⏳ Pending      │
└─────────────────────────────────────┘

Final State (All complete):
┌─────────────────────────────────────┐
│ PDF Adapter         ✅ Complete     │
│   Tokens: 14,169 | Duration: 5.1s  │
│ Trade Extraction    ✅ Complete     │
│   Tokens: 8,234 | Duration: 3.2s   │
│ Trade Matching      ✅ Complete     │
│   Tokens: 12,456 | Duration: 8.5s  │
│ Exception Mgmt      ⏳ Pending      │
└─────────────────────────────────────┘
```

### Test 4: Error Handling

**Trigger an error by uploading an invalid PDF:**

```bash
# Upload a non-existent document
curl -X POST http://localhost:8000/api/upload \
  -F "file=@invalid.pdf" \
  -F "source_type=BANK"
```

**Expected UI Behavior:**
- Agent status should show "error" state
- Error message should be displayed
- Retry option should be available
- Polling should stop

### Test 5: Query DynamoDB Directly

**Verify status is being written correctly:**

```bash
# Get the session ID from orchestrator logs or frontend
SESSION_ID="session-corr_abc123"

aws dynamodb get-item \
  --table-name trade-matching-system-processing-status \
  --key "{\"processing_id\": {\"S\": \"${SESSION_ID}\"}}" \
  --region us-east-1 | jq
```

**Expected Output:**
```json
{
  "Item": {
    "processing_id": {"S": "session-corr_abc123"},
    "sessionId": {"S": "session-corr_abc123"},
    "correlationId": {"S": "corr_abc123"},
    "overallStatus": {"S": "completed"},
    "pdfAdapter": {
      "M": {
        "status": {"S": "success"},
        "activity": {"S": "Text extraction complete"},
        "tokenUsage": {
          "M": {
            "inputTokens": {"N": "11689"},
            "outputTokens": {"N": "2480"},
            "totalTokens": {"N": "14169"}
          }
        }
      }
    },
    "lastUpdated": {"S": "2025-12-24T10:02:30.456Z"}
  }
}
```

## Browser DevTools Testing

### Network Tab
1. Open DevTools → Network tab
2. Upload a PDF
3. Watch for polling requests to `/api/workflow/{sessionId}/status`
4. Verify requests occur every 30 seconds
5. Verify polling stops when `overallStatus` is "completed" or "failed"

### Console Tab
1. Check for any JavaScript errors
2. Verify React Query logs (if debug mode enabled)
3. Check for proper state updates

## Performance Testing

### Polling Efficiency
```javascript
// In browser console, monitor polling behavior
let pollCount = 0;
const originalFetch = window.fetch;
window.fetch = function(...args) {
  if (args[0].includes('/workflow/') && args[0].includes('/status')) {
    pollCount++;
    console.log(`Poll #${pollCount} at ${new Date().toISOString()}`);
  }
  return originalFetch.apply(this, args);
};
```

**Expected:**
- Polls every 30 seconds while processing
- Stops polling when complete
- No excessive polling (< 20 polls for typical workflow)

## Troubleshooting

### Issue: Status Not Updating

**Check:**
1. Backend is running: `curl http://localhost:8000/health`
2. DynamoDB table exists: `aws dynamodb describe-table --table-name trade-matching-system-processing-status`
3. Orchestrator is writing status: Check CloudWatch logs
4. Frontend is polling: Check Network tab in DevTools

**Debug:**
```bash
# Check backend logs
cd web-portal-api
tail -f logs/app.log

# Check orchestrator logs
aws logs tail /aws/bedrock-agentcore/trade_matching_swarm_agentcore_http --follow
```

### Issue: Wrong Table Name

**Verify environment variables:**
```bash
# In orchestrator
echo $STATUS_TABLE_NAME

# In backend
grep STATUS_TABLE web-portal-api/.env
```

### Issue: Permissions Error

**Verify IAM permissions:**
```bash
# Check if backend can read from DynamoDB
aws dynamodb get-item \
  --table-name trade-matching-system-processing-status \
  --key '{"processing_id": {"S": "test"}}' \
  --region us-east-1
```

## Success Criteria

✅ Backend API returns status for existing sessions
✅ Backend API returns pending status for non-existent sessions
✅ Frontend displays real-time agent progress
✅ Token usage is displayed for completed agents
✅ Polling stops when workflow completes
✅ Error states are handled gracefully
✅ No console errors in browser
✅ Status persists in DynamoDB with 90-day TTL

## Next Steps After Testing

1. Monitor production workflows
2. Set up CloudWatch alarms for status write failures
3. Add metrics dashboard for token usage
4. Implement WebSocket for real-time updates (optional)
5. Add status history view in UI

---

**Testing Date**: December 24, 2025
**Tested By**: [Your Name]
**Status**: Ready for Testing
