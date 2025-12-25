# Bug Report: AgentCore Deployment Failure - Exception Management Agent

## ✅ RESOLVED - December 22, 2025

---

## Issue Summary
AgentCore deployment fails during CodeBuild phase with status `FAILED` when deploying the Exception Management Agent. Multiple root causes were identified and fixed.

## Environment
- **Agent**: exception_management
- **Deployment Mode**: CodeBuild (ARM64)
- **Account**: 401552979575
- **Region**: us-east-1
- **AgentCore CLI**: Latest version

---

## Root Causes Identified (3 Issues)

### Issue 1: AgentCore CLI dockerignore.template Filtering
**Problem**: The `agentcore deploy` command uses an internal `dockerignore.template` with 46 patterns that filters out essential files when creating `source.zip`.

**Symptoms**:
- `source.zip` uploaded to S3 was only ~621-889 bytes (should be ~15KB+)
- Docker build failed with: `"/requirements.txt": not found`
- Only `Dockerfile` was included, missing `requirements.txt` and Python agent file

**Evidence from CloudWatch Logs**:
```
#1 transferring dockerfile: 889B done
#6 ERROR: failed to calculate checksum of ref: "/requirements.txt": not found
```

### Issue 2: Deleted IAM Execution Role
**Problem**: The execution role `AmazonBedrockAgentCoreSDKRuntime-us-east-1-116b035397` referenced in `.bedrock_agentcore.yaml` was deleted.

**Symptoms**:
- Agent invocation failed with: `AccessDeniedException: The execution role cannot be assumed by Bedrock AgentCore`
- Runtime status showed `READY` but invocations failed

### Issue 3: Runtime Using Stale Role Reference
**Problem**: Even after updating the YAML config, the AgentCore runtime still referenced the deleted role `AmazonBedrockAgentCoreSDKRuntime-us-east-1-ad04f7aab0`.

---

## Resolution Steps

### Step 1: Manual Source.zip Creation (Bypass CLI Filtering)
Since the agentcore CLI's dockerignore.template was filtering out essential files, we manually created and uploaded the source.zip:

```bash
# Navigate to the build folder
cd deployment/exception_management/.bedrock_agentcore/exception_manager

# Create source.zip with all required files
zip -r source.zip Dockerfile requirements.txt exception_management_agent_strands.py .dockerignore

# Verify zip size (should be ~15KB, not 600 bytes)
ls -la source.zip

# Upload to S3 (bypassing agentcore CLI)
aws s3 cp source.zip s3://bedrock-agentcore-codebuild-sources-401552979575-us-east-1/exception_manager/source.zip

# Trigger CodeBuild manually
aws codebuild start-build --project-name bedrock-agentcore-exception_manager-builder --region us-east-1
```

**Result**: Build #9 succeeded - Docker image pushed to ECR.

### Step 2: Update Runtime Execution Role
The runtime was still using a deleted IAM role. Updated it directly via AWS CLI:

```bash
aws bedrock-agentcore-control update-agent-runtime \
  --agent-runtime-id exception_manager-uliBS5DsX3 \
  --role-arn arn:aws:iam::401552979575:role/AmazonBedrockAgentCoreSDKRuntime-us-east-1-0f9cb91bfb \
  --agent-runtime-artifact '{"containerConfiguration":{"containerUri":"401552979575.dkr.ecr.us-east-1.amazonaws.com/bedrock-agentcore-exception_manager:latest"}}' \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --region us-east-1
```

**Result**: Runtime updated to version 2 with working execution role.

### Step 3: Update Local Configuration
Updated `.bedrock_agentcore.yaml` to use the correct execution role for future deployments:

```yaml
# Changed from:
execution_role: arn:aws:iam::401552979575:role/AmazonBedrockAgentCoreSDKRuntime-us-east-1-116b035397

# Changed to:
execution_role: arn:aws:iam::401552979575:role/AmazonBedrockAgentCoreSDKRuntime-us-east-1-0f9cb91bfb
```

---

## Verification

```bash
# Check runtime status
agentcore status
# Output: Ready - Agent deployed and endpoint available

# Test invocation
agentcore invoke '{"prompt": "Hello"}'
# Output: Agent responded successfully
```

---

## Key Learnings

### 1. ⭐ Update IAM Role WITHOUT Redeploying Agent (IMPORTANT)
You can update the execution role of a running AgentCore runtime WITHOUT rebuilding or redeploying the container. This is critical when:
- An IAM role gets accidentally deleted
- You need to switch to a different role with updated permissions
- Role ARN changes due to infrastructure updates

**Command**:
```bash
aws bedrock-agentcore-control update-agent-runtime \
  --agent-runtime-id <RUNTIME_ID> \
  --role-arn <NEW_ROLE_ARN> \
  --agent-runtime-artifact '{"containerConfiguration":{"containerUri":"<ECR_IMAGE_URI>"}}' \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --region us-east-1
```

**Example**:
```bash
aws bedrock-agentcore-control update-agent-runtime \
  --agent-runtime-id exception_manager-uliBS5DsX3 \
  --role-arn arn:aws:iam::401552979575:role/AmazonBedrockAgentCoreSDKRuntime-us-east-1-0f9cb91bfb \
  --agent-runtime-artifact '{"containerConfiguration":{"containerUri":"401552979575.dkr.ecr.us-east-1.amazonaws.com/bedrock-agentcore-exception_manager:latest"}}' \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --region us-east-1
```

**Note**: The `--agent-runtime-artifact` and `--network-configuration` are required parameters even if you're only changing the role. Use the existing values from `get-agent-runtime`.

### 2. AgentCore CLI Source.zip Filtering Bug
The `agentcore deploy` command's internal `dockerignore.template` (46 patterns) can filter out essential files like `requirements.txt` and Python source files. 

**Workaround**: Manually create and upload `source.zip` to S3, then trigger CodeBuild directly.

### 3. Updating YAML Config Does NOT Update Runtime
Updating `.bedrock_agentcore.yaml` does NOT update the runtime's execution role. The YAML is only used during initial deployment. For live runtimes, use the API.

### 4. Useful Debugging Commands
```bash
# Check source.zip size in S3
aws s3 ls s3://bedrock-agentcore-codebuild-sources-<ACCOUNT>-<REGION>/<AGENT>/

# Get CodeBuild logs
aws codebuild list-builds-for-project --project-name <PROJECT> --max-items 1
aws logs get-log-events --log-group-name /aws/codebuild/<PROJECT> --log-stream-name <BUILD_ID>

# Get runtime details (including actual role being used)
aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id <ID> --region us-east-1
```

---

## Files Modified
- `deployment/exception_management/.bedrock_agentcore.yaml` - Updated execution role
- `deployment/exception_management/.bedrock_agentcore/exception_manager/source.zip` - Manually created

## AWS Resources Updated
- **Runtime**: `exception_manager-uliBS5DsX3` - Updated to version 2 with new execution role
- **ECR Image**: `bedrock-agentcore-exception_manager:latest` - Rebuilt and pushed

---

## Prevention Recommendations

1. **Pre-deployment Validation**: Add script to verify source.zip contains all required files before upload
2. **IAM Role Protection**: Add deletion protection or alerts for AgentCore execution roles
3. **CI/CD Pipeline**: Implement automated deployment that bypasses CLI filtering issues
4. **Documentation**: Document the manual deployment workaround for future reference

---

## Timeline
| Time | Action | Result |
|------|--------|--------|
| Dec 21 Evening | Initial deployment attempts | Failed - source.zip filtering |
| Dec 22 14:07 | Manual source.zip upload + CodeBuild | Build #7 succeeded |
| Dec 22 14:09 | agentcore deploy (overwrote source.zip) | Build #8 failed |
| Dec 22 14:10 | Manual source.zip upload again | Build #9 succeeded |
| Dec 22 14:15 | Agent invocation test | Failed - IAM role deleted |
| Dec 22 14:18 | Runtime role update via API | Success |
| Dec 22 14:19 | Agent invocation test | ✅ Working |

---

**Status**: ✅ RESOLVED  
**Resolution Date**: December 22, 2025  
**Resolved By**: Development Team