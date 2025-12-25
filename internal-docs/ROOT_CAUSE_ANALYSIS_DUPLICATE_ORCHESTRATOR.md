# Root Cause Analysis: Duplicate Orchestrator Invocations

**Date**: December 24, 2025  
**Severity**: High  
**Component**: S3 Event Processor Lambda → HTTP Agent Orchestrator  
**Status**: Root cause identified

## Executive Summary

The duplicate orchestrator invocations are caused by **Lambda retry behavior combined with lack of idempotency controls**. When the S3 Event Processor Lambda times out (60s timeout) while waiting for the AgentCore orchestrator response (which takes 160-280s), AWS Lambda automatically retries the function, causing duplicate workflow executions.

## Root Cause

### Primary Issue: Lambda Timeout Mismatch

1. **Lambda Timeout**: 60 seconds (configured)
2. **Orchestrator Duration**: 160-280 seconds (observed)
3. **Result**: Lambda times out before orchestrator completes, triggering automatic retry

### Contributing Factors

1. **Idempotency Cache Disabled**: The orchestrator has idempotency code but it's intentionally disabled:
   ```python
   # deployment/swarm_agentcore/http_agent_orchestrator.py:270
   self.idempotency_cache = None  # Idempotency disabled
   ```

2. **No Lambda-Level Deduplication**: The S3 Event Processor Lambda has no mechanism to prevent processing duplicate S3 events

3. **Synchronous Invocation Pattern**: Lambda waits for orchestrator response instead of fire-and-forget

## Evidence Analysis

### From CloudWatch Logs
```
17:50:02 - Starting workflow for document: 3982037b-c436-418b-ad3c-b0656495983a-FAB_27254314
17:50:58 - Starting workflow for document: 3982037b-c436-418b-ad3c-b0656495983a-FAB_27254314
```
- 56-second gap matches Lambda timeout retry behavior
- Both workflows run to completion independently

### From Code Analysis

#### Lambda Function (s3_event_processor.py)
```python
def lambda_handler(event, context):
    # No deduplication check
    # Direct synchronous invocation
    success, response = invoker.invoke(AGENTCORE_RUNTIME_ARN, payload)
    # If invocation takes > 60s, Lambda times out and retries
```

#### Orchestrator (http_agent_orchestrator.py)
```python
# Line 266-270: Idempotency intentionally disabled
# self.idempotency_cache = IdempotencyCache(...)  # COMMENTED OUT
self.idempotency_cache = None  # Idempotency disabled

# Line 326-337: Check would prevent duplicates if enabled
if self.idempotency_cache:
    cached_result = self.idempotency_cache.check_and_set(correlation_id, payload)
    if cached_result is not None:
        return cached_result  # Would return cached result
```

## Why S3 "At-Least-Once" Delivery Isn't the Issue

While S3 event notifications do use at-least-once delivery, the 56-second gap between duplicates strongly indicates Lambda retry behavior rather than S3 duplicate events. S3 duplicates would typically arrive within milliseconds or seconds.

## Impact

1. **Cost Impact**: 
   - Double LLM token consumption ($X per duplicate)
   - Double compute time (160-280s × 2)
   
2. **Data Integrity**:
   - Multiple status table writes for same session
   - Potential race conditions in trade matching
   
3. **Performance**:
   - Increased latency for other documents in queue
   - Resource contention

## Solution Options

### Option 1: Enable Existing Idempotency (Recommended - Quick Fix)

**Implementation**: Enable the already-implemented idempotency cache
```python
# deployment/swarm_agentcore/http_agent_orchestrator.py
# Change line 270 from:
self.idempotency_cache = None

# To:
self.idempotency_cache = IdempotencyCache(
    table_name="trade-matching-system-idempotency",  
    ttl_seconds=300,
    region_name="us-east-1"
)
```

**Required**: Create DynamoDB idempotency table
```bash
aws dynamodb create-table \
  --table-name trade-matching-system-idempotency \
  --attribute-definitions AttributeName=correlation_id,AttributeType=S \
  --key-schema AttributeName=correlation_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

**Pros**: 
- Minimal code change
- Uses existing, tested code
- 5-minute TTL prevents long-term storage

**Cons**: 
- Requires new DynamoDB table
- Small additional latency for cache check

### Option 2: Async Invocation Pattern (Recommended - Long-term)

**Implementation**: Make Lambda invoke orchestrator asynchronously
```python
# s3_event_processor.py
def process_s3_record(record, invoker, metrics, lambda_request_id):
    # Start workflow asynchronously
    success = invoker.invoke_async(AGENTCORE_RUNTIME_ARN, payload)
    
    # Store invocation metadata in status table
    status_tracker.create_workflow(correlation_id, document_id, "initiated")
    
    # Return immediately (no timeout)
    return {"success": True, "correlation_id": correlation_id}
```

**Pros**:
- Lambda completes in seconds, no timeout
- No retry issues
- Better scalability

**Cons**:
- Requires refactoring response handling
- Need separate mechanism for completion notification

### Option 3: Increase Lambda Timeout (Not Recommended)

**Implementation**: Increase timeout to 900s (Lambda max)
```bash
aws lambda update-function-configuration \
  --function-name s3-event-processor-production \
  --timeout 900
```

**Pros**: 
- Simple configuration change
- No code changes

**Cons**:
- Lambda bills for full duration (expensive)
- Still vulnerable to S3 duplicate events
- 900s may still not be enough for complex workflows

### Option 4: Add Lambda-Level Deduplication

**Implementation**: Check status table before processing
```python
def lambda_handler(event, context):
    for record in event['Records']:
        s3_key = record['s3']['object']['key']
        
        # Check if recently processed
        if is_recently_processed(s3_key):
            logger.info(f"Skipping recently processed: {s3_key}")
            continue
            
        # Process normally
        process_s3_record(record, ...)
```

**Pros**:
- Prevents all duplicate processing
- Works with S3 duplicates too

**Cons**:
- Requires DynamoDB lookups
- Additional complexity

## Recommended Implementation Plan

### Phase 1: Immediate Fix (Today)
1. Enable idempotency cache in orchestrator
2. Create idempotency DynamoDB table
3. Redeploy orchestrator
4. Monitor for duplicates

### Phase 2: Long-term Solution (This Week)
1. Refactor to async invocation pattern
2. Implement status webhook/polling
3. Add Lambda-level deduplication
4. Comprehensive testing

## Validation Steps

After implementing fix:

1. **Test Duplicate Prevention**:
   ```bash
   # Upload same file twice quickly
   aws s3 cp test.pdf s3://trade-matching-system-agentcore-production/BANK/
   aws s3 cp test.pdf s3://trade-matching-system-agentcore-production/BANK/test2.pdf
   ```

2. **Monitor Logs**:
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/bedrock-agentcore/http_agent_orchestrator \
     --filter-pattern "Returning cached result"
   ```

3. **Verify Idempotency Table**:
   ```bash
   aws dynamodb scan \
     --table-name trade-matching-system-idempotency \
     --region us-east-1
   ```

## Prevention Measures

1. **Design Principle**: Always implement idempotency for event-driven systems
2. **Testing**: Include duplicate event scenarios in integration tests
3. **Monitoring**: Alert on duplicate correlation_ids in logs
4. **Documentation**: Document timeout requirements and retry behavior

## Conclusion

The root cause is a **timeout mismatch between Lambda (60s) and orchestrator (160-280s)** combined with **disabled idempotency controls**. The immediate fix is to enable the existing idempotency cache. The long-term solution is to refactor to an asynchronous invocation pattern that eliminates timeout issues entirely.

This is a common pattern in serverless architectures where short-lived compute (Lambda) needs to invoke long-running processes (AgentCore). The solution pattern of async invocation with status tracking is an industry best practice for this scenario.