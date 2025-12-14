# A2A Integration for Trade Matching System

This directory now supports **two execution modes** for the Trade Matching System:

1. **Strands Swarm Mode** (default): Local agents with emergent collaboration
2. **A2A Mode**: Agent-to-Agent communication with deployed AgentCore agents

## Architecture Overview

### Deployed AgentCore Agents

Your production-ready agents:
- **pdf_adapter_agent**: `arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/pdf_adapter_agent-Az72YP53FJ`
- **trade_extraction_agent**: `arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_extraction_agent-KnAx4O4ezw`  
- **trade_matching_agent**: `arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_matching_agent-3aAvK64dQz`
- **exception_manager**: `arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/exception_manager-uliBS5DsX3`

### A2A Workflow

```
A2A Orchestrator → pdf_adapter_agent (Download & Extract)
                → trade_extraction_agent (Parse & Store)  
                → trade_matching_agent (Match & Analyze)
                → exception_manager (Handle Issues)
```

## Quick Start

### 1. Setup Authentication

Run the authentication setup script:

```bash
python setup_a2a_authentication.py
```

This will:
- Create Cognito user pools for authentication
- Generate a bearer token for A2A communication
- Save configuration files for easy access

### 2. Enable A2A Mode

```bash
# Load A2A environment
source setup_a2a_env.sh

# Verify configuration
echo $A2A_MODE          # Should be "true"
echo $AGENTCORE_BEARER_TOKEN  # Should show your token
```

### 3. Test A2A Integration

```bash
# Test connectivity with all agents
python test_a2a_integration.py

# Test with specific document
python a2a_client_integration.py \
  data/BANK/FAB_26933659.pdf \
  --source-type BANK \
  --document-id test_a2a_001 \
  --verbose
```

### 4. Deploy Swarm with A2A Mode

```bash
# Set environment variables for deployment
export A2A_MODE=true
export AGENTCORE_BEARER_TOKEN="$(cat a2a_config.json | jq -r '.bearer_token')"

# Deploy the orchestrator
agentcore deploy

# Test via AgentCore Runtime
agentcore invoke '{
  "document_path": "data/BANK/FAB_26933659.pdf",
  "source_type": "BANK", 
  "document_id": "test_agentcore_001"
}'
```

## File Structure

```
deployment/swarm_agentcore/
├── trade_matching_swarm_agentcore.py    # Main entrypoint (supports both modes)
├── trade_matching_swarm.py              # Strands swarm implementation
├── a2a_client_integration.py            # A2A orchestration logic
├── setup_a2a_authentication.py          # Authentication setup script
├── test_a2a_integration.py              # Integration test suite
├── agentcore.yaml                       # AgentCore deployment config
├── requirements.txt                     # Dependencies (includes A2A)
└── README_A2A_INTEGRATION.md            # This file
```

## Environment Variables

### Required for A2A Mode

```bash
# Enable A2A mode
A2A_MODE=true

# Authentication token for AgentCore agents
AGENTCORE_BEARER_TOKEN=your-bearer-token-here

# Standard AgentCore configuration
AGENTCORE_MEMORY_ID=your-memory-id
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket
DYNAMODB_BANK_TABLE=BankTradeData
DYNAMODB_COUNTERPARTY_TABLE=CounterpartyTradeData
DYNAMODB_EXCEPTIONS_TABLE=ExceptionsTable
```

### Mode Selection

The entrypoint automatically detects the mode based on `A2A_MODE`:

- **A2A_MODE=true**: Uses A2A communication with deployed agents
- **A2A_MODE=false** (default): Uses local Strands swarm

## A2A vs Strands Swarm Comparison

| Aspect | Strands Swarm Mode | A2A Mode |
|--------|-------------------|----------|
| **Execution** | Single AgentCore agent running local swarm | Orchestrator calling separate deployed agents |
| **Communication** | In-memory handoffs | HTTP-based A2A protocol |
| **Scaling** | Single runtime instance | Independent agent scaling |
| **Memory** | Shared session context | Per-agent session isolation |
| **Latency** | Lower (in-memory) | Higher (network calls) |
| **Resilience** | Single point of failure | Distributed resilience |
| **Development** | Easier testing/debugging | More production-like |

## Authentication Setup Details

The authentication uses **Cognito User Pools** with OAuth 2.0:

1. **Runtime Authentication**: Cognito manages user authentication TO your orchestrator
2. **Agent Authentication**: Bearer tokens authenticate orchestrator TO individual agents
3. **Session Management**: Each A2A call uses unique session IDs for isolation

### Manual Authentication Setup

If the automated script fails, you can set up authentication manually:

```bash
# 1. Create Cognito pools
agentcore identity setup-cognito

# 2. Load environment variables
export $(grep -v '^#' .agentcore_identity_user.env | xargs)

# 3. Generate bearer token
BEARER_TOKEN=$(agentcore identity get-cognito-inbound-token)

# 4. Configure for A2A
export A2A_MODE=true
export AGENTCORE_BEARER_TOKEN="$BEARER_TOKEN"
```

## Testing and Validation

### Connectivity Tests

```bash
# Test individual agent connectivity
python test_a2a_integration.py

# Expected output:
# pdf_adapter         ✅ PASS
# trade_extractor     ✅ PASS  
# trade_matcher       ✅ PASS
# exception_handler   ✅ PASS
```

### Workflow Tests

```bash
# Test complete workflow
python a2a_client_integration.py \
  s3://your-bucket/BANK/sample.pdf \
  --source-type BANK \
  --document-id workflow_test_001
```

### AgentCore Deployment Test

```bash
# Deploy with A2A mode
agentcore deploy

# Invoke via AgentCore
agentcore invoke '{
  "document_path": "data/BANK/FAB_26933659.pdf",
  "source_type": "BANK",
  "document_id": "agentcore_test_001"
}'
```

## Error Handling and Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```
   Error: AGENTCORE_BEARER_TOKEN environment variable not set
   ```
   **Solution**: Run `python setup_a2a_authentication.py` or manually set the token

2. **Agent Not Responding**
   ```
   Error: Agent pdf_adapter_agent not responding
   ```
   **Solution**: Check agent status with `agentcore status` in the agent's directory

3. **Token Expired**
   ```
   Error: 401 Unauthorized
   ```
   **Solution**: Regenerate token with `agentcore identity get-cognito-inbound-token`

4. **Missing A2A Dependencies**
   ```
   ModuleNotFoundError: No module named 'a2a'
   ```
   **Solution**: Install with `pip install strands-agents[a2a] httpx`

### Debugging Tips

1. **Enable verbose logging**:
   ```bash
   export PYTHONPATH=.
   python a2a_client_integration.py --verbose ...
   ```

2. **Check agent logs**:
   ```bash
   # Check individual agent logs
   cd /path/to/agent/directory
   aws logs tail /aws/bedrock-agentcore/runtimes/agent-name --follow
   ```

3. **Validate agent status**:
   ```bash
   # Check all agent statuses
   for agent in pdf_adapter trade_extraction trade_matching exception_management; do
     echo "=== $agent ==="
     cd ../deployment/$agent
     agentcore status
   done
   ```

## Performance Considerations

### A2A Mode Performance

- **Network Latency**: A2A calls have network overhead vs in-memory handoffs
- **Session Isolation**: Each agent maintains separate session state
- **Concurrent Processing**: Agents can be scaled independently
- **Token Refresh**: Bearer tokens may need periodic refresh

### Optimization Strategies

1. **Session Reuse**: A2A client reuses sessions where possible
2. **Timeout Configuration**: Configurable timeouts for different operation types
3. **Error Recovery**: Automatic retry logic for transient failures
4. **Memory Management**: Efficient session cleanup

## Security Considerations

### Authentication Security

- **Token Security**: Bearer tokens should be stored securely and rotated regularly
- **Session Isolation**: Each workflow gets unique session IDs
- **Transport Security**: All A2A communication uses HTTPS
- **Access Control**: Cognito manages authentication boundaries

### Best Practices

1. **Token Rotation**: Regenerate bearer tokens periodically
2. **Environment Isolation**: Use separate tokens for dev/staging/prod
3. **Logging**: Avoid logging sensitive authentication data
4. **Network Security**: Ensure network access to AgentCore endpoints

## Production Deployment

### Deployment Checklist

- [ ] All four agents deployed and ready
- [ ] Authentication configured and tested
- [ ] A2A integration tests passing
- [ ] Environment variables configured
- [ ] Monitoring and logging enabled
- [ ] Bearer token rotation strategy in place

### Monitoring

1. **Agent Health**: Monitor individual agent status
2. **A2A Communication**: Track success/failure rates
3. **Authentication**: Monitor token usage and expiration
4. **Performance**: Track end-to-end workflow latency

### Scaling Considerations

- **Agent Scaling**: Individual agents can be scaled based on demand
- **Orchestrator Scaling**: Multiple orchestrator instances can run concurrently
- **Token Management**: Consider shared token management for multiple instances

## Migration Path

### From Strands Swarm to A2A

1. **Keep Both Modes**: Both modes can coexist using the `A2A_MODE` flag
2. **Gradual Migration**: Test A2A mode with subset of traffic
3. **Performance Comparison**: Compare metrics between modes
4. **Feature Parity**: Ensure both modes provide equivalent functionality

### Rollback Strategy

```bash
# Switch back to Strands Swarm mode
export A2A_MODE=false
agentcore deploy

# Or remove environment variable entirely
unset A2A_MODE
```

## Support and Resources

- **AgentCore Documentation**: https://aws.github.io/bedrock-agentcore-starter-toolkit/
- **A2A Protocol**: https://a2a-protocol.org/
- **Strands SDK**: https://github.com/anthropics/strands-python
- **Issue Tracking**: Use project issue tracker for bugs and feature requests