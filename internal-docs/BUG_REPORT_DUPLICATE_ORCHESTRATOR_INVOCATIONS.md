# Bug Report: Duplicate Orchestrator Invocations for Same Document

**Date**: December 24, 2025  
**Severity**: High  
**Component**: S3 Event Processor Lambda / Orchestrator AgentCore Runtime  
**Status**: ✅ RESOLVED

## Resolution Summary

**Root Cause**: Lambda timeout (60s) < orchestrator duration (160-280s) caused AWS Lambda to retry, triggering duplicate workflow executions.

**Fix Applied** (December 24, 2025):
1. Enabled the existing idempotency cache in `http_agent_orchestrator.py`
2. Created DynamoDB table `trade-matching-system-idempotency` with TTL enabled
3. Cache entries auto-expire after 5 minutes (300s)

**Verification**: Redeploy orchestrator and test with duplicate uploads.

---

## Summary

The orchestrator agent is being invoked multiple times for the same document upload, causing duplicate processing, wasted compute/tokens, and potential data inconsistencies.

## Evidence from Logs

Same document `3982037b-c436-418b-ad3c-b0656495983a-FAB_27254314` processed multiple times:

```
17:50:02 - [corr_61c8d7e876e9] Starting trade confirmation workflow - Document ID: 3982037b-c436-418b-ad3c-b0656495983a-FAB_27254314
17:50:58 - [corr_61c8d7e876e9] Starting trade confirmation workflow - Document ID: 3982037b-c436-418b-ad3c-b0656495983a-FAB_27254314
```

Both workflows run in parallel:
- First completes at 17:52:42 (160s)
- Second completes at 17:53:53 (175s)

## Impact

1. **Wasted Resources**: Each duplicate run costs ~160-175 seconds of AgentCore compute
2. **Wasted Tokens**: Each run consumes LLM tokens (PDF extraction, trade extraction, matching)
3. **Data Inconsistency**: Multiple writes to DynamoDB status table with same session_id
4. **Potential Race Conditions**: Concurrent updates to trade data tables

## Root Cause Analysis

### Hypothesis 1: S3 Event Delivery Duplicates (MOST LIKELY)
S3 event notifications are "at-least-once" delivery - the same event can be delivered multiple times. The Lambda should implement idempotency but currently doesn't.

### Hypothesis 2: Lambda Retry on Timeout
If the Lambda times out before returning success, AWS retries it. The Lambda timeout is 60s but orchestrator takes 160-280s.

### Hypothesis 3: AgentCore Runtime Retry
The AgentCore runtime may be retrying invocations internally.

## S3 Notification Configuration (Verified Correct)

```json
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:401552979575:function:s3-event-processor-production",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {"Key": {"FilterRules": [
        {"Name": "Prefix", "Value": "BANK/"},
        {"Name": "Suffix", "Value": ".pdf"}
      ]}}
    },
    {
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:401552979575:function:s3-event-processor-production",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {"Key": {"FilterRules": [
        {"Name": "Prefix", "Value": "COUNTERPARTY/"},
        {"Name": "Suffix", "Value": ".pdf"}
      ]}}
    }
  ]
}
```

The S3 filter is correct - only triggers for `BANK/*.pdf` and `COUNTERPARTY/*.pdf`.

## Lambda Configuration

- **Function**: `s3-event-processor-production`
- **Timeout**: 60 seconds (TOO SHORT - orchestrator takes 160-280s)
- **Memory**: 256 MB

## Resolution Options

### Option 1: Implement Idempotency in Lambda (Recommended)
Add DynamoDB-based idempotency check before invoking orchestrator:

```python
def lambda_handler(event, context):
    for record in event['Records']:
        s3_key = record['s3']['object']['key']
        event_id = record['responseElements']['x-amz-request-id']
        
        # Check if already processed
        if is_already_processed(s3_key, event_id):
            logger.info(f"Skipping duplicate event for {s3_key}")
            continue
            
        # Mark as processing
        mark_as_processing(s3_key, event_id)
        
        # Invoke orchestrator asynchronously
        invoke_orchestrator_async(s3_key)
```

### Option 2: Use SQS with Deduplication
Route S3 events through SQS FIFO queue with content-based deduplication:
- S3 → SQS FIFO → Lambda
- Deduplication window: 5 minutes

### Option 3: Increase Lambda Timeout + Async Invocation
- Increase Lambda timeout to 900s (max)
- Or invoke orchestrator asynchronously and return immediately

### Option 4: Add Idempotency in Orchestrator
Check if document already processed before starting workflow:

```python
def process_document(document_id, correlation_id):
    # Check if already processed in last N minutes
    existing = get_recent_processing(document_id, minutes=5)
    if existing and existing['status'] in ['processing', 'completed']:
        logger.info(f"Document {document_id} already being processed")
        return existing
```

## Files to Investigate

1. **Lambda Code**: Check `s3-event-processor-production` source code
2. **Orchestrator**: `deployment/swarm_agentcore/http_agent_orchestrator.py`
3. **Status Tracker**: `deployment/swarm_agentcore/status_tracker.py`

## Immediate Mitigation

Until fixed, manually check for duplicate processing by monitoring:
```bash
aws logs filter-log-events \
  --log-group-name /aws/bedrock-agentcore/http_agent_orchestrator \
  --filter-pattern "Starting trade confirmation workflow" \
  --start-time $(date -d '10 minutes ago' +%s000)
```

## Related Issues

- Lambda timeout (60s) is too short for orchestrator workflow (160-280s)
- No idempotency mechanism in current implementation
- S3 "at-least-once" delivery not handled

---

**Note**: The S3 trigger filter configuration is correct (BANK/ and COUNTERPARTY/ only). The issue is duplicate event delivery, not incorrect filtering.
