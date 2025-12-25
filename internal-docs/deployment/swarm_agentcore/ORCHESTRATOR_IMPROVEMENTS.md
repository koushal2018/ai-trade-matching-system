# HTTP Agent Orchestrator - AWS Best Practices Improvements

## Critical Issues Identified

### 1. Architecture Pattern Anti-Pattern
**Current**: Custom sequential orchestration in Python
**Problem**: Reinventing AWS Step Functions functionality
**Impact**: Higher maintenance, no visual workflow, manual state management

**Recommended Solution**: Migrate to AWS Step Functions Express Workflows

```json
{
  "Comment": "Trade Matching Orchestration",
  "StartAt": "PDFAdapter",
  "States": {
    "PDFAdapter": {
      "Type": "Task",
      "Resource": "arn:aws:states:::bedrock:invokeAgent",
      "Parameters": {
        "AgentId.$": "$.pdf_adapter_arn",
        "Input.$": "$.document_path"
      },
      "Retry": [{
        "ErrorEquals": ["States.TaskFailed"],
        "IntervalSeconds": 1,
        "MaxAttempts": 3,
        "BackoffRate": 2.0
      }],
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "ExceptionManagement"
      }],
      "Next": "TradeExtraction"
    },
    "TradeExtraction": {
      "Type": "Task",
      "Resource": "arn:aws:states:::bedrock:invokeAgent",
      "Parameters": {
        "AgentId.$": "$.trade_extraction_arn",
        "Input.$": "$.pdf_result"
      },
      "Next": "TradeMatching"
    },
    "TradeMatching": {
      "Type": "Task",
      "Resource": "arn:aws:states:::bedrock:invokeAgent",
      "Parameters": {
        "AgentId.$": "$.trade_matching_arn",
        "Input.$": "$.extraction_result"
      },
      "Next": "EvaluateMatch"
    },
    "EvaluateMatch": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.classification",
        "StringMatches": "REVIEW_REQUIRED|BREAK",
        "Next": "ExceptionManagement"
      }],
      "Default": "Success"
    },
    "ExceptionManagement": {
      "Type": "Task",
      "Resource": "arn:aws:states:::bedrock:invokeAgent",
      "End": true
    },
    "Success": {
      "Type": "Succeed"
    }
  }
}
```

**Benefits**:
- Visual workflow in AWS Console
- Built-in retry/error handling
- Automatic state persistence
- CloudWatch integration
- Lower cost (pay per execution)

**AWS Reference**: 
- [Step Functions Best Practices](https://docs.aws.amazon.com/step-functions/latest/dg/bp-express.html)
- [Bedrock Agent Integration](https://docs.aws.amazon.com/step-functions/latest/dg/connect-bedrock.html)

---

### 2. Security: Hardcoded ARNs with Account ID Exposure

**Current** (Lines 44-47):
```python
PDF_ADAPTER_ARN = os.getenv("PDF_ADAPTER_AGENT_ARN", 
    "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/...")
```

**Problem**: 
- Account ID `401552979575` exposed in code
- ARNs hardcoded as fallback values
- No rotation mechanism

**Recommended Solution**: Use AWS Systems Manager Parameter Store

```python
import boto3
from functools import lru_cache

@lru_cache(maxsize=None)
def get_agent_arns() -> Dict[str, str]:
    """Fetch agent ARNs from Parameter Store with caching."""
    ssm = boto3.client('ssm', region_name=REGION)
    
    parameter_names = [
        '/agentcore/agents/pdf-adapter/arn',
        '/agentcore/agents/trade-extraction/arn',
        '/agentcore/agents/trade-matching/arn',
        '/agentcore/agents/exception-management/arn'
    ]
    
    response = ssm.get_parameters(
        Names=parameter_names,
        WithDecryption=False
    )
    
    return {
        'pdf_adapter': next(
            (p['Value'] for p in response['Parameters'] 
             if 'pdf-adapter' in p['Name']), None
        ),
        'trade_extraction': next(
            (p['Value'] for p in response['Parameters'] 
             if 'trade-extraction' in p['Name']), None
        ),
        # ... etc
    }

# Usage
agent_arns = get_agent_arns()
```

**Terraform to create parameters**:
```hcl
resource "aws_ssm_parameter" "pdf_adapter_arn" {
  name  = "/agentcore/agents/pdf-adapter/arn"
  type  = "String"
  value = aws_bedrock_agentcore_runtime.pdf_adapter.arn
  
  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```

**AWS Reference**: [Parameter Store Best Practices](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-best-practices.html)

---

### 3. Observability: Missing AWS X-Ray Integration

**Current**: Basic logging only
**Problem**: No distributed tracing across agents

**Recommended Solution**: Add AWS X-Ray SDK

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Patch all supported libraries (httpx, boto3, etc.)
patch_all()

class AgentCoreClient:
    async def invoke_agent(self, runtime_arn: str, payload: Dict) -> Dict:
        """Invoke agent with X-Ray tracing."""
        
        # Create subsegment for agent invocation
        with xray_recorder.in_subsegment(f'invoke_{agent_name}') as subsegment:
            subsegment.put_annotation('agent_arn', runtime_arn)
            subsegment.put_annotation('correlation_id', correlation_id)
            subsegment.put_metadata('payload_size_kb', len(body) / 1024)
            
            try:
                response = await client.post(url, headers=signed_headers, content=body)
                
                subsegment.put_annotation('status_code', response.status_code)
                subsegment.put_metadata('response_time_ms', attempt_time_ms)
                
                return response.json()
            except Exception as e:
                subsegment.put_annotation('error', str(e))
                raise
```

**Benefits**:
- End-to-end trace visualization
- Automatic service map generation
- Performance bottleneck identification
- Error rate tracking per agent

**AWS Reference**: [X-Ray SDK for Python](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-python.html)

---

### 4. Error Handling: Improve Retry Logic

**Current** (Lines 200-250):
```python
backoff_seconds = 1.0 * (attempt + 1)  # Linear backoff
await asyncio.sleep(backoff_seconds)
```

**Problem**: Linear backoff without jitter causes thundering herd

**Recommended Solution**: Exponential backoff with jitter (AWS SDK pattern)

```python
import random

def calculate_backoff_with_jitter(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 30.0
) -> float:
    """
    Calculate exponential backoff with full jitter.
    
    AWS SDK pattern: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
    """
    exponential_delay = min(max_delay, base_delay * (2 ** attempt))
    jittered_delay = random.uniform(0, exponential_delay)
    return jittered_delay

# Usage in retry loop
for attempt in range(retries):
    try:
        response = await client.post(...)
        if response.status_code >= 500 and attempt < retries - 1:
            backoff = calculate_backoff_with_jitter(attempt)
            logger.info(f"Retrying after {backoff:.2f}s (attempt {attempt + 1})")
            await asyncio.sleep(backoff)
            continue
```

**AWS Reference**: [Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

---

### 5. Performance: Add Circuit Breaker Pattern

**Problem**: No circuit breaker for failing agents
**Impact**: Cascading failures, wasted resources

**Recommended Solution**: Implement circuit breaker

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Circuit breaker for agent invocations."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
    
    def can_execute(self) -> bool:
        """Check if request can proceed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout expired
            if datetime.utcnow() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        
        # HALF_OPEN state
        return self.half_open_calls < self.half_open_max_calls
    
    def record_success(self):
        """Record successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
        self.failure_count = 0
    
    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage in AgentCoreClient
class AgentCoreClient:
    def __init__(self):
        self.circuit_breakers = {
            'pdf_adapter': CircuitBreaker(),
            'trade_extraction': CircuitBreaker(),
            'trade_matching': CircuitBreaker(),
            'exception_management': CircuitBreaker()
        }
    
    async def invoke_agent(self, runtime_arn: str, ...) -> Dict:
        agent_name = self._extract_agent_name(runtime_arn)
        circuit = self.circuit_breakers.get(agent_name)
        
        if circuit and not circuit.can_execute():
            return {
                "success": False,
                "error": f"Circuit breaker OPEN for {agent_name}",
                "circuit_state": circuit.state.value
            }
        
        try:
            result = await self._do_invoke(runtime_arn, ...)
            if circuit:
                circuit.record_success()
            return result
        except Exception as e:
            if circuit:
                circuit.record_failure()
            raise
```

**AWS Reference**: [Reliability Pillar - Circuit Breaker](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html)

---

### 6. Testing: Add Integration Tests

**Current**: No automated tests for orchestrator
**Problem**: Manual testing only, no CI/CD validation

**Recommended Solution**: Add pytest integration tests

```python
# tests/integration/test_http_orchestrator.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from deployment.swarm_agentcore.http_agent_orchestrator import (
    TradeMatchingHTTPOrchestrator
)

@pytest.fixture
def mock_agent_responses():
    """Mock successful agent responses."""
    return {
        'pdf_adapter': {
            'success': True,
            'agent_response': 'Extracted text from PDF',
            'canonical_output_location': 's3://bucket/extracted/BANK/doc.json'
        },
        'trade_extraction': {
            'success': True,
            'trade_id': '26933659',
            'agent_response': 'Extracted trade data'
        },
        'trade_matching': {
            'success': True,
            'match_classification': 'MATCHED',
            'confidence_score': 95
        }
    }

@pytest.mark.asyncio
async def test_successful_orchestration(mock_agent_responses):
    """Test successful end-to-end orchestration."""
    orchestrator = TradeMatchingHTTPOrchestrator()
    
    # Mock agent invocations
    with patch.object(
        orchestrator.client, 
        'invoke_agent', 
        new_callable=AsyncMock
    ) as mock_invoke:
        # Configure mock to return different responses per agent
        mock_invoke.side_effect = [
            mock_agent_responses['pdf_adapter'],
            mock_agent_responses['trade_extraction'],
            mock_agent_responses['trade_matching']
        ]
        
        result = await orchestrator.process_trade_confirmation(
            document_path='s3://bucket/BANK/test.pdf',
            source_type='BANK',
            document_id='test_doc',
            correlation_id='test_corr'
        )
        
        assert result['success'] is True
        assert result['match_classification'] == 'MATCHED'
        assert result['confidence_score'] == 95
        assert len(result['workflow_steps']) == 3
        assert mock_invoke.call_count == 3

@pytest.mark.asyncio
async def test_extraction_failure_triggers_exception_management():
    """Test that extraction failure routes to exception management."""
    orchestrator = TradeMatchingHTTPOrchestrator()
    
    with patch.object(
        orchestrator.client,
        'invoke_agent',
        new_callable=AsyncMock
    ) as mock_invoke:
        mock_invoke.side_effect = [
            {'success': True, 'agent_response': 'PDF extracted'},
            {'success': False, 'error': 'Extraction failed'},
            {'success': True, 'exception_logged': True}  # Exception mgmt
        ]
        
        result = await orchestrator.process_trade_confirmation(
            document_path='s3://bucket/BANK/test.pdf',
            source_type='BANK',
            document_id='test_doc',
            correlation_id='test_corr'
        )
        
        assert result['success'] is False
        assert 'exception_management' in result['workflow_steps']
```

**Run tests**:
```bash
pytest tests/integration/test_http_orchestrator.py -v
```

---

## Summary of Improvements

| Issue | Current State | Recommended Solution | Priority |
|-------|--------------|---------------------|----------|
| Architecture | Custom orchestration | AWS Step Functions | 🔴 High |
| Security | Hardcoded ARNs | Parameter Store | 🔴 High |
| Observability | Basic logging | AWS X-Ray | 🟡 Medium |
| Error Handling | Linear backoff | Exponential + jitter | 🟡 Medium |
| Resilience | No circuit breaker | Circuit breaker pattern | 🟡 Medium |
| Testing | Manual only | Automated integration tests | 🟢 Low |

## Implementation Priority

1. **Immediate** (This Sprint):
   - Move ARNs to Parameter Store
   - Add local testing script (✅ Created)
   - Add integration tests

2. **Short-term** (Next Sprint):
   - Implement exponential backoff with jitter
   - Add AWS X-Ray tracing
   - Add circuit breaker pattern

3. **Long-term** (Future):
   - Migrate to AWS Step Functions
   - Add comprehensive monitoring dashboard
   - Implement A2A protocol for agent communication

## References

- [AWS Step Functions Best Practices](https://docs.aws.amazon.com/step-functions/latest/dg/bp-express.html)
- [AWS Well-Architected Framework - Reliability](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html)
- [Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [AWS X-Ray Developer Guide](https://docs.aws.amazon.com/xray/latest/devguide/aws-xray.html)
- [Bedrock AgentCore Runtime Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-invoke-agent.html)
