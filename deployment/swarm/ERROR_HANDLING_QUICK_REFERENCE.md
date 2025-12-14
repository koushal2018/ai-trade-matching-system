# Memory Error Handling - Quick Reference

## Import

```python
from memory_error_handling import (
    MemoryFallbackHandler,
    get_fallback_handler,
    create_session_manager_safe,
    retrieve_with_timeout,
    store_pattern_safe
)
```

## Common Patterns

### 1. Create Session Manager Safely

```python
session_manager = create_session_manager_safe(
    agent_name="pdf_adapter",
    document_id="doc_123",
    memory_id="mem_abc"
)

if session_manager is None:
    # Memory unavailable - continue without it
    logger.warning("Operating without memory")
```

### 2. Retrieve with Timeout

```python
import asyncio

async def get_patterns():
    results = await retrieve_with_timeout(
        session_manager=session_manager,
        query="extraction patterns",
        namespace="/facts/{actorId}",
        timeout_seconds=2.0
    )
    
    if results is None:
        # Timeout or error - use defaults
        return []
    
    return results

# Run async
results = asyncio.run(get_patterns())
```

### 3. Store Pattern Safely

```python
pattern = {
    "field": "notional",
    "technique": "regex",
    "success_rate": 0.95
}

success = store_pattern_safe(
    session_manager=session_manager,
    pattern=pattern,
    namespace="/facts/{actorId}"
)

# Continue regardless of success
if not success:
    logger.warning("Pattern not stored")
```

### 4. Use Fallback Handler Directly

```python
handler = get_fallback_handler()

def risky_operation():
    # Your memory operation
    return session_manager.some_operation()

result = handler.execute_with_fallback(
    risky_operation,
    operation_name="my_operation"
)

if result is None:
    # Operation failed or circuit open
    pass
```

### 5. Check Circuit Breaker Status

```python
handler = get_fallback_handler()
status = handler.get_status()

print(f"Circuit open: {status['circuit_breaker_open']}")
print(f"Failures: {status['circuit_breaker_failures']}")
```

### 6. Manual Circuit Reset

```python
handler = get_fallback_handler()
handler.reset_circuit_breaker()
```

## Configuration

### Default Values

```python
MemoryFallbackHandler(
    max_retries=3,                      # Retry attempts
    backoff_factor=2.0,                 # Exponential backoff
    circuit_breaker_threshold=5,        # Failures before open
    circuit_breaker_reset_timeout=60.0  # Seconds before retry
)
```

### Custom Configuration

```python
handler = MemoryFallbackHandler(
    max_retries=5,
    backoff_factor=1.5,
    circuit_breaker_threshold=10,
    circuit_breaker_reset_timeout=120.0
)
```

## Error Scenarios

| Scenario | Handler | Result | Impact |
|----------|---------|--------|--------|
| Service unavailable | Retry + Circuit breaker | None | Continue without memory |
| Invalid config | Catch ValueError | None | No memory integration |
| Slow retrieval | Timeout | None | Skip this query |
| Storage failure | Catch exception | False | Pattern not stored |

## Logging Levels

```python
# Success
logger.info("Successfully created session manager")

# Retry
logger.info("Retrying operation in 2.0s...")

# Circuit breaker
logger.error("Circuit breaker opened")

# Fallback
logger.warning("Executing without memory")

# Timeout
logger.warning("Memory retrieval timed out")

# Storage failure
logger.error("Failed to store pattern")
```

## Testing

### Run pytest tests
```bash
pytest deployment/swarm/test_memory_error_handling.py -v
```

### Run validation script
```bash
python deployment/swarm/validate_error_handling.py
```

## Best Practices

1. ✅ Always check for `None` before using results
2. ✅ Use safe wrappers instead of direct calls
3. ✅ Log appropriately (ERROR/WARNING/INFO)
4. ✅ Design agents to work without memory
5. ✅ Monitor circuit breaker status in production
6. ✅ Set reasonable timeouts (default 2s is good)

## Common Mistakes

1. ❌ Not checking for `None` results
2. ❌ Raising exceptions on memory failures
3. ❌ Blocking on slow memory operations
4. ❌ Not logging memory errors
5. ❌ Assuming memory is always available

## Quick Troubleshooting

### Circuit breaker keeps opening
- Check memory service health
- Increase circuit breaker threshold
- Increase retry attempts
- Check network connectivity

### Timeouts occurring frequently
- Increase timeout value
- Check memory service performance
- Optimize query complexity
- Check network latency

### Patterns not being stored
- Check storage permissions
- Check memory quota
- Check namespace configuration
- Review error logs

## Environment Variables

```bash
# Required for memory integration
export AGENTCORE_MEMORY_ID=mem_abc123

# Optional
export AWS_REGION=us-east-1
export ACTOR_ID=trade_matching_system
```

## Documentation

- Full documentation: `MEMORY_ERROR_HANDLING.md`
- Completion summary: `TASK_5_COMPLETION_SUMMARY.md`
- This quick reference: `ERROR_HANDLING_QUICK_REFERENCE.md`
