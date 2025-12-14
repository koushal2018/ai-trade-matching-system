# Troubleshooting Model Errors

## Error: "Model produced invalid sequence as part of ToolUse"

### Symptoms

```
EventStreamError: An error occurred (modelStreamErrorException) when calling the ConverseStream operation: 
Model produced invalid sequence as part of ToolUse. Please refer to the model tool use troubleshooting guide.
```

### Root Cause

This error occurs when the Bedrock model's tool use response doesn't match the expected format. This can happen with:

1. **Inference Profiles**: Application Inference Profiles may have issues with tool use
2. **Model Version**: Specific model versions may have tool use bugs
3. **Tool Schema**: Complex tool schemas may confuse the model
4. **Transient Issues**: Temporary Bedrock service issues

### Solution 1: Disable Inference Profiles (Recommended)

Inference profiles are for cost attribution only. The system works fine without them.

**Temporary disable (for testing):**

```bash
cd deployment/swarm_agentcore

# Rename the profiles file
mv inference_profiles.json inference_profiles.json.backup

# Restart dev server
agentcore dev --port 8082
```

The system will automatically fall back to the base model when profiles are not found.

**Re-enable later:**

```bash
mv inference_profiles.json.backup inference_profiles.json
```

### Solution 2: Use Base Model Directly

Edit `trade_matching_swarm.py` to force base model usage:

```python
# Around line 96, comment out the profile loading:
# INFERENCE_PROFILES = load_inference_profiles()
INFERENCE_PROFILES = {}  # Force disable
```

### Solution 3: Update to Latest Model

If using an older model version, update to the latest:

```python
# In trade_matching_swarm.py
BEDROCK_MODEL_ID = "amazon.nova-pro-v1:0"  # Latest version
```

### Solution 4: Simplify Tool Schemas

If the error persists, simplify tool parameter schemas:

```python
@tool
def download_pdf_from_s3(bucket: str, key: str) -> str:
    """Download PDF from S3.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
    """
    # Implementation
```

Keep descriptions short and parameter types simple (str, int, bool only).

### Solution 5: Retry with Exponential Backoff

For transient issues, implement retry logic:

```python
import time
from botocore.exceptions import EventStreamError

max_retries = 3
for attempt in range(max_retries):
    try:
        result = swarm(task)
        break
    except EventStreamError as e:
        if "modelStreamErrorException" in str(e) and attempt < max_retries - 1:
            wait_time = 2 ** attempt  # Exponential backoff
            logger.warning(f"Model error, retrying in {wait_time}s...")
            time.sleep(wait_time)
        else:
            raise
```

### Verification

After applying a solution, test with:

```bash
agentcore invoke --dev --port 8082 '{
  "document_path": "BANK/FAB_26933659.pdf",
  "source_type": "BANK"
}'
```

Expected: No `modelStreamErrorException`, successful tool execution.

### Prevention

1. **Use Base Model for Development**: Inference profiles are for production cost tracking
2. **Test Tools Individually**: Verify each tool works before adding to agents
3. **Keep Tool Schemas Simple**: Avoid complex nested objects
4. **Monitor Bedrock Service Health**: Check AWS Service Health Dashboard

### Related Issues

- **Memory Integration**: This error is unrelated to AgentCore Memory
- **Session Managers**: This error is unrelated to session management
- **Payload Format**: This error occurs after successful payload validation

### AWS Documentation

- [Bedrock Tool Use Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use.html)
- [Bedrock Troubleshooting](https://docs.aws.amazon.com/bedrock/latest/userguide/troubleshooting.html)
- [Application Inference Profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)

## Quick Fix Summary

**For immediate testing:**

```bash
# Disable inference profiles
cd deployment/swarm_agentcore
mv inference_profiles.json inference_profiles.json.backup

# Restart dev server
agentcore dev --port 8082

# Test again
agentcore invoke --dev --port 8082 '{
  "document_path": "BANK/FAB_26933659.pdf",
  "source_type": "BANK"
}'
```

This should resolve the `modelStreamErrorException` error.
