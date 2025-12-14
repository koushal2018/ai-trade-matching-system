# AgentCore Troubleshooting Guide

This guide provides solutions to common issues encountered when deploying and running the Trade Matching Swarm on Amazon Bedrock AgentCore Runtime with memory integration.

## Table of Contents

1. [Memory Configuration Issues](#memory-configuration-issues)
2. [Deployment Issues](#deployment-issues)
3. [Runtime Errors](#runtime-errors)
4. [Performance Issues](#performance-issues)
5. [Memory Retrieval Issues](#memory-retrieval-issues)
6. [Agent Execution Issues](#agent-execution-issues)
7. [AWS Service Integration Issues](#aws-service-integration-issues)
8. [Debugging Techniques](#debugging-techniques)

## Memory Configuration Issues

### Issue 1: Memory ID Not Set

**Error Message**:
```
ValueError: AGENTCORE_MEMORY_ID environment variable not set
```

**Cause**: The memory ID environment variable is missing or not configured in `agentcore.yaml`.

**Solution**:

1. Verify memory resource was created:
   ```bash
   aws bedrock-agent list-memories --region us-east-1
   ```

2. Get the memory ID from the output:
   ```json
   {
     "memories": [
       {
         "id": "mem_abc123xyz456",
         "name": "TradeMatchingMemory",
         "status": "ACTIVE"
       }
     ]
   }
   ```

3. Update `agentcore.yaml`:
   ```yaml
   environment:
     AGENTCORE_MEMORY_ID: mem_abc123xyz456
   ```

4. Redeploy the agent:
   ```bash
   agentcore launch --agent-name trade-matching-swarm
   ```

### Issue 2: Memory Resource Not Found

**Error Message**:
```
ResourceNotFoundException: Memory resource 'mem_abc123xyz456' not found
```

**Cause**: Memory resource was deleted or the ID is incorrect.

**Solution**:

1. List all memory resources:
   ```bash
   aws bedrock-agent list-memories --region us-east-1
   ```

2. If memory doesn't exist, recreate it:
   ```bash
   cd deployment/swarm_agentcore
   python setup_memory.py
   ```

3. Update the memory ID in `agentcore.yaml` with the new ID.

### Issue 3: Memory Resource Not Active

**Error Message**:
```
InvalidStateException: Memory resource is in CREATING state
```

**Cause**: Memory resource creation is still in progress.

**Solution**:

1. Check memory status:
   ```bash
   aws bedrock-agent describe-memory \
     --memory-id mem_abc123xyz456 \
     --region us-east-1
   ```

2. Wait for status to become `ACTIVE`:
   ```bash
   # Poll every 10 seconds
   while true; do
     STATUS=$(aws bedrock-agent describe-memory \
       --memory-id mem_abc123xyz456 \
       --region us-east-1 \
       --query 'memory.status' \
       --output text)
     echo "Status: $STATUS"
     if [ "$STATUS" = "ACTIVE" ]; then
       break
     fi
     sleep 10
   done
   ```

3. Once active, retry deployment.

### Issue 4: Invalid Namespace Pattern

**Error Message**:
```
ValidationException: Invalid namespace pattern '/custom_namespace'
```

**Cause**: Using custom namespace patterns instead of built-in AgentCore patterns.

**Solution**:

Use only the standard AgentCore namespace patterns:
- `/facts/{actorId}`
- `/preferences/{actorId}`
- `/summaries/{actorId}/{sessionId}`

Update your memory configuration to use these patterns:
```python
strategies=[
    {
        "semanticMemoryStrategy": {
            "name": "TradeFacts",
            "namespaces": ["/facts/{actorId}"]
        }
    }
]
```

## Deployment Issues

### Issue 5: Deployment Fails with InvalidConfiguration

**Error Message**:
```
InvalidConfigurationException: Agent configuration is invalid
```

**Cause**: Missing required environment variables or invalid configuration in `agentcore.yaml`.

**Solution**:

1. Validate `agentcore.yaml` has all required fields:
   ```yaml
   name: trade-matching-swarm
   runtime: python3.11
   
   environment:
     AGENTCORE_MEMORY_ID: mem_abc123xyz456
     ACTOR_ID: trade_matching_system
     AWS_REGION: us-east-1
     S3_BUCKET_NAME: trade-matching-system-agentcore-production
     DYNAMODB_BANK_TABLE: BankTradeData
     DYNAMODB_COUNTERPARTY_TABLE: CounterpartyTradeData
     DYNAMODB_EXCEPTIONS_TABLE: ExceptionsTable
     BEDROCK_MODEL_ID: amazon.nova-pro-v1:0
   
   dependencies:
     - strands>=0.1.0
     - strands-tools>=0.1.0
     - bedrock-agentcore[strands-agents]>=0.1.0
     - boto3>=1.34.0
     - pydantic>=2.0.0
   
   timeout: 600
   memory: 2048
   ```

2. Verify all dependencies are available:
   ```bash
   pip install -r requirements.txt --dry-run
   ```

3. Check for syntax errors in YAML:
   ```bash
   python -c "import yaml; yaml.safe_load(open('agentcore.yaml'))"
   ```

### Issue 6: Dependency Installation Fails

**Error Message**:
```
DependencyInstallationException: Failed to install strands>=0.1.0
```

**Cause**: Package version not available or network issues.

**Solution**:

1. Test dependency installation locally:
   ```bash
   pip install strands>=0.1.0 --verbose
   ```

2. If package not found, check PyPI:
   ```bash
   pip index versions strands
   ```

3. Update to available version in `agentcore.yaml`:
   ```yaml
   dependencies:
     - strands==0.1.5  # Use specific version
   ```

4. For private packages, configure PyPI credentials:
   ```yaml
   environment:
     PIP_INDEX_URL: https://username:password@pypi.example.com/simple
   ```

### Issue 7: Timeout During Deployment

**Error Message**:
```
TimeoutException: Agent deployment exceeded 300 seconds
```

**Cause**: Large dependencies or slow network.

**Solution**:

1. Increase deployment timeout (if supported):
   ```bash
   agentcore launch --agent-name trade-matching-swarm --timeout 600
   ```

2. Pre-build dependencies locally and upload:
   ```bash
   # Create deployment package
   pip install -r requirements.txt -t ./package
   cd package
   zip -r ../deployment.zip .
   cd ..
   zip -g deployment.zip trade_matching_swarm_agentcore.py
   
   # Upload to S3
   aws s3 cp deployment.zip s3://my-deployment-bucket/
   ```

3. Reference pre-built package in deployment.

## Runtime Errors

### Issue 8: Agent Execution Timeout

**Error Message**:
```
ExecutionTimeoutException: Agent execution exceeded 600 seconds
```

**Cause**: Trade processing taking longer than configured timeout.

**Solution**:

1. Increase timeout in `agentcore.yaml`:
   ```yaml
   timeout: 900  # 15 minutes
   ```

2. Increase per-agent timeout in swarm configuration:
   ```python
   swarm = Swarm(
       agents,
       entry_point=pdf_adapter,
       execution_timeout=900.0,  # 15 minutes total
       node_timeout=300.0        # 5 minutes per agent
   )
   ```

3. Optimize agent processing:
   - Reduce max_tokens for faster responses
   - Optimize tool execution
   - Cache frequent operations

### Issue 9: Session Manager Initialization Fails

**Error Message**:
```
SessionManagerException: Failed to initialize session manager
```

**Cause**: Invalid memory configuration or network issues.

**Solution**:

1. Verify memory ID is correct:
   ```bash
   aws bedrock-agent describe-memory \
     --memory-id $AGENTCORE_MEMORY_ID \
     --region us-east-1
   ```

2. Check IAM permissions for AgentCore execution role:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "bedrock:GetMemory",
       "bedrock:QueryMemory",
       "bedrock:PutMemory"
     ],
     "Resource": "arn:aws:bedrock:us-east-1:*:memory/*"
   }
   ```

3. Add error handling to session manager creation:
   ```python
   try:
       session_manager = create_agent_session_manager(
           agent_name="pdf_adapter",
           document_id=document_id,
           memory_id=memory_id
       )
   except Exception as e:
       logger.error(f"Failed to create session manager: {e}")
       # Fallback: create agent without memory
       session_manager = None
   ```

### Issue 10: Agent Handoff Fails

**Error Message**:
```
HandoffException: Failed to hand off from pdf_adapter to trade_extractor
```

**Cause**: Agent not returning proper handoff signal or next agent not found.

**Solution**:

1. Verify all agents are registered in swarm:
   ```python
   swarm = Swarm(
       [pdf_adapter, trade_extractor, trade_matcher, exception_handler],
       entry_point=pdf_adapter
   )
   ```

2. Check agent system prompts include handoff instructions:
   ```python
   system_prompt = """...
   
   ## When to Hand Off
   - After successfully extracting text → hand off to trade_extractor
   - If extraction fails → hand off to exception_handler
   """
   ```

3. Enable verbose logging to see handoff decisions:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## Performance Issues

### Issue 11: Slow Memory Retrieval

**Error Message**:
```
PerformanceWarning: Memory retrieval took 2500ms (threshold: 500ms)
```

**Cause**: Large memory size or inefficient retrieval configuration.

**Solution**:

1. Reduce `top_k` to retrieve fewer results:
   ```python
   RetrievalConfig(
       top_k=5,  # Reduced from 10
       relevance_score=0.6
   )
   ```

2. Increase `relevance_score` to filter more aggressively:
   ```python
   RetrievalConfig(
       top_k=10,
       relevance_score=0.75  # Increased from 0.6
   )
   ```

3. Archive old memory data:
   ```bash
   # Export old summaries to S3
   python scripts/archive_memory.py \
     --memory-id $AGENTCORE_MEMORY_ID \
     --older-than 30d \
     --output s3://my-bucket/memory-archive/
   ```

4. Monitor retrieval latency:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/BedrockAgentCore/Memory \
     --metric-name RetrievalLatency \
     --dimensions Name=MemoryId,Value=$AGENTCORE_MEMORY_ID \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
     --period 300 \
     --statistics Average,Maximum \
     --region us-east-1
   ```

### Issue 12: High Token Usage

**Error Message**:
```
TokenLimitException: Request exceeded token limit
```

**Cause**: Large context or verbose agent responses.

**Solution**:

1. Reduce `max_tokens` in model configuration:
   ```python
   model = BedrockModel(
       model_id="amazon.nova-pro-v1:0",
       max_tokens=2048  # Reduced from 4096
   )
   ```

2. Limit memory retrieval results:
   ```python
   RetrievalConfig(
       top_k=3,  # Fewer results = less context
       relevance_score=0.8
   )
   ```

3. Optimize system prompts to be more concise.

4. Monitor token usage:
   ```python
   result = swarm(task)
   print(f"Total tokens: {result.accumulated_usage}")
   ```

### Issue 13: Concurrent Execution Limits

**Error Message**:
```
ThrottlingException: Rate exceeded for agent invocations
```

**Cause**: Too many concurrent agent invocations.

**Solution**:

1. Implement rate limiting in batch processing:
   ```python
   import time
   
   for document in documents:
       result = invoke_agent(document)
       time.sleep(2)  # 2 second delay between invocations
   ```

2. Request quota increase:
   ```bash
   # Open AWS Support case to increase AgentCore quotas
   ```

3. Use exponential backoff for retries:
   ```python
   import time
   from botocore.exceptions import ClientError
   
   def invoke_with_retry(document, max_retries=5):
       for attempt in range(max_retries):
           try:
               return invoke_agent(document)
           except ClientError as e:
               if e.response['Error']['Code'] == 'ThrottlingException':
                   wait_time = 2 ** attempt
                   time.sleep(wait_time)
               else:
                   raise
   ```

## Memory Retrieval Issues

### Issue 14: No Results from Memory Query

**Error Message**:
```
MemoryRetrievalWarning: No results found for query
```

**Cause**: Relevance threshold too high or no matching data in memory.

**Solution**:

1. Lower relevance threshold temporarily:
   ```python
   RetrievalConfig(
       top_k=10,
       relevance_score=0.3  # Lower threshold
   )
   ```

2. Check if memory has data:
   ```bash
   aws bedrock-agent query-memory \
     --memory-id $AGENTCORE_MEMORY_ID \
     --query "trade patterns" \
     --region us-east-1
   ```

3. Verify data was stored:
   ```python
   # Check CloudWatch logs for memory storage events
   aws logs filter-log-events \
     --log-group-name /aws/bedrock/agentcore/trade-matching-swarm \
     --filter-pattern "memory storage" \
     --region us-east-1
   ```

4. Rephrase query to be more general:
   ```python
   # Instead of: "Bank of America notional extraction pattern"
   # Try: "notional extraction"
   ```

### Issue 15: Irrelevant Memory Results

**Error Message**:
```
MemoryRetrievalWarning: Retrieved results have low relevance
```

**Cause**: Relevance threshold too low or poor quality stored data.

**Solution**:

1. Increase relevance threshold:
   ```python
   RetrievalConfig(
       top_k=10,
       relevance_score=0.8  # Higher threshold
   )
   ```

2. Improve stored data quality:
   - Store more specific, detailed facts
   - Include context and examples
   - Add metadata for better matching

3. Clean up low-quality data:
   ```python
   # Review and remove irrelevant facts
   # (Manual process - query, review, delete)
   ```

### Issue 16: Memory Storage Fails

**Error Message**:
```
MemoryStorageException: Failed to store data in namespace /facts/{actorId}
```

**Cause**: Invalid data format or IAM permission issues.

**Solution**:

1. Verify IAM permissions:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "bedrock:PutMemory"
     ],
     "Resource": "arn:aws:bedrock:us-east-1:*:memory/*"
   }
   ```

2. Check data format:
   ```python
   # Memory stores text data, not binary
   # Ensure data is string format
   fact = str(fact_data)
   ```

3. Add error handling:
   ```python
   try:
       # Agent stores fact during conversation
       # Strands SDK handles storage automatically
       pass
   except Exception as e:
       logger.error(f"Memory storage failed: {e}")
       # Continue processing without memory
   ```

## Agent Execution Issues

### Issue 17: Tool Execution Fails

**Error Message**:
```
ToolExecutionException: Failed to execute tool 'download_pdf_from_s3'
```

**Cause**: AWS service errors or invalid tool parameters.

**Solution**:

1. Test tool execution directly:
   ```python
   from deployment.swarm_agentcore.trade_matching_swarm import download_pdf_from_s3
   
   result = download_pdf_from_s3(
       bucket="trade-matching-system-agentcore-production",
       key="BANK/FAB_26933659.pdf",
       local_path="/tmp/test.pdf"
   )
   print(result)
   ```

2. Check IAM permissions for tool operations:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "s3:GetObject",
       "dynamodb:PutItem",
       "dynamodb:Scan",
       "bedrock:InvokeModel"
     ],
     "Resource": "*"
   }
   ```

3. Add tool error handling:
   ```python
   def download_pdf_from_s3(bucket: str, key: str, local_path: str) -> str:
       try:
           s3_client.download_file(bucket, key, local_path)
           return json.dumps({"success": True, "path": local_path})
       except Exception as e:
           return json.dumps({"success": False, "error": str(e)})
   ```

### Issue 18: Agent Stuck in Loop

**Error Message**:
```
RepetitiveHandoffException: Detected repetitive handoff pattern
```

**Cause**: Agents handing off back and forth without making progress.

**Solution**:

1. Review swarm configuration:
   ```python
   swarm = Swarm(
       agents,
       entry_point=pdf_adapter,
       max_handoffs=10,  # Limit total handoffs
       repetitive_handoff_detection_window=6,
       repetitive_handoff_min_unique_agents=2
   )
   ```

2. Check agent system prompts for clear handoff conditions:
   ```python
   system_prompt = """...
   
   ## When to Hand Off
   - ONLY hand off after completing your task
   - DO NOT hand off if you encounter errors - report them instead
   """
   ```

3. Enable verbose logging to see handoff pattern:
   ```bash
   python deployment/swarm_agentcore/trade_matching_swarm_agentcore.py \
     --verbose
   ```

## AWS Service Integration Issues

### Issue 19: S3 Access Denied

**Error Message**:
```
AccessDeniedException: User is not authorized to perform: s3:GetObject
```

**Cause**: Missing S3 permissions in AgentCore execution role.

**Solution**:

1. Add S3 permissions to execution role:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "s3:GetObject",
       "s3:PutObject",
       "s3:ListBucket"
     ],
     "Resource": [
       "arn:aws:s3:::trade-matching-system-agentcore-production",
       "arn:aws:s3:::trade-matching-system-agentcore-production/*"
     ]
   }
   ```

2. Verify bucket exists and is in correct region:
   ```bash
   aws s3 ls s3://trade-matching-system-agentcore-production --region us-east-1
   ```

3. Check bucket policy allows AgentCore access.

### Issue 20: DynamoDB Access Denied

**Error Message**:
```
AccessDeniedException: User is not authorized to perform: dynamodb:PutItem
```

**Cause**: Missing DynamoDB permissions in AgentCore execution role.

**Solution**:

1. Add DynamoDB permissions:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "dynamodb:PutItem",
       "dynamodb:GetItem",
       "dynamodb:Scan",
       "dynamodb:Query"
     ],
     "Resource": [
       "arn:aws:dynamodb:us-east-1:*:table/BankTradeData",
       "arn:aws:dynamodb:us-east-1:*:table/CounterpartyTradeData",
       "arn:aws:dynamodb:us-east-1:*:table/ExceptionsTable"
     ]
   }
   ```

2. Verify tables exist:
   ```bash
   aws dynamodb list-tables --region us-east-1
   ```

### Issue 21: Bedrock Model Access Denied

**Error Message**:
```
AccessDeniedException: User is not authorized to perform: bedrock:InvokeModel
```

**Cause**: Missing Bedrock permissions or model not enabled.

**Solution**:

1. Add Bedrock permissions:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "bedrock:InvokeModel"
     ],
     "Resource": "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"
   }
   ```

2. Enable model access in Bedrock console:
   - Go to Bedrock console → Model access
   - Request access to Amazon Nova Pro

3. Verify model is available:
   ```bash
   aws bedrock list-foundation-models --region us-east-1
   ```

## Debugging Techniques

### Enable Verbose Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### View CloudWatch Logs

```bash
# Tail logs in real-time
aws logs tail /aws/bedrock/agentcore/trade-matching-swarm \
  --follow \
  --region us-east-1

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/bedrock/agentcore/trade-matching-swarm \
  --filter-pattern "ERROR" \
  --region us-east-1
```

### Test Components Individually

```python
# Test memory setup
python deployment/swarm_agentcore/setup_memory.py

# Test session manager creation
python deployment/swarm_agentcore/test_session_manager_creation.py

# Test agent creation
python deployment/swarm_agentcore/test_agent_creation.py

# Test local execution
python deployment/swarm_agentcore/test_local.py
```

### Monitor Metrics

```bash
# Memory retrieval latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgentCore/Memory \
  --metric-name RetrievalLatency \
  --dimensions Name=MemoryId,Value=$AGENTCORE_MEMORY_ID \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region us-east-1

# Agent execution time
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgentCore \
  --metric-name ExecutionTime \
  --dimensions Name=AgentName,Value=trade-matching-swarm \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region us-east-1
```

### Trace Execution Flow

```python
# Add tracing to see execution flow
from deployment.swarm_agentcore.trade_matching_swarm import create_trade_matching_swarm_with_memory

swarm = create_trade_matching_swarm_with_memory(
    document_id="test_doc",
    memory_id=os.environ["AGENTCORE_MEMORY_ID"]
)

result = swarm("Process test trade")

# Print execution history
for node in result.node_history:
    print(f"Agent: {node.node_id}")
    print(f"  Status: {node.status}")
    print(f"  Duration: {node.execution_time}ms")
    print(f"  Tokens: {node.usage}")
```

---

**Need More Help?**

- Check the [Deployment Guide](DEPLOYMENT_GUIDE.md) for setup instructions
- Review the [Memory Configuration Guide](MEMORY_CONFIGURATION_GUIDE.md) for memory tuning
- Consult the [CLI Command Examples](CLI_COMMAND_EXAMPLES.md) for common operations
- Open an issue in the repository for additional support
