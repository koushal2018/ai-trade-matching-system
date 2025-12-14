# CLI Command Examples

This guide provides practical command-line examples for deploying, managing, and testing the Trade Matching Swarm on Amazon Bedrock AgentCore Runtime.

## Table of Contents

1. [Memory Resource Management](#memory-resource-management)
2. [Agent Deployment](#agent-deployment)
3. [Agent Invocation](#agent-invocation)
4. [Testing and Validation](#testing-and-validation)
5. [Monitoring and Debugging](#monitoring-and-debugging)
6. [Batch Processing](#batch-processing)
7. [Maintenance Operations](#maintenance-operations)

## Memory Resource Management

### Create Memory Resource

```bash
# Create memory resource using Python script
cd deployment/swarm_agentcore
python setup_memory.py

# Expected output:
# Creating AgentCore Memory resource...
# Memory resource created successfully!
# Memory ID: mem_abc123xyz456
# 
# Set environment variable:
# export AGENTCORE_MEMORY_ID=mem_abc123xyz456
```

### List Memory Resources

```bash
# List all memory resources in the account
aws bedrock-agent list-memories \
  --region us-east-1

# List with filtering
aws bedrock-agent list-memories \
  --region us-east-1 \
  --query 'memories[?name==`TradeMatchingMemory`]'
```

### Describe Memory Resource

```bash
# Get detailed information about a memory resource
aws bedrock-agent describe-memory \
  --memory-id mem_abc123xyz456 \
  --region us-east-1

# Get just the status
aws bedrock-agent describe-memory \
  --memory-id mem_abc123xyz456 \
  --region us-east-1 \
  --query 'memory.status' \
  --output text
```

### Query Memory

```bash
# Query semantic memory for trade patterns
aws bedrock-agent query-memory \
  --memory-id mem_abc123xyz456 \
  --query "trade extraction patterns for Bank of America" \
  --region us-east-1

# Query with specific namespace
aws bedrock-agent query-memory \
  --memory-id mem_abc123xyz456 \
  --query "matching decisions" \
  --namespace "/facts/trade_matching_system" \
  --region us-east-1

# Query with relevance threshold
aws bedrock-agent query-memory \
  --memory-id mem_abc123xyz456 \
  --query "exception resolutions" \
  --min-relevance-score 0.7 \
  --max-results 5 \
  --region us-east-1
```

### Delete Memory Resource

```bash
# Delete memory resource (use with caution!)
aws bedrock-agent delete-memory \
  --memory-id mem_abc123xyz456 \
  --region us-east-1

# Confirm deletion
aws bedrock-agent describe-memory \
  --memory-id mem_abc123xyz456 \
  --region us-east-1
# Expected: ResourceNotFoundException
```

## Agent Deployment

### Configure Agent

```bash
# Navigate to deployment directory
cd deployment/swarm_agentcore

# Configure agent using AgentCore CLI
agentcore configure --name trade-matching-swarm

# Configure with custom settings
agentcore configure \
  --name trade-matching-swarm \
  --runtime python3.11 \
  --timeout 600 \
  --memory 2048
```

### Deploy Agent

```bash
# Deploy agent to AgentCore Runtime
agentcore launch --agent-name trade-matching-swarm

# Deploy with specific version tag
agentcore launch \
  --agent-name trade-matching-swarm \
  --version v1.0.0

# Deploy with custom configuration file
agentcore launch \
  --agent-name trade-matching-swarm \
  --config agentcore.yaml
```

### Check Deployment Status

```bash
# Check agent status
agentcore status --agent-name trade-matching-swarm

# Get detailed agent information
agentcore describe --agent-name trade-matching-swarm

# Get agent endpoint URL
agentcore describe --agent-name trade-matching-swarm \
  --query 'agent.endpoint' \
  --output text
```

### Update Agent

```bash
# Update agent configuration
agentcore update \
  --agent-name trade-matching-swarm \
  --config agentcore.yaml

# Update environment variables only
agentcore update-env \
  --agent-name trade-matching-swarm \
  --env AGENTCORE_MEMORY_ID=mem_new123xyz789

# Update timeout
agentcore update \
  --agent-name trade-matching-swarm \
  --timeout 900
```

### List Agent Versions

```bash
# List all versions of the agent
agentcore list-versions --agent-name trade-matching-swarm

# Get latest version
agentcore list-versions \
  --agent-name trade-matching-swarm \
  --query 'versions[0].version' \
  --output text
```

### Rollback Agent

```bash
# Rollback to previous version
agentcore rollback \
  --agent-name trade-matching-swarm \
  --version v1.0.0

# Rollback to last stable version
agentcore rollback \
  --agent-name trade-matching-swarm \
  --to-last-stable
```

### Delete Agent

```bash
# Delete agent deployment
agentcore delete --agent-name trade-matching-swarm

# Delete with confirmation
agentcore delete \
  --agent-name trade-matching-swarm \
  --confirm
```

## Agent Invocation

### Invoke Agent with AWS CLI

```bash
# Basic invocation
aws bedrock-agent-runtime invoke-agent \
  --agent-id <agent-id> \
  --agent-alias-id <alias-id> \
  --session-id session-$(date +%s) \
  --input-text '{
    "document_path": "s3://trade-matching-system-agentcore-production/BANK/FAB_26933659.pdf",
    "source_type": "BANK",
    "document_id": "FAB_26933659",
    "correlation_id": "test-001"
  }' \
  --region us-east-1 \
  output.json

# View results
cat output.json | jq '.'
```

### Invoke with S3 Path

```bash
# Process bank trade
aws bedrock-agent-runtime invoke-agent \
  --agent-id <agent-id> \
  --agent-alias-id <alias-id> \
  --session-id bank-trade-$(date +%s) \
  --input-text '{
    "document_path": "s3://trade-matching-system-agentcore-production/BANK/FAB_26933659.pdf",
    "source_type": "BANK",
    "document_id": "FAB_26933659"
  }' \
  --region us-east-1 \
  bank_result.json

# Process counterparty trade
aws bedrock-agent-runtime invoke-agent \
  --agent-id <agent-id> \
  --agent-alias-id <alias-id> \
  --session-id cp-trade-$(date +%s) \
  --input-text '{
    "document_path": "s3://trade-matching-system-agentcore-production/COUNTERPARTY/GCS381315_V1.pdf",
    "source_type": "COUNTERPARTY",
    "document_id": "GCS381315"
  }' \
  --region us-east-1 \
  cp_result.json
```

### Invoke with Local File

```bash
# Upload local file to S3 first
aws s3 cp local_trade.pdf \
  s3://trade-matching-system-agentcore-production/BANK/local_trade.pdf

# Then invoke agent
aws bedrock-agent-runtime invoke-agent \
  --agent-id <agent-id> \
  --agent-alias-id <alias-id> \
  --session-id local-$(date +%s) \
  --input-text '{
    "document_path": "BANK/local_trade.pdf",
    "source_type": "BANK",
    "document_id": "local_trade"
  }' \
  --region us-east-1 \
  local_result.json
```

### Invoke with Correlation ID

```bash
# Include correlation ID for tracing
aws bedrock-agent-runtime invoke-agent \
  --agent-id <agent-id> \
  --agent-alias-id <alias-id> \
  --session-id traced-$(date +%s) \
  --input-text '{
    "document_path": "s3://trade-matching-system-agentcore-production/BANK/FAB_26933659.pdf",
    "source_type": "BANK",
    "document_id": "FAB_26933659",
    "correlation_id": "batch-2023-12-15-001"
  }' \
  --region us-east-1 \
  traced_result.json
```

## Testing and Validation

### Local Dev Server Testing

Start the AgentCore dev server:

```bash
cd deployment/swarm_agentcore
agentcore dev --port 8082
```

In another terminal, invoke with the correct payload format:

```bash
# Test with BANK trade (full S3 path)
agentcore invoke --dev --port 8082 '{
  "document_path": "s3://trade-matching-system-agentcore-production/BANK/FAB_26933659.pdf",
  "source_type": "BANK",
  "document_id": "FAB_26933659",
  "correlation_id": "test_001"
}'

# Test with COUNTERPARTY trade (just the key)
agentcore invoke --dev --port 8082 '{
  "document_path": "COUNTERPARTY/GCS381315_V1.pdf",
  "source_type": "COUNTERPARTY",
  "document_id": "GCS381315"
}'

# Test with minimal payload (auto-generated IDs)
agentcore invoke --dev --port 8082 '{
  "document_path": "BANK/FAB_26933659.pdf",
  "source_type": "BANK"
}'
```

**Required Payload Fields:**
- `document_path`: S3 path to PDF (full `s3://bucket/key` URL or just the key)
- `source_type`: Must be `"BANK"` or `"COUNTERPARTY"`

**Optional Payload Fields:**
- `document_id`: Unique identifier (auto-generated if not provided)
- `correlation_id`: Tracing ID (auto-generated if not provided)

**Common Errors:**
- `"document_path is required in payload"`: You must include `document_path` in the JSON
- `"source_type is required in payload"`: You must include `source_type` in the JSON
- `"source_type must be BANK or COUNTERPARTY"`: Check the value is exactly `"BANK"` or `"COUNTERPARTY"`

### Test Memory Setup

```bash
# Test memory resource creation
cd deployment/swarm_agentcore
python setup_memory.py

# Verify memory is active
aws bedrock-agent describe-memory \
  --memory-id $AGENTCORE_MEMORY_ID \
  --region us-east-1 \
  --query 'memory.status' \
  --output text
# Expected: ACTIVE
```

### Test Session Manager Creation

```bash
# Run session manager test
cd deployment/swarm_agentcore
python test_session_manager_creation.py

# Expected output:
# Testing session manager creation...
# ✓ Session manager created successfully
# ✓ Session ID format is correct
# ✓ Retrieval configs are set
```

### Test Agent Creation

```bash
# Run agent creation test
cd deployment/swarm_agentcore
python test_agent_creation.py

# Expected output:
# Testing agent creation with memory...
# ✓ PDF Adapter agent created
# ✓ Trade Extractor agent created
# ✓ Trade Matcher agent created
# ✓ Exception Handler agent created
# ✓ All agents have session managers
```

### Test Local Execution

```bash
# Test swarm locally before deployment
cd deployment/swarm_agentcore
python test_local.py

# Expected output:
# Testing local swarm execution...
# ✓ Swarm created successfully
# ✓ Processing test trade...
# ✓ Trade processed successfully
# ✓ Memory storage verified
# ✓ Memory retrieval verified
```

### Run Property Tests

```bash
# Run all property tests
cd /path/to/project
pytest test_property_*.py -v

# Run specific property test
pytest test_property_1_memory_storage_consistency.py -v

# Run with coverage
pytest test_property_*.py --cov=deployment/swarm_agentcore
```

### Run Unit Tests

```bash
# Run all unit tests
cd deployment/swarm_agentcore
pytest test_*.py -v

# Run specific test file
pytest test_memory_resource_creation.py -v

# Run with verbose output
pytest test_agent_creation.py -vv
```

### Run Integration Tests

```bash
# Run integration tests
cd deployment/swarm_agentcore
pytest test_integration_*.py -v

# Run trade processing integration test
pytest test_integration_trade_processing.py -v

# Run memory persistence integration test
pytest test_integration_memory_persistence.py -v
```

### Validate Deployment

```bash
# Run deployment validation script
cd deployment/swarm_agentcore
./validate_deployment.sh

# Expected output:
# ✓ Memory resource is active
# ✓ Agent is deployed
# ✓ Agent status is ACTIVE
# ✓ Environment variables are set
# ✓ S3 bucket is accessible
# ✓ DynamoDB tables exist
# ✓ IAM permissions are correct
```

## Monitoring and Debugging

### View CloudWatch Logs

```bash
# Tail logs in real-time
aws logs tail /aws/bedrock/agentcore/trade-matching-swarm \
  --follow \
  --region us-east-1

# View last 100 lines
aws logs tail /aws/bedrock/agentcore/trade-matching-swarm \
  --region us-east-1

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/bedrock/agentcore/trade-matching-swarm \
  --filter-pattern "ERROR" \
  --region us-east-1

# Filter for specific document
aws logs filter-log-events \
  --log-group-name /aws/bedrock/agentcore/trade-matching-swarm \
  --filter-pattern "FAB_26933659" \
  --region us-east-1

# Get logs from last hour
aws logs filter-log-events \
  --log-group-name /aws/bedrock/agentcore/trade-matching-swarm \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --region us-east-1
```

### Monitor Metrics

```bash
# Get memory retrieval latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgentCore/Memory \
  --metric-name RetrievalLatency \
  --dimensions Name=MemoryId,Value=$AGENTCORE_MEMORY_ID \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum,Minimum \
  --region us-east-1

# Get agent execution time
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgentCore \
  --metric-name ExecutionTime \
  --dimensions Name=AgentName,Value=trade-matching-swarm \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region us-east-1

# Get agent invocation count
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgentCore \
  --metric-name Invocations \
  --dimensions Name=AgentName,Value=trade-matching-swarm \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region us-east-1

# Get agent error count
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgentCore \
  --metric-name Errors \
  --dimensions Name=AgentName,Value=trade-matching-swarm \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region us-east-1
```

### Create CloudWatch Alarms

```bash
# Create alarm for execution failures
aws cloudwatch put-metric-alarm \
  --alarm-name trade-matching-swarm-failures \
  --alarm-description "Alert on agent execution failures" \
  --metric-name Errors \
  --namespace AWS/BedrockAgentCore \
  --dimensions Name=AgentName,Value=trade-matching-swarm \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --region us-east-1

# Create alarm for high latency
aws cloudwatch put-metric-alarm \
  --alarm-name trade-matching-swarm-latency \
  --alarm-description "Alert on high execution latency" \
  --metric-name ExecutionTime \
  --namespace AWS/BedrockAgentCore \
  --dimensions Name=AgentName,Value=trade-matching-swarm \
  --statistic Average \
  --period 300 \
  --threshold 60000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --region us-east-1

# Create alarm for memory retrieval latency
aws cloudwatch put-metric-alarm \
  --alarm-name memory-retrieval-latency \
  --alarm-description "Alert on slow memory retrieval" \
  --metric-name RetrievalLatency \
  --namespace AWS/BedrockAgentCore/Memory \
  --dimensions Name=MemoryId,Value=$AGENTCORE_MEMORY_ID \
  --statistic Average \
  --period 300 \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --region us-east-1
```

### Debug Agent Execution

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export AGENTCORE_DEBUG=true

# Run local test with debug output
cd deployment/swarm_agentcore
python test_local.py 2>&1 | tee debug.log

# Search debug log for specific patterns
grep "memory retrieval" debug.log
grep "agent handoff" debug.log
grep "tool execution" debug.log
```

## Batch Processing

### Process Multiple Trades

```bash
#!/bin/bash
# batch_process.sh - Process all trades in a folder

BUCKET="trade-matching-system-agentcore-production"
SOURCE_TYPE="BANK"
AGENT_ID="<agent-id>"
ALIAS_ID="<alias-id>"

# List all PDFs in the folder
aws s3 ls s3://${BUCKET}/${SOURCE_TYPE}/ | grep .pdf | while read -r line; do
  FILE=$(echo $line | awk '{print $4}')
  DOCUMENT_ID=$(basename $FILE .pdf)
  
  echo "Processing: $FILE"
  
  # Invoke agent
  aws bedrock-agent-runtime invoke-agent \
    --agent-id $AGENT_ID \
    --agent-alias-id $ALIAS_ID \
    --session-id batch-$(date +%s) \
    --input-text "{
      \"document_path\": \"s3://${BUCKET}/${SOURCE_TYPE}/${FILE}\",
      \"source_type\": \"${SOURCE_TYPE}\",
      \"document_id\": \"${DOCUMENT_ID}\"
    }" \
    --region us-east-1 \
    output_${DOCUMENT_ID}.json
    
  # Check result
  if [ $? -eq 0 ]; then
    echo "✓ Success: $DOCUMENT_ID"
  else
    echo "✗ Failed: $DOCUMENT_ID"
  fi
  
  sleep 2  # Rate limiting
done

echo "Batch processing complete!"
```

### Process with Parallel Execution

```bash
#!/bin/bash
# parallel_process.sh - Process trades in parallel

BUCKET="trade-matching-system-agentcore-production"
SOURCE_TYPE="BANK"
AGENT_ID="<agent-id>"
ALIAS_ID="<alias-id>"
MAX_PARALLEL=5

# Function to process a single trade
process_trade() {
  FILE=$1
  DOCUMENT_ID=$(basename $FILE .pdf)
  
  aws bedrock-agent-runtime invoke-agent \
    --agent-id $AGENT_ID \
    --agent-alias-id $ALIAS_ID \
    --session-id parallel-$(date +%s)-$$ \
    --input-text "{
      \"document_path\": \"s3://${BUCKET}/${SOURCE_TYPE}/${FILE}\",
      \"source_type\": \"${SOURCE_TYPE}\",
      \"document_id\": \"${DOCUMENT_ID}\"
    }" \
    --region us-east-1 \
    output_${DOCUMENT_ID}.json
}

export -f process_trade
export BUCKET SOURCE_TYPE AGENT_ID ALIAS_ID

# Process in parallel
aws s3 ls s3://${BUCKET}/${SOURCE_TYPE}/ | grep .pdf | awk '{print $4}' | \
  xargs -P $MAX_PARALLEL -I {} bash -c 'process_trade "$@"' _ {}

echo "Parallel processing complete!"
```

### Generate Batch Report

```bash
#!/bin/bash
# generate_batch_report.sh - Summarize batch processing results

echo "Batch Processing Report"
echo "======================"
echo ""

TOTAL=$(ls output_*.json 2>/dev/null | wc -l)
SUCCESS=$(grep -l '"success": true' output_*.json 2>/dev/null | wc -l)
FAILED=$((TOTAL - SUCCESS))

echo "Total Processed: $TOTAL"
echo "Successful: $SUCCESS"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -gt 0 ]; then
  echo "Failed Documents:"
  grep -L '"success": true' output_*.json | while read file; do
    DOC_ID=$(basename $file .json | sed 's/output_//')
    ERROR=$(jq -r '.error' $file 2>/dev/null)
    echo "  - $DOC_ID: $ERROR"
  done
fi
```

## Maintenance Operations

### Archive Old Memory Data

```bash
# Export memory data to S3 (conceptual - actual implementation may vary)
python scripts/archive_memory.py \
  --memory-id $AGENTCORE_MEMORY_ID \
  --older-than 30d \
  --output s3://my-bucket/memory-archive/$(date +%Y-%m-%d)/
```

### Clean Up Test Data

```bash
# Delete test outputs
rm -f output_*.json
rm -f debug.log

# Clean up S3 test files
aws s3 rm s3://trade-matching-system-agentcore-production/test/ --recursive

# Clean up DynamoDB test records
aws dynamodb delete-item \
  --table-name BankTradeData \
  --key '{"Trade_ID": {"S": "test_trade_001"}}' \
  --region us-east-1
```

### Backup Configuration

```bash
# Backup agentcore.yaml
cp agentcore.yaml agentcore.yaml.backup.$(date +%Y%m%d)

# Backup environment variables
env | grep -E "AGENTCORE|AWS|DYNAMODB|S3" > env.backup.$(date +%Y%m%d)

# Backup memory configuration
aws bedrock-agent describe-memory \
  --memory-id $AGENTCORE_MEMORY_ID \
  --region us-east-1 \
  > memory_config.backup.$(date +%Y%m%d).json
```

### Update Dependencies

```bash
# Update requirements.txt
cd deployment/swarm_agentcore
pip list --outdated

# Update specific package
pip install --upgrade strands

# Regenerate requirements.txt
pip freeze > requirements.txt

# Test with new dependencies
python test_local.py
```

### Scale Agent Resources

```bash
# Update memory allocation
agentcore update \
  --agent-name trade-matching-swarm \
  --memory 4096  # Increase to 4GB

# Update timeout
agentcore update \
  --agent-name trade-matching-swarm \
  --timeout 900  # Increase to 15 minutes

# Update concurrency limits
agentcore update-scaling \
  --agent-name trade-matching-swarm \
  --min-instances 2 \
  --max-instances 20
```

---

**Quick Reference Card**

```bash
# Setup
python setup_memory.py
export AGENTCORE_MEMORY_ID=mem_abc123xyz456
agentcore launch --agent-name trade-matching-swarm

# Test
python test_local.py
pytest test_*.py -v

# Deploy
agentcore launch --agent-name trade-matching-swarm

# Invoke
aws bedrock-agent-runtime invoke-agent \
  --agent-id <id> --agent-alias-id <alias> \
  --session-id session-$(date +%s) \
  --input-text '{"document_path":"s3://bucket/key","source_type":"BANK"}' \
  --region us-east-1 output.json

# Monitor
aws logs tail /aws/bedrock/agentcore/trade-matching-swarm --follow

# Debug
export LOG_LEVEL=DEBUG
python test_local.py 2>&1 | tee debug.log
```
