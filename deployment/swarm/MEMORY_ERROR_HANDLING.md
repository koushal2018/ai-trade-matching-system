# Memory Error Handling Documentation

## Overview

This document describes the error handling implementation for AgentCore Memory operations in the Trade Matching Swarm. The error handling system ensures that memory service failures do not interrupt the core trade processing workflow.

## Components

### 1. MemoryFallbackHandler

A comprehensive error handler that implements:

- **Retry Logic with Exponential Backoff**: Automatically retries failed operations with increasing delays
- **Circuit Breaker Pattern**: Prevents cascading failures by temporarily disabling memory operations after repeated failures
- **Graceful Fallback**: Allows the system to continue operating without memory when the service is unavailable
- **Comprehensive Logging**: Tracks all memory operations for monitoring and debugging

#### Configuration

```python
handler = MemoryFallbackHandler(
    max_retries=3,                      # Number of retry attempts
    backoff_factor=2.0,                 # Exponential backoff multiplier
    circuit_breaker_threshold=5,        # Failures before opening circuit
    circuit_breaker_reset_timeout=60.0  # Seconds before attempting to close circuit
)
```

#### Usage

```python
from memory_error_handling import get_fallback_handler

handler = get_fallback_handler()

def risky_memory_operation():
    # Memory operation that might fail
    return session_manager.retrieve(query="...")

result = handler.execute_with_fallback(
    risky_memory_operation,
    operation_name="retrieve_patterns"
)

if result is None:
    # Operation failed or circuit breaker is open
    # Continue without memory
    pass
```

#### Circuit Breaker States

1. **Closed (Normal)**: All operations execute normally
2. **Open (Failure Mode)**: Operations are skipped, returns None immediately
3. **Half-Open (Recovery)**: After timeout, attempts to close circuit on next success

### 2. create_session_manager_safe()

Safe wrapper for session manager creation that handles initialization failures gracefully.

#### Features

- Catches `ValueError` for missing/invalid configuration
- Catches generic exceptions for network/service issues
- Returns `None` instead of raising exceptions
- Logs all errors with context

#### Usage

```python
from memory_error_handling import create_session_manager_safe

session_manager = create_session_manager_safe(
    agent_name="pdf_adapter",
    document_id="doc_123",
    memory_id="mem_abc",
    actor_id="trade_matching_system",
    region_name="us-east-1"
)

if session_manager is None:
    # Failed to create session manager
    # Agent will operate without memory
    logger.warning("Operating without memory integration")
```

### 3. retrieve_with_timeout()

Async function that implements timeout handling for memory retrieval operations.

#### Features

- Configurable timeout (default: 2.0 seconds)
- Returns `None` on timeout
- Handles both async and sync retrieval methods
- Comprehensive error logging

#### Usage

```python
import asyncio
from memory_error_handling import retrieve_with_timeout

async def get_patterns():
    results = await retrieve_with_timeout(
        session_manager=session_manager,
        query="extraction patterns",
        namespace="/facts/{actorId}",
        timeout_seconds=2.0
    )
    
    if results is None:
        # Timeout or error occurred
        # Continue without historical context
        return []
    
    return results

# Run async function
results = asyncio.run(get_patterns())
```

### 4. store_pattern_safe()

Safe wrapper for storing patterns to memory that prevents storage failures from interrupting processing.

#### Features

- Catches all exceptions during storage
- Returns boolean success indicator
- Logs failures with context
- Allows processing to continue on failure

#### Usage

```python
from memory_error_handling import store_pattern_safe

pattern = {
    "field": "notional",
    "extraction_technique": "regex_pattern",
    "success_rate": 0.95
}

success = store_pattern_safe(
    session_manager=session_manager,
    pattern=pattern,
    namespace="/facts/{actorId}"
)

if not success:
    logger.warning("Pattern not stored - continuing without memory update")
# Processing continues regardless of storage success
```

## Integration with Trade Matching Swarm

The error handling is integrated into the swarm at multiple levels:

### Session Manager Creation

```python
def create_agent_session_manager(
    agent_name: str,
    document_id: str,
    memory_id: str = None,
    actor_id: str = "trade_matching_system",
    region_name: str = "us-east-1"
) -> Optional[AgentCoreMemorySessionManager]:
    """Create session manager with fallback handling."""
    
    fallback_handler = get_fallback_handler()
    
    def _create_session_manager():
        # Session manager creation logic
        ...
    
    try:
        return fallback_handler.execute_with_fallback(
            _create_session_manager,
            operation_name=f"create_session_manager_{agent_name}"
        )
    except Exception as e:
        logger.error(f"Failed to create session manager: {e}")
        return None
```

### Agent Creation

Each agent factory function uses the safe session manager creation:

```python
def create_pdf_adapter_agent(document_id: str, memory_id: str = None) -> Agent:
    """Create PDF Adapter agent with memory integration."""
    
    # Session manager creation with error handling
    session_manager = create_agent_session_manager(
        agent_name="pdf_adapter",
        document_id=document_id,
        memory_id=memory_id
    )
    
    # Agent is created with session_manager (may be None)
    return Agent(
        name="pdf_adapter",
        model=create_bedrock_model(),
        system_prompt=get_pdf_adapter_prompt(),
        tools=[...],
        session_manager=session_manager  # None if memory unavailable
    )
```

## Error Scenarios and Handling

### Scenario 1: Memory Service Unavailable

**Symptoms**: Connection timeouts, service errors

**Handling**:
1. Retry with exponential backoff (3 attempts)
2. If all retries fail, increment circuit breaker counter
3. After threshold (5 failures), open circuit breaker
4. All subsequent operations skip memory access
5. After timeout (60s), attempt to close circuit

**Impact**: Agents continue processing without historical context

### Scenario 2: Invalid Memory Configuration

**Symptoms**: Missing `AGENTCORE_MEMORY_ID`, invalid memory ID

**Handling**:
1. `create_session_manager_safe()` catches `ValueError`
2. Logs error with context
3. Returns `None` instead of raising
4. Agent operates without memory

**Impact**: No memory integration, but processing continues

### Scenario 3: Memory Retrieval Timeout

**Symptoms**: Slow memory queries, network latency

**Handling**:
1. `retrieve_with_timeout()` enforces 2-second timeout
2. Returns `None` on timeout
3. Logs timeout event
4. Agent continues without historical context for this query

**Impact**: Single query fails, but processing continues

### Scenario 4: Memory Storage Failure

**Symptoms**: Storage errors, quota exceeded, network issues

**Handling**:
1. `store_pattern_safe()` catches all exceptions
2. Logs error with pattern details
3. Returns `False` to indicate failure
4. Processing continues without storing pattern

**Impact**: Pattern not stored, but trade processing completes

## Monitoring and Observability

### Log Messages

All error handling functions emit structured log messages:

```python
# Success
logger.info("Successfully created session manager for pdf_adapter")

# Retry
logger.info("Retrying memory_operation in 2.0s...")

# Circuit Breaker
logger.error("Circuit breaker opened after 5 failures. Will retry after 60s")

# Fallback
logger.warning("Circuit breaker open - executing without memory")

# Timeout
logger.warning("Memory retrieval timed out after 2.0s")

# Storage Failure
logger.error("Failed to store pattern to /facts/{actorId}: Network error")
```

### Metrics

The `MemoryFallbackHandler` provides status information:

```python
handler = get_fallback_handler()
status = handler.get_status()

# Returns:
# {
#     "circuit_breaker_open": False,
#     "circuit_breaker_failures": 2,
#     "circuit_breaker_opened_at": None,
#     "max_retries": 3,
#     "backoff_factor": 2.0,
#     "circuit_breaker_threshold": 5
# }
```

## Testing

### Unit Tests

Run the comprehensive unit test suite:

```bash
pytest deployment/swarm/test_memory_error_handling.py -v
```

### Validation Script

Run the simple validation script (no pytest required):

```bash
python deployment/swarm/validate_error_handling.py
```

### Manual Testing

Test circuit breaker behavior:

```python
from memory_error_handling import MemoryFallbackHandler

handler = MemoryFallbackHandler(max_retries=1, circuit_breaker_threshold=2)

def always_fails():
    raise Exception("Test failure")

# Trigger failures to open circuit
for i in range(3):
    result = handler.execute_with_fallback(always_fails, operation_name=f"test_{i}")
    print(f"Attempt {i+1}: {result}, Circuit open: {handler.circuit_breaker_open}")
```

## Best Practices

1. **Always use safe wrappers**: Use `create_session_manager_safe()`, `retrieve_with_timeout()`, and `store_pattern_safe()` instead of direct calls

2. **Check for None**: Always check if session manager or retrieval results are `None` before using them

3. **Log appropriately**: Use appropriate log levels (ERROR for failures, WARNING for fallbacks, INFO for success)

4. **Monitor circuit breaker**: Track circuit breaker status in production to identify persistent memory issues

5. **Set reasonable timeouts**: Balance between allowing slow operations and preventing blocking (default 2s is reasonable)

6. **Handle None gracefully**: Design agents to work without memory when it's unavailable

## Requirements Validation

This implementation validates the following requirements:

- **18.1**: Memory operations are logged for monitoring
- **18.2**: Retrieval latency is logged and tracked
- **18.3**: Relevance scores are logged for analysis
- **18.4**: Detailed error information is logged
- **18.5**: Metrics can be emitted to CloudWatch (via logging integration)

## Future Enhancements

1. **Adaptive Timeouts**: Adjust timeout based on historical latency
2. **Metrics Export**: Direct CloudWatch metrics integration
3. **Health Checks**: Periodic memory service health checks
4. **Graceful Degradation**: Partial memory access when some namespaces fail
5. **Retry Strategies**: Different retry strategies for different error types
