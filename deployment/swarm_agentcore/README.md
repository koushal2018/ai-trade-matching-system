# Trade Matching Swarm - AgentCore Runtime Deployment

This directory contains the AgentCore Runtime deployment package for the Trade Matching Swarm with memory integration.

## Overview

The Trade Matching Swarm is deployed as a serverless agent on Amazon Bedrock AgentCore Runtime, enabling:
- **Serverless Scalability**: Automatic scaling based on load
- **Memory Integration**: Learning from past trade processing patterns using AgentCore Memory
- **Multi-Agent Orchestration**: Four specialized agents that autonomously collaborate
- **AWS Service Integration**: Direct access to S3, DynamoDB, and Bedrock

## Directory Structure

```
deployment/swarm_agentcore/
├── trade_matching_swarm_agentcore.py  # AgentCore entrypoint
├── trade_matching_swarm.py            # Swarm implementation with memory
├── aws_resources.py                   # Shared AWS client configuration
├── memory_error_handling.py           # Memory fallback and error handling
├── agentcore.yaml                     # AgentCore deployment configuration
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

## Prerequisites

Before deploying, ensure you have:

1. **AgentCore Memory Resource**: Created using the setup script
   ```bash
   python deployment/setup_memory.py
   ```
   This will output a memory ID that you'll need for deployment.

2. **AWS Resources**: DynamoDB tables and S3 bucket configured
   - BankTradeData table
   - CounterpartyTradeData table
   - ExceptionsTable table
   - S3 bucket for document storage

3. **Environment Variables**: Set the following:
   ```bash
   export AGENTCORE_MEMORY_ID=<your-memory-id>
   export S3_BUCKET_NAME=trade-matching-system-agentcore-production
   export DYNAMODB_BANK_TABLE=BankTradeData
   export DYNAMODB_COUNTERPARTY_TABLE=CounterpartyTradeData
   export DYNAMODB_EXCEPTIONS_TABLE=ExceptionsTable
   ```

## Deployment

### Step 1: Configure the Agent

```bash
cd deployment/swarm_agentcore
agentcore configure --name trade-matching-swarm
```

This will:
- Validate the agentcore.yaml configuration
- Set up the agent in AgentCore Runtime
- Configure environment variables

### Step 2: Deploy the Agent

```bash
agentcore launch --agent-name trade-matching-swarm
```

This will:
- Package the Python code and dependencies
- Deploy to AgentCore Runtime
- Provision serverless infrastructure
- Output the agent endpoint URL

### Step 3: Verify Deployment

```bash
agentcore status --agent-name trade-matching-swarm
```

Check that the agent status is "ACTIVE" and ready to receive requests.

## Usage

### Invoke via AgentCore Runtime

```python
import boto3

agentcore_client = boto3.client('bedrock-agentcore-runtime', region_name='us-east-1')

response = agentcore_client.invoke_agent(
    agentName='trade-matching-swarm',
    payload={
        'document_path': 's3://bucket/BANK/trade.pdf',
        'source_type': 'BANK',
        'document_id': 'trade_123',
        'correlation_id': 'corr_123'
    }
)

result = response['result']
print(f"Success: {result['success']}")
print(f"Status: {result['status']}")
```

### Invoke via CLI (for testing)

```bash
python trade_matching_swarm_agentcore.py
```

This will run a local test with the test payload defined in the `__main__` block.

## Configuration

### agentcore.yaml

The deployment configuration includes:

- **Runtime**: Python 3.11
- **Timeout**: 600 seconds (10 minutes)
- **Memory**: 2048 MB (2GB)
- **Dependencies**: Strands SDK, AgentCore Memory, boto3, pydantic

### Environment Variables

Required:
- `AGENTCORE_MEMORY_ID`: Memory resource ID for pattern storage
- `S3_BUCKET_NAME`: S3 bucket for document storage
- `DYNAMODB_BANK_TABLE`: Bank trades table name
- `DYNAMODB_COUNTERPARTY_TABLE`: Counterparty trades table name
- `DYNAMODB_EXCEPTIONS_TABLE`: Exceptions table name

Optional:
- `ACTOR_ID`: Actor identifier (default: trade_matching_system)
- `AWS_REGION`: AWS region (default: us-east-1)
- `BEDROCK_MODEL_ID`: Model ID (default: amazon.nova-pro-v1:0)

## Memory Integration

The swarm uses AgentCore Memory with three built-in strategies:

1. **Semantic Memory** (`/facts/{actorId}`):
   - Trade processing patterns
   - Field extraction techniques
   - Matching decisions
   - Exception resolutions

2. **User Preferences** (`/preferences/{actorId}`):
   - OCR quality preferences
   - Extraction thresholds
   - Matching tolerances
   - Severity classifications

3. **Session Summaries** (`/summaries/{actorId}/{sessionId}`):
   - Trade processing summaries
   - Agent handoff history
   - Key decisions made

Each agent has its own session manager with a unique session ID, but all agents share the same memory resource for cross-agent learning.

## Agent Architecture

The swarm consists of four specialized agents:

1. **PDF Adapter** (`pdf_adapter`):
   - Downloads PDFs from S3
   - Extracts text using Bedrock multimodal
   - Saves canonical output
   - Hands off to trade_extractor

2. **Trade Extraction** (`trade_extractor`):
   - Reads canonical output
   - Extracts structured trade data
   - Stores in DynamoDB
   - Hands off to trade_matcher

3. **Trade Matching** (`trade_matcher`):
   - Scans both DynamoDB tables
   - Matches by attributes (not Trade_ID)
   - Calculates confidence scores
   - Hands off to exception_handler if needed

4. **Exception Handler** (`exception_handler`):
   - Analyzes exceptions
   - Determines severity
   - Calculates SLA deadlines
   - Stores exception records

## Error Handling

The deployment includes robust error handling:

- **Memory Fallback**: Continues without memory if service fails
- **Circuit Breaker**: Prevents cascading failures
- **Retry Logic**: Exponential backoff for transient errors
- **Graceful Degradation**: Core functionality maintained even without memory

## Monitoring

AgentCore Runtime provides built-in observability:

- **Metrics**: Invocation count, duration, errors
- **Logs**: CloudWatch Logs integration
- **Traces**: X-Ray tracing for request flow
- **Memory Usage**: Memory operation metrics

Access logs via:
```bash
agentcore logs --agent-name trade-matching-swarm --tail
```

## Troubleshooting

### Agent fails to deploy

Check:
- All environment variables are set correctly
- Memory resource exists and is accessible
- IAM permissions are configured
- Dependencies are compatible

### Memory operations fail

Check:
- AGENTCORE_MEMORY_ID is correct
- Memory resource is in the same region
- IAM role has memory access permissions
- Circuit breaker hasn't opened (check logs)

### Swarm execution times out

Check:
- PDF size (large PDFs take longer)
- DynamoDB table size (scanning large tables is slow)
- Network connectivity to AWS services
- Timeout configuration (increase if needed)

## Updates and Maintenance

### Update the Agent

After making code changes:

```bash
agentcore launch --agent-name trade-matching-swarm --update
```

This performs a zero-downtime update.

### View Agent Status

```bash
agentcore status --agent-name trade-matching-swarm
```

### Delete the Agent

```bash
agentcore delete --agent-name trade-matching-swarm
```

## Related Documentation

- [Requirements Document](../../.kiro/specs/swarm-to-agentcore/requirements.md)
- [Design Document](../../.kiro/specs/swarm-to-agentcore/design.md)
- [Implementation Tasks](../../.kiro/specs/swarm-to-agentcore/tasks.md)
- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Strands SDK Documentation](https://github.com/awslabs/strands-agents)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review AgentCore logs: `agentcore logs --agent-name trade-matching-swarm`
3. Verify memory resource status
4. Check AWS service health dashboard


## Testing

### Running Tests

**Important**: Test scripts are located in the **project root** (`../../`), not in this directory.

#### Option 1: Use the Local Test Runner

From this directory:

```bash
bash run_tests.sh
```

This script navigates to the project root and runs all tests.

#### Option 2: Navigate to Root First

```bash
# Go to project root
cd ../..

# Run all tests
bash run_all_swarm_agentcore_tests.sh
```

#### Option 3: Run Individual Tests

From project root:

```bash
# Property tests (in root directory)
python test_property_1_memory_storage_consistency.py
python test_property_2_memory_retrieval_relevance.py
python test_property_3_session_id_format.py
python test_property_4_functional_parity.py
python test_property_5_memory_configuration.py
python test_property_6_agentcore_runtime_scaling.py

# Unit tests (in deployment/swarm_agentcore/)
python deployment/swarm_agentcore/test_memory_resource_creation.py
python deployment/swarm_agentcore/test_session_manager_creation.py
python deployment/swarm_agentcore/test_agent_creation.py
python deployment/swarm_agentcore/test_error_handling.py

# Integration tests (in deployment/swarm_agentcore/)
python deployment/swarm_agentcore/test_integration_trade_processing.py
python deployment/swarm_agentcore/test_integration_memory_persistence.py

# Performance tests (in deployment/swarm_agentcore/)
python deployment/swarm_agentcore/test_performance_memory_retrieval.py
python deployment/swarm_agentcore/test_performance_agentcore_scaling.py
```

### Test Behavior

Tests are designed to **gracefully skip** when prerequisites are not met:
- Without `AGENTCORE_MEMORY_ID`: Tests skip with informative messages
- Without AgentCore deployment: Scaling tests skip gracefully
- Without AWS credentials: Tests skip or use fallback behavior

This is **expected behavior** - the system degrades gracefully when resources are unavailable.

See `../../HOW_TO_RUN_TESTS.md` for detailed testing instructions.

## Documentation

Complete documentation is available:

- **DEPLOYMENT_GUIDE.md**: Step-by-step deployment instructions
- **MEMORY_CONFIGURATION_GUIDE.md**: Memory setup and configuration
- **TROUBLESHOOTING_GUIDE.md**: Common issues and solutions
- **CLI_COMMAND_EXAMPLES.md**: Example CLI commands
- **INTEGRATION_TESTS_GUIDE.md**: Integration testing guide
- **PERFORMANCE_TESTS_GUIDE.md**: Performance testing guide
- **QUICK_TEST_GUIDE.md**: Quick reference for running tests

## Project Status

✅ **All tasks complete** - The swarm-to-agentcore migration is fully implemented and tested.

See `TASK_14_FINAL_CHECKPOINT_COMPLETE.md` in the project root for complete status.
