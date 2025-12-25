# Fix AgentCore Memory Permissions

## Problem
Agents are using AWS default service role instead of custom role with memory permissions.

## Solution

### 1. Update Agent Configuration
Add execution role to your `.bedrock_agentcore.yaml`:

```yaml
# .bedrock_agentcore.yaml
runtime:
  execution_role_arn: "arn:aws:iam::401552979575:role/trade-matching-system-agentcore-runtime-production"

agents:
  pdf_adapter:
    entrypoint: pdf_adapter_agent_strands.py
    memory_enabled: true
    execution_role_arn: "arn:aws:iam::401552979575:role/trade-matching-system-agentcore-runtime-production"
```

### 2. Redeploy Agents
```bash
cd deployment/pdf_adapter
agentcore configure --execution-role-arn arn:aws:iam::401552979575:role/trade-matching-system-agentcore-runtime-production
agentcore launch
```

### 3. Verify Role ARN
Get the correct role ARN from Terraform:
```bash
cd terraform/agentcore
terraform output agentcore_runtime_execution_role_arn
```

### 4. Alternative: Add Permissions to Default Role
If you can't change the execution role, add memory permissions to the default role:

```bash
aws iam attach-role-policy \
  --role-name AmazonBedrockAgentCoreSDKRuntime-us-east-1-d49ec2442f \
  --policy-arn arn:aws:iam::401552979575:policy/trade-matching-system-agentcore-memory-access-production
```