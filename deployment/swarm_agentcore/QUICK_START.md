# Quick Start Guide

## Testing Locally with AgentCore Dev Server

### 1. Start the Dev Server

```bash
cd deployment/swarm_agentcore
agentcore dev --port 8082
```

Keep this terminal open - the dev server will run here.

### 2. Invoke the Agent (in a new terminal)

**Correct payload format:**

```bash
agentcore invoke --dev --port 8082 '{
  "document_path": "s3://trade-matching-system-agentcore-production/BANK/FAB_26933659.pdf",
  "source_type": "BANK"
}'
```

**Or with just the key:**

```bash
agentcore invoke --dev --port 8082 '{
  "document_path": "BANK/FAB_26933659.pdf",
  "source_type": "BANK"
}'
```

**For COUNTERPARTY trades:**

```bash
agentcore invoke --dev --port 8082 '{
  "document_path": "COUNTERPARTY/GCS381315_V1.pdf",
  "source_type": "COUNTERPARTY"
}'
```

### Required Payload Fields

- **`document_path`**: S3 path to the PDF
  - Full path: `s3://bucket/key`
  - Or just key: `BANK/file.pdf`
- **`source_type`**: Must be `"BANK"` or `"COUNTERPARTY"`

### Optional Payload Fields

- **`document_id`**: Unique identifier (auto-generated if omitted)
- **`correlation_id`**: Tracing ID (auto-generated if omitted)

### Common Errors

❌ **Error**: `"document_path is required in payload"`
✅ **Fix**: Add `"document_path"` to your JSON payload

❌ **Error**: `"source_type is required in payload"`
✅ **Fix**: Add `"source_type"` to your JSON payload

❌ **Error**: `"source_type must be BANK or COUNTERPARTY"`
✅ **Fix**: Use exactly `"BANK"` or `"COUNTERPARTY"` (case-sensitive)

## Full Deployment

### 1. Create Memory Resource

```bash
cd deployment/swarm_agentcore
python setup_memory.py
```

Save the memory ID from the output.

### 2. Set Environment Variables

```bash
export AGENTCORE_MEMORY_ID=<memory-id-from-step-1>
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=trade-matching-system-agentcore-production
export DYNAMODB_BANK_TABLE=BankTradeData
export DYNAMODB_COUNTERPARTY_TABLE=CounterpartyTradeData
export DYNAMODB_EXCEPTIONS_TABLE=ExceptionsTable
```

### 3. Deploy to AgentCore Runtime

```bash
cd deployment/swarm_agentcore
bash deploy_agentcore.sh
```

### 4. Invoke the Deployed Agent

```bash
aws bedrock-agent-runtime invoke-agent \
  --agent-id <agent-id> \
  --agent-alias-id <alias-id> \
  --session-id session-$(date +%s) \
  --input-text '{
    "document_path": "s3://trade-matching-system-agentcore-production/BANK/FAB_26933659.pdf",
    "source_type": "BANK",
    "document_id": "FAB_26933659"
  }' \
  --region us-east-1 \
  output.json
```

## Running Tests

### From deployment/swarm_agentcore/

```bash
bash run_tests.sh
```

### From Project Root

```bash
cd ../..
bash run_all_swarm_agentcore_tests.sh
```

## Documentation

- **Full CLI Examples**: `CLI_COMMAND_EXAMPLES.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Memory Configuration**: `MEMORY_CONFIGURATION_GUIDE.md`
- **Troubleshooting**: `TROUBLESHOOTING_GUIDE.md`
- **How to Run Tests**: `../../HOW_TO_RUN_TESTS.md`

## Need Help?

See `TROUBLESHOOTING_GUIDE.md` for common issues and solutions.
