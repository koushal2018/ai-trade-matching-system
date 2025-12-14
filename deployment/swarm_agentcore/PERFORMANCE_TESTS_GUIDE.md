# Performance Tests Guide

## Overview

This guide explains how to run and interpret the performance tests for AgentCore Memory integration and Runtime scaling.

## Test Files

1. **`test_performance_memory_retrieval.py`** - Memory retrieval latency tests (Requirement 2.5)
2. **`test_performance_agentcore_scaling.py`** - AgentCore Runtime scaling tests (Requirement 1.2)

## Prerequisites

### Environment Variables

```bash
# Required for memory retrieval tests
export AGENTCORE_MEMORY_ID=your-memory-id

# Optional for AgentCore endpoint integration test
export AGENTCORE_ENDPOINT=https://your-agentcore-endpoint

# Standard AWS configuration
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=trade-matching-system-agentcore-production
```

### Dependencies

Ensure you have the required packages installed:

```bash
pip install pytest
pip install bedrock-agentcore[strands-agents]
pip install strands
pip install boto3
```

## Running Tests

### Memory Retrieval Tests

```bash
# Run all memory retrieval tests
python -m pytest deployment/swarm_agentcore/test_performance_memory_retrieval.py -v -s

# Run specific test
python -m pytest deployment/swarm_agentcore/test_performance_memory_retrieval.py::TestMemoryRetrievalPerformance::test_facts_namespace_retrieval_latency -v

# Run with detailed output
python -m pytest deployment/swarm_agentcore/test_performance_memory_retrieval.py -v -s --log-cli-level=INFO
```

### Scaling Tests

```bash
# Run all scaling tests (local simulation)
python -m pytest deployment/swarm_agentcore/test_performance_agentcore_scaling.py -v -s

# Run specific test
python -m pytest deployment/swarm_agentcore/test_performance_agentcore_scaling.py::TestAgentCoreRuntimeScaling::test_response_time_degradation_under_load -v

# Run with AgentCore endpoint integration test
export AGENTCORE_ENDPOINT=https://your-endpoint
python -m pytest deployment/swarm_agentcore/test_performance_agentcore_scaling.py::TestAgentCoreRuntimeScalingIntegration -v -s
```

### Run All Performance Tests

```bash
# Run both test suites
python -m pytest deployment/swarm_agentcore/test_performance_*.py -v -s
```

## Test Descriptions

### Memory Retrieval Tests

| Test | Description | Validates |
|------|-------------|-----------|
| `test_facts_namespace_retrieval_latency` | Tests retrieval from /facts namespace | Req 2.5 |
| `test_preferences_namespace_retrieval_latency` | Tests retrieval from /preferences namespace | Req 2.5 |
| `test_summaries_namespace_retrieval_latency` | Tests retrieval from /summaries namespace | Req 2.5 |
| `test_multiple_sequential_retrievals_latency` | Tests multiple namespace queries | Req 2.5 |
| `test_retrieval_latency_with_complex_query` | Tests complex query performance | Req 2.5 |
| `test_retrieval_latency_percentiles` | Statistical analysis of 20 samples | Req 2.5 |

### Scaling Tests

| Test | Description | Validates |
|------|-------------|-----------|
| `test_baseline_performance` | Establishes baseline with 5 concurrent requests | Req 1.2 |
| `test_scaled_performance` | Tests with 20 concurrent requests | Req 1.2 |
| `test_response_time_degradation_under_load` | Core scaling test (degradation ≤ 2x) | Req 1.2 |
| `test_incremental_load_scaling` | Tests 5, 10, 15, 20 concurrent requests | Req 1.2 |
| `test_sustained_load_performance` | Tests consistency over 3 iterations | Req 1.2 |
| `test_agentcore_endpoint_scaling` | Integration test with real endpoint | Req 1.2 |

## Performance Thresholds

### Memory Retrieval (Requirement 2.5)

- **Maximum Latency**: 500ms per retrieval
- **P95 Target**: < 450ms (90% of threshold)
- **Test Passes If**: All retrievals complete within 500ms

### AgentCore Scaling (Requirement 1.2)

- **Maximum Degradation**: 2.0x under 4x load increase
- **Success Rate**: ≥ 80% under high load
- **Consistency**: Coefficient of variation < 30%
- **Test Passes If**: Response time doesn't more than double under 4x load

## Interpreting Results

### Memory Retrieval Test Output

```
INFO - Retrieval completed in 245.32ms (query: 'trade matching decision...', namespace: /facts/{actorId}, results: 8)
INFO - Latency percentiles over 20 samples:
  Average: 267.45ms
  P50 (median): 255.12ms
  P95: 312.89ms
  P99: 345.67ms
  Max: 356.23ms
```

**Interpretation**:
- ✅ All latencies under 500ms threshold
- ✅ P95 well under threshold (312ms < 450ms)
- ✅ Consistent performance (low variance)

### Scaling Test Output

```
INFO - Response time comparison:
  Baseline (5 concurrent): 1234.56ms
  Scaled (20 concurrent): 2156.78ms
  Degradation factor: 1.75x
  Threshold: 2.00x
```

**Interpretation**:
- ✅ Degradation factor 1.75x < 2.0x threshold
- ✅ System scaled effectively
- ✅ Response time increased by 75% for 4x load (good scaling)

## Troubleshooting

### Test Failures

#### Memory Retrieval Test Fails

**Symptom**: Latency exceeds 500ms

**Possible Causes**:
1. Network latency to AgentCore Memory service
2. Memory resource not properly configured
3. High load on AgentCore Memory service
4. Complex query requiring optimization

**Solutions**:
- Check network connectivity to us-east-1
- Verify memory resource is active
- Reduce query complexity
- Adjust retrieval configuration (top_k, relevance_score)

#### Scaling Test Fails

**Symptom**: Degradation factor > 2.0x

**Possible Causes**:
1. System not scaling (fixed capacity)
2. Resource constraints (CPU, memory)
3. Bottleneck in shared resources
4. Cold start overhead

**Solutions**:
- Verify AgentCore Runtime auto-scaling is enabled
- Check resource limits in agentcore.yaml
- Monitor CloudWatch metrics for scaling events
- Pre-warm instances if cold starts are an issue

### Common Issues

#### AGENTCORE_MEMORY_ID Not Set

```
SKIPPED - AGENTCORE_MEMORY_ID environment variable not set
```

**Solution**: Set the environment variable:
```bash
export AGENTCORE_MEMORY_ID=your-memory-id
```

#### Import Errors

```
ModuleNotFoundError: No module named 'bedrock_agentcore'
```

**Solution**: Install required dependencies:
```bash
pip install bedrock-agentcore[strands-agents]
```

#### Timeout Errors

```
TimeoutError: Memory retrieval timed out after 2.0s
```

**Solution**: This is expected behavior - the test validates timeout handling. If all tests timeout, check network connectivity.

## Performance Monitoring

### Key Metrics to Track

1. **Memory Retrieval**:
   - Average latency per namespace
   - P95 and P99 latencies
   - Query complexity vs latency

2. **AgentCore Scaling**:
   - Response time vs load
   - Throughput (requests/sec)
   - Degradation factor
   - Success rate

### CloudWatch Integration

Monitor these CloudWatch metrics:
- `AgentCore/MemoryRetrievalLatency`
- `AgentCore/RequestCount`
- `AgentCore/ResponseTime`
- `AgentCore/InstanceCount` (scaling indicator)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Tests

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Daily

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r deployment/swarm_agentcore/requirements.txt
          pip install pytest
      
      - name: Run Memory Retrieval Tests
        env:
          AGENTCORE_MEMORY_ID: ${{ secrets.AGENTCORE_MEMORY_ID }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          python -m pytest deployment/swarm_agentcore/test_performance_memory_retrieval.py -v
      
      - name: Run Scaling Tests
        run: |
          python -m pytest deployment/swarm_agentcore/test_performance_agentcore_scaling.py -v
      
      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: performance-results
          path: |
            pytest-report.xml
            performance-metrics.json
```

## Best Practices

1. **Run Regularly**: Schedule performance tests daily or weekly
2. **Track Trends**: Monitor performance over time, not just pass/fail
3. **Set Alerts**: Alert on degradation trends, not just threshold violations
4. **Test in Production-Like Environment**: Use similar load and data patterns
5. **Document Baselines**: Record baseline performance for comparison

## Additional Resources

- [AgentCore Memory Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-memory.html)
- [AgentCore Runtime Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-runtime.html)
- [Performance Testing Best Practices](../PERFORMANCE_TESTING_BEST_PRACTICES.md)

---

**Last Updated**: 2025-12-14
**Requirements**: 1.2, 2.5
