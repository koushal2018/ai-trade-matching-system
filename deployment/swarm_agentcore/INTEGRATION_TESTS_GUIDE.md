# Integration Tests Guide

## Overview

This guide explains how to run and interpret the integration tests for the Trade Matching Swarm with AgentCore Memory integration.

## Test Files

### test_integration_trade_processing.py

Tests complete trade processing workflow with memory integration.

**Tests**:
- `test_complete_trade_processing_with_memory`: Full workflow test
- `test_memory_infrastructure_availability`: Infrastructure validation

**Validates**: Requirements 2.2, 2.3, 2.4, 3.1-3.5, 4.1-4.5, 5.1-5.5, 6.1-6.5

### test_integration_memory_persistence.py

Tests memory persistence across different sessions.

**Tests**:
- `test_memory_persistence_across_sessions`: Cross-session persistence
- `test_namespace_retrieval_configs`: Configuration validation
- `test_multiple_agents_share_memory`: Multi-agent memory sharing

**Validates**: Requirements 2.2, 2.3, 2.4

## Prerequisites

### Required Environment Variables

```bash
# Required for tests to run
export AGENTCORE_MEMORY_ID=<your-memory-resource-id>

# Optional (have defaults)
export ACTOR_ID=trade_matching_system
export AWS_REGION=us-east-1
```

### AWS Configuration

Ensure AWS credentials are configured:
```bash
aws configure
# or
export AWS_ACCESS_KEY_ID=<your-key>
export AWS_SECRET_ACCESS_KEY=<your-secret>
```

### Python Dependencies

```bash
pip install pytest bedrock-agentcore[strands-agents] strands boto3
```

## Running Tests

### Run All Integration Tests

```bash
python -m pytest deployment/swarm_agentcore/test_integration_*.py -v -s
```

### Run Specific Test File

```bash
# Trade processing tests
python -m pytest deployment/swarm_agentcore/test_integration_trade_processing.py -v -s

# Memory persistence tests
python -m pytest deployment/swarm_agentcore/test_integration_memory_persistence.py -v -s
```

### Run Specific Test

```bash
python -m pytest deployment/swarm_agentcore/test_integration_trade_processing.py::test_memory_infrastructure_availability -v -s
```

### Run with Verbose Output

```bash
python -m pytest deployment/swarm_agentcore/test_integration_*.py -v -s --log-cli-level=DEBUG
```

## Test Behavior

### With AGENTCORE_MEMORY_ID Set

Tests will execute and verify:
- Session manager creation for all agents
- Memory configuration correctness
- Session isolation and memory sharing
- Namespace retrieval configurations

### Without AGENTCORE_MEMORY_ID

Tests will skip with message:
```
SKIPPED (AGENTCORE_MEMORY_ID not set - memory integration tests require memory resource)
```

This is expected behavior for environments without memory resources.

## Understanding Test Output

### Successful Test Run

```
test_integration_trade_processing.py::test_complete_trade_processing_with_memory PASSED
test_integration_trade_processing.py::test_memory_infrastructure_availability PASSED
test_integration_memory_persistence.py::test_memory_persistence_across_sessions PASSED
test_integration_memory_persistence.py::test_namespace_retrieval_configs PASSED
test_integration_memory_persistence.py::test_multiple_agents_share_memory PASSED

====== 5 passed in 2.34s ======
```

### Skipped Tests

```
test_integration_trade_processing.py::test_complete_trade_processing_with_memory SKIPPED
test_integration_memory_persistence.py::test_memory_persistence_across_sessions SKIPPED

====== 2 skipped in 0.52s ======
```

### Failed Test

```
test_integration_trade_processing.py::test_memory_infrastructure_availability FAILED

AssertionError: Session manager configuration verification failed
```

Check logs for detailed error information.

## What Tests Verify

### Infrastructure Verification

✅ Session managers can be created for all agents
✅ Session IDs follow correct format
✅ Memory resource ID is set correctly
✅ Actor ID enables cross-agent learning
✅ Retrieval configs match specifications

### Configuration Verification

✅ Three namespaces configured (facts, preferences, summaries)
✅ Correct top_k values (10, 5, 5)
✅ Correct relevance scores (0.6, 0.7, 0.5)
✅ All agents share same memory resource
✅ Each agent has unique session ID

### Cross-Session Verification

✅ Sessions are isolated (different session IDs)
✅ Sessions share memory (same memory ID)
✅ Sessions enable learning (same actor ID)
✅ Configuration is consistent across sessions

## Troubleshooting

### Tests Skip Immediately

**Problem**: Tests skip with "AGENTCORE_MEMORY_ID not set"

**Solution**: Set the environment variable:
```bash
export AGENTCORE_MEMORY_ID=<your-memory-id>
```

To get a memory ID, run:
```bash
python deployment/swarm_agentcore/setup_memory.py
```

### Session Manager Creation Fails

**Problem**: "Failed to create session manager"

**Possible Causes**:
1. Invalid memory ID
2. AWS credentials not configured
3. Insufficient permissions
4. Memory resource not in correct region

**Solution**:
```bash
# Verify memory resource exists
aws bedrock-agent-runtime get-memory --memory-id $AGENTCORE_MEMORY_ID --region us-east-1

# Check AWS credentials
aws sts get-caller-identity
```

### Configuration Verification Fails

**Problem**: "Session ID format incorrect" or "Missing retrieval config"

**Possible Causes**:
1. Code changes broke session manager creation
2. Retrieval config not properly set

**Solution**: Review `create_agent_session_manager()` function in `trade_matching_swarm.py`

### Import Errors

**Problem**: "ModuleNotFoundError: No module named 'bedrock_agentcore'"

**Solution**:
```bash
pip install bedrock-agentcore[strands-agents]
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
      
      - name: Run integration tests
        env:
          AGENTCORE_MEMORY_ID: ${{ secrets.AGENTCORE_MEMORY_ID }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1
        run: |
          python -m pytest deployment/swarm_agentcore/test_integration_*.py -v
```

## Local Testing Workflow

### 1. Create Memory Resource

```bash
cd deployment/swarm_agentcore
python setup_memory.py
# Copy the memory ID from output
export AGENTCORE_MEMORY_ID=<memory-id>
```

### 2. Run Integration Tests

```bash
python -m pytest test_integration_*.py -v -s
```

### 3. Test with Real Data

```bash
python test_local.py \
  --document-path data/BANK/FAB_26933659.pdf \
  --source-type BANK
```

### 4. Deploy to AgentCore

```bash
./deploy_agentcore.sh
```

## Test Maintenance

### Adding New Tests

1. Create test function with descriptive name
2. Add pytest fixtures for dependencies
3. Include comprehensive docstring
4. Reference validated requirements
5. Add to this guide

### Updating Tests

When updating memory configuration:
1. Update `create_agent_session_manager()` in `trade_matching_swarm.py`
2. Update expected values in tests
3. Update this guide
4. Run tests to verify changes

## Best Practices

### Test Isolation

- Each test uses unique document IDs
- Tests don't depend on each other
- Tests clean up after themselves (when applicable)

### Test Documentation

- Clear docstrings explaining purpose
- Requirements references
- Expected outcomes documented

### Error Handling

- Tests skip gracefully when dependencies missing
- Clear error messages for failures
- Detailed logging for debugging

## Related Documentation

- [TASK_11_INTEGRATION_TESTS_SUMMARY.md](../../TASK_11_INTEGRATION_TESTS_SUMMARY.md): Complete implementation summary
- [test_local.py](test_local.py): Local testing script
- [setup_memory.py](setup_memory.py): Memory resource creation
- [README.md](README.md): Deployment guide

## Support

For issues or questions:
1. Check test output logs
2. Review this guide
3. Check related documentation
4. Verify environment configuration
5. Test with `test_local.py` for manual validation

---

**Last Updated**: 2025-12-14
**Version**: 1.0
