# Logging Improvements - HTTP Agent Orchestrator

**Date**: December 21, 2025  
**Component**: Trade Matching HTTP Orchestrator  
**Status**: ✅ Comprehensive Logging Implemented

---

## Summary of Changes

Enhanced logging across the HTTP Agent Orchestrator to provide complete observability for production debugging, performance monitoring, and security auditing.

### 1. Dockerfile Enhancements

**File**: `deployment/swarm_agentcore/.bedrock_agentcore/Dockerfile`

Added OpenTelemetry configuration environment variables:

```dockerfile
ENV OTEL_PYTHON_LOG_CORRELATION=true \
    OTEL_PYTHON_LOG_LEVEL=info \
    OTEL_TRACES_EXPORTER=otlp \
    OTEL_METRICS_EXPORTER=otlp
```

**Benefits**:
- ✅ Automatic correlation of logs with traces
- ✅ Structured log export to CloudWatch
- ✅ Distributed tracing across agent invocations
- ✅ Metrics collection for performance monitoring

---

### 2. HTTP Agent Invocation Logging

**File**: `deployment/swarm_agentcore/http_agent_orchestrator.py`

**Method**: `AgentCoreClient.invoke_agent()`

#### Added Logging Points:

1. **Request Initialization**
   ```python
   logger.info(f"[{correlation_id}] INFO: Invoking agent '{agent_name}'")
   logger.info(f"[{correlation_id}] INFO: Agent ARN: ...{runtime_arn[-40:]}")
   logger.info(f"[{correlation_id}] INFO: Endpoint: {self.endpoint}")
   logger.info(f"[{correlation_id}] INFO: Timeout: {timeout}s, Max retries: {retries}")
   logger.debug(f"[{correlation_id}] DEBUG: Payload: {json.dumps(payload)[:200]}...")
   logger.debug(f"[{correlation_id}] DEBUG: Request body size: {body_size_kb:.2f} KB")
   ```

2. **SigV4 Signing**
   ```python
   logger.debug(f"[{correlation_id}] DEBUG: Signing request with SigV4")
   logger.debug(f"[{correlation_id}] DEBUG: Request signed in {signing_time_ms:.2f}ms")
   ```

3. **HTTP Request/Response**
   ```python
   logger.info(f"[{correlation_id}] INFO: Attempt {attempt + 1}/{retries} - calling agent")
   logger.info(f"[{correlation_id}] INFO: Response status: {response.status_code}")
   logger.info(f"[{correlation_id}] INFO: Response time: {attempt_time_ms:.2f}ms")
   logger.debug(f"[{correlation_id}] DEBUG: Response size: {response_size_kb:.2f} KB")
   ```

4. **Success Logging**
   ```python
   logger.info(f"[{correlation_id}] INFO: Agent returned success={result.get('success')}")
   logger.debug(f"[{correlation_id}] DEBUG: Response keys: {list(result.keys())}")
   ```

5. **Error Logging**
   ```python
   logger.error(f"[{correlation_id}] ERROR: Agent returned {response.status_code}")
   logger.error(f"[{correlation_id}] ERROR: Response: {error_text}")
   logger.error(f"[{correlation_id}] ERROR: Attempt {attempt + 1}/{retries} failed")
   ```

6. **Retry Logic**
   ```python
   logger.warning(f"[{correlation_id}] WARN: Retrying after {backoff_seconds}s backoff")
   logger.debug(f"[{correlation_id}] DEBUG: Re-signing request for retry")
   ```

7. **Timeout Handling**
   ```python
   logger.error(f"[{correlation_id}] ERROR: Timeout on attempt {attempt + 1}/{retries}")
   logger.error(f"[{correlation_id}] ERROR: Elapsed time: {attempt_time_ms:.2f}ms")
   logger.error(f"[{correlation_id}] ERROR: Timeout threshold: {timeout}s")
   ```

8. **Exception Handling**
   ```python
   logger.error(f"[{correlation_id}] ERROR: Request failed on attempt {attempt + 1}/{retries}")
   logger.error(f"[{correlation_id}] ERROR: Exception type: {type(e).__name__}")
   logger.error(f"[{correlation_id}] ERROR: Exception message: {e}")
   logger.error(f"[{correlation_id}] ERROR: Elapsed time: {attempt_time_ms:.2f}ms")
   ```

---

### 3. Workflow Orchestration Logging

**Method**: `TradeMatchingHTTPOrchestrator.process_trade_confirmation()`

#### Added Logging Points:

1. **Workflow Start**
   ```python
   logger.info(f"[{correlation_id}] ========================================")
   logger.info(f"[{correlation_id}] INFO: Starting trade confirmation workflow")
   logger.info(f"[{correlation_id}] INFO: Document ID: {document_id}")
   logger.info(f"[{correlation_id}] INFO: Source Type: {source_type}")
   logger.info(f"[{correlation_id}] INFO: Document Path: {document_path}")
   logger.info(f"[{correlation_id}] ========================================")
   ```

2. **Step-by-Step Progress**
   ```python
   logger.info(f"[{correlation_id}] INFO: Step 1/4: PDF Adapter Agent")
   logger.info(f"[{correlation_id}] INFO: Extracting text from PDF document")
   logger.info(f"[{correlation_id}] INFO: PDF Adapter completed in {step_time_ms:.2f}ms")
   logger.info(f"[{correlation_id}] INFO: PDF Adapter success: {pdf_result.get('success')}")
   ```

3. **Trade ID Extraction**
   ```python
   logger.info(f"[{correlation_id}] INFO: Extracted trade_id: {trade_id}")
   if trade_id != document_id:
       logger.info(f"[{correlation_id}] INFO: Trade ID differs from document ID")
       logger.debug(f"[{correlation_id}] DEBUG: Document ID: {document_id}")
       logger.debug(f"[{correlation_id}] DEBUG: Trade ID: {trade_id}")
   ```

4. **Matching Results**
   ```python
   logger.info(f"[{correlation_id}] INFO: Match classification: {classification}")
   logger.info(f"[{correlation_id}] INFO: Confidence score: {confidence_score}%")
   ```

5. **Exception Handling Decision**
   ```python
   logger.info(f"[{correlation_id}] INFO: Classification requires exception handling: {classification}")
   logger.info(f"[{correlation_id}] INFO: Reason codes: {reason_codes}")
   ```

6. **Workflow Completion**
   ```python
   logger.info(f"[{correlation_id}] ========================================")
   logger.info(f"[{correlation_id}] INFO: Workflow completed successfully")
   logger.info(f"[{correlation_id}] INFO: Total processing time: {processing_time_ms:.2f}ms")
   logger.info(f"[{correlation_id}] INFO: Steps executed: {len(workflow_steps)}")
   logger.info(f"[{correlation_id}] INFO: Final classification: {classification}")
   logger.info(f"[{correlation_id}] ========================================")
   ```

7. **Workflow Errors**
   ```python
   logger.error(f"[{correlation_id}] ========================================")
   logger.error(f"[{correlation_id}] ERROR: Workflow failed at step: {current_step}")
   logger.error(f"[{correlation_id}] ERROR: Exception type: {type(e).__name__}")
   logger.error(f"[{correlation_id}] ERROR: Exception message: {e}")
   logger.error(f"[{correlation_id}] ========================================", exc_info=True)
   ```

---

## Log Level Usage

### INFO Level
- Workflow progress and milestones
- Agent invocation start/completion
- Success/failure status
- Performance metrics (timing)
- Classification results

### DEBUG Level
- Request/response payloads (truncated)
- Request body sizes
- SigV4 signing details
- Detailed timing breakdowns
- Internal state transitions

### WARN Level
- Retry attempts
- Recoverable errors
- Configuration issues
- Missing optional parameters

### ERROR Level
- Agent invocation failures
- HTTP errors (4xx, 5xx)
- Timeout exceptions
- Workflow failures
- Validation errors

---

## Correlation ID Tracking

Every log message includes the correlation ID in the format:
```
[{correlation_id}] LEVEL: Message
```

**Benefits**:
- ✅ End-to-end request tracing
- ✅ Easy filtering in CloudWatch Logs Insights
- ✅ Cross-agent correlation
- ✅ Debugging multi-step workflows

**Example CloudWatch Query**:
```sql
fields @timestamp, @message
| filter @message like /\[corr_abc123\]/
| sort @timestamp asc
```

---

## Performance Metrics Logged

1. **Request Signing Time**: Time to sign HTTP requests with SigV4
2. **Agent Response Time**: Time for each agent invocation
3. **Step Time**: Time for each workflow step
4. **Total Processing Time**: End-to-end workflow time
5. **Retry Backoff Time**: Time spent in retry delays

**Example Log Output**:
```
2025-12-21T10:30:15 - [corr_abc123] INFO: Request signed in 12.34ms
2025-12-21T10:30:18 - [corr_abc123] INFO: Response time: 2345.67ms
2025-12-21T10:30:18 - [corr_abc123] INFO: PDF Adapter completed in 2358.01ms
2025-12-21T10:30:25 - [corr_abc123] INFO: Total processing time: 10234.56ms
```

---

## Size Metrics Logged

1. **Request Body Size**: Size of payload sent to agents
2. **Response Size**: Size of response received from agents

**Example Log Output**:
```
2025-12-21T10:30:15 - [corr_abc123] DEBUG: Request body size: 2.45 KB
2025-12-21T10:30:18 - [corr_abc123] DEBUG: Response size: 15.67 KB
```

---

## Error Context Logged

For every error, the following context is captured:

1. **Error Type**: Exception class name
2. **Error Message**: Full error message (truncated to 500 chars)
3. **Attempt Number**: Which retry attempt failed
4. **Elapsed Time**: Time spent before failure
5. **HTTP Status Code**: For HTTP errors
6. **Stack Trace**: Full stack trace for exceptions (via `exc_info=True`)

**Example Error Log**:
```
2025-12-21T10:30:20 - [corr_abc123] ERROR: Request failed on attempt 2/3
2025-12-21T10:30:20 - [corr_abc123] ERROR: Exception type: ConnectionError
2025-12-21T10:30:20 - [corr_abc123] ERROR: Exception message: Connection refused
2025-12-21T10:30:20 - [corr_abc123] ERROR: Elapsed time: 5234.56ms
```

---

## CloudWatch Logs Integration

### Log Groups
- **AgentCore Runtime**: `/aws/bedrock-agentcore/trade-matching-http-orchestrator`
- **OpenTelemetry Traces**: Exported to AWS X-Ray
- **Metrics**: Exported to CloudWatch Metrics

### Useful CloudWatch Insights Queries

#### 1. Find All Errors for a Correlation ID
```sql
fields @timestamp, @message
| filter @message like /\[corr_abc123\]/ and @message like /ERROR/
| sort @timestamp asc
```

#### 2. Calculate Average Processing Time
```sql
fields @timestamp, @message
| filter @message like /Total processing time/
| parse @message /processing time: (?<time_ms>[\d.]+)ms/
| stats avg(time_ms) as avg_time_ms, max(time_ms) as max_time_ms, min(time_ms) as min_time_ms
```

#### 3. Count Errors by Type
```sql
fields @timestamp, @message
| filter @message like /ERROR: Exception type/
| parse @message /Exception type: (?<error_type>\w+)/
| stats count() by error_type
```

#### 4. Track Retry Attempts
```sql
fields @timestamp, @message
| filter @message like /WARN: Retrying/
| parse @message /Retrying after (?<backoff>[\d.]+)s/
| stats count() as retry_count, sum(backoff) as total_backoff_seconds
```

#### 5. Monitor Agent Performance
```sql
fields @timestamp, @message
| filter @message like /completed in/
| parse @message /(?<agent>\w+) completed in (?<time_ms>[\d.]+)ms/
| stats avg(time_ms) as avg_time_ms by agent
```

---

## Security Considerations

### What's Logged
- ✅ Correlation IDs
- ✅ Document IDs
- ✅ Trade IDs
- ✅ Agent ARNs (last 40 chars)
- ✅ HTTP status codes
- ✅ Error messages (truncated)
- ✅ Performance metrics

### What's NOT Logged
- ❌ Full agent ARNs (only last 40 chars)
- ❌ AWS credentials
- ❌ Full request/response payloads (only first 200 chars in DEBUG)
- ❌ PII data (redacted by AgentCore Observability)
- ❌ Sensitive trade details

### PII Redaction
AgentCore Observability automatically redacts PII when `pii_redaction: true` is configured:
```yaml
observability:
  enabled: true
  pii_redaction: true
```

---

## Testing Logging

### 1. Test with Sample Request
```bash
# Deploy the orchestrator
cd deployment/swarm_agentcore
agentcore deploy

# Invoke with test payload
python -c "
import asyncio
from http_agent_orchestrator import TradeMatchingHTTPOrchestrator

async def test():
    orchestrator = TradeMatchingHTTPOrchestrator()
    result = await orchestrator.process_trade_confirmation(
        document_path='s3://bucket/BANK/test.pdf',
        source_type='BANK',
        document_id='test_123',
        correlation_id='test_corr_123'
    )
    print(result)

asyncio.run(test())
"
```

### 2. View Logs in CloudWatch
```bash
# Tail logs
aws logs tail /aws/bedrock-agentcore/trade-matching-http-orchestrator --follow

# Filter by correlation ID
aws logs filter-log-events \
  --log-group-name /aws/bedrock-agentcore/trade-matching-http-orchestrator \
  --filter-pattern "[corr_test_corr_123]"
```

### 3. Check OpenTelemetry Traces
```bash
# View traces in AWS X-Ray Console
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --filter-expression 'service("trade_matching_http_orchestrator")'
```

---

## Monitoring Recommendations

### 1. Create CloudWatch Alarms

**High Error Rate**:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name http-orchestrator-high-error-rate \
  --alarm-description "Alert when error rate exceeds 10%" \
  --metric-name ErrorRate \
  --namespace TradeMatching/HTTPOrchestrator \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

**High Latency**:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name http-orchestrator-high-latency \
  --alarm-description "Alert when p99 latency exceeds 30s" \
  --metric-name ProcessingTimeMs \
  --namespace TradeMatching/HTTPOrchestrator \
  --statistic p99 \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 30000 \
  --comparison-operator GreaterThanThreshold
```

### 2. Create CloudWatch Dashboard

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["TradeMatching/HTTPOrchestrator", "ProcessingTimeMs", {"stat": "Average"}],
          ["...", {"stat": "p99"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Processing Time"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/bedrock-agentcore/trade-matching-http-orchestrator' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20",
        "region": "us-east-1",
        "title": "Recent Errors"
      }
    }
  ]
}
```

---

## Benefits of Enhanced Logging

### 1. Debugging
- ✅ Trace requests end-to-end with correlation IDs
- ✅ Identify which agent failed and why
- ✅ See exact error messages and stack traces
- ✅ Understand retry behavior

### 2. Performance Monitoring
- ✅ Track processing time per agent
- ✅ Identify slow agents
- ✅ Monitor timeout occurrences
- ✅ Analyze retry patterns

### 3. Security Auditing
- ✅ Track all agent invocations
- ✅ Monitor authentication failures
- ✅ Detect unusual patterns
- ✅ Compliance reporting

### 4. Operational Excellence
- ✅ Proactive alerting on errors
- ✅ Capacity planning with metrics
- ✅ SLA monitoring
- ✅ Cost optimization insights

---

## Next Steps

1. **Deploy Updated Code**
   ```bash
   cd deployment/swarm_agentcore
   agentcore deploy
   ```

2. **Verify Logging**
   - Check CloudWatch Logs for structured output
   - Verify correlation IDs appear in all logs
   - Test error scenarios to ensure proper logging

3. **Set Up Monitoring**
   - Create CloudWatch alarms for errors and latency
   - Build CloudWatch dashboard for visualization
   - Configure SNS notifications for critical alerts

4. **Document Runbooks**
   - Create troubleshooting guides using log queries
   - Document common error patterns
   - Train team on log analysis

---

**Status**: ✅ **COMPLETE**  
**Impact**: **HIGH** - Comprehensive observability for production operations  
**Effort**: 2 hours implementation, immediate benefits
