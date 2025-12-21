#!/bin/bash
AGENTCORE_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:CreateAgentRuntime",
        "bedrock-agentcore:DeleteAgentRuntime",
        "bedrock-agentcore:GetAgentRuntime",
        "bedrock-agentcore:UpdateAgentRuntime",
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": "*"
    }
  ]
}'

aws iam create-policy \
  --policy-name "AmazonBedrockAgentCoreRuntimeDefaultServiceRole-dmdo4-AgentCoreAccess" \
  --policy-document "${AGENTCORE_POLICY}" 2>/dev/null || echo "Policy exists"

aws iam attach-role-policy \
  --role-name "AmazonBedrockAgentCoreRuntimeDefaultServiceRole-dmdo4" \
  --policy-arn "arn:aws:iam::401552979575:policy/AmazonBedrockAgentCoreRuntimeDefaultServiceRole-dmdo4-AgentCoreAccess"