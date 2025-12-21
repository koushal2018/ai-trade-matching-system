#!/usr/bin/env python3
"""
Fix Trade Matching Agent execution roles.
The agent is configured with non-existent roles, causing 403 and ECR errors.
"""

import boto3
import json
from botocore.exceptions import ClientError

# Configuration
AGENT_RUNTIME_ID = "trade_matching_ai-r8eaGb4u7B"
NEW_RUNTIME_ROLE_ARN = "arn:aws:iam::401552979575:role/AmazonBedrockAgentCoreSDKRuntime-us-east-1-0f9cb91bfb"
NEW_CODEBUILD_ROLE_ARN = "arn:aws:iam::401552979575:role/AmazonBedrockAgentCoreSDKCodeBuild-us-east-1-0f9cb91bfb"
CODEBUILD_PROJECT = "bedrock-agentcore-trade_matching_ai-builder"
REGION = "us-east-1"

def main():
    print("=" * 50)
    print("Fixing Trade Matching Agent Execution Roles")
    print("=" * 50)
    print()
    print(f"Agent Runtime ID: {AGENT_RUNTIME_ID}")
    print(f"New Runtime Role: {NEW_RUNTIME_ROLE_ARN}")
    print(f"New CodeBuild Role: {NEW_CODEBUILD_ROLE_ARN}")
    print(f"CodeBuild Project: {CODEBUILD_PROJECT}")
    print(f"Region: {REGION}")
    print()
    
    # Initialize clients
    iam_client = boto3.client('iam', region_name=REGION)
    agentcore_client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    codebuild_client = boto3.client('codebuild', region_name=REGION)
    
    # Step 1: Verify the runtime role exists
    print("Step 1: Verifying IAM runtime role exists...")
    try:
        role_response = iam_client.get_role(
            RoleName='AmazonBedrockAgentCoreSDKRuntime-us-east-1-0f9cb91bfb'
        )
        print(f"✅ Runtime role verified: {role_response['Role']['Arn']}")
    except ClientError as e:
        print(f"❌ Runtime role verification failed: {e}")
        return 1
    
    # Step 2: Verify the CodeBuild role exists
    print()
    print("Step 2: Verifying IAM CodeBuild role exists...")
    try:
        role_response = iam_client.get_role(
            RoleName='AmazonBedrockAgentCoreSDKCodeBuild-us-east-1-0f9cb91bfb'
        )
        print(f"✅ CodeBuild role verified: {role_response['Role']['Arn']}")
    except ClientError as e:
        print(f"❌ CodeBuild role verification failed: {e}")
        return 1
    
    print()
    print("Step 3: Updating CodeBuild project service role...")
    
    # Step 3: Update CodeBuild project
    try:
        codebuild_response = codebuild_client.update_project(
            name=CODEBUILD_PROJECT,
            serviceRole=NEW_CODEBUILD_ROLE_ARN
        )
        print("✅ CodeBuild project updated successfully")
        print(f"   Project: {codebuild_response['project']['name']}")
        print(f"   Service Role: {codebuild_response['project']['serviceRole']}")
    except ClientError as e:
        print(f"❌ CodeBuild update failed: {e}")
        return 1
    
    print()
    print("Step 4: Updating AgentCore Runtime execution role...")
    
    # Step 4: Update the runtime
    try:
        update_response = agentcore_client.update_agent_runtime(
            agentRuntimeId=AGENT_RUNTIME_ID,
            roleArn=NEW_RUNTIME_ROLE_ARN
        )
        print("✅ Runtime updated successfully")
        print(f"   Status: {update_response.get('status', 'N/A')}")
        print(f"   Version: {update_response.get('agentRuntimeVersion', 'N/A')}")
    except ClientError as e:
        print(f"❌ Runtime update failed: {e}")
        return 1
    
    print()
    print("Step 5: Verifying runtime status...")
    
    # Step 5: Verify the update
    try:
        runtime_response = agentcore_client.get_agent_runtime(
            agentRuntimeId=AGENT_RUNTIME_ID
        )
        runtime = runtime_response['agentRuntime']
        print(f"✅ Runtime verified")
        print(f"   Status: {runtime.get('status', 'N/A')}")
        print(f"   Role ARN: {runtime.get('roleArn', 'N/A')}")
    except ClientError as e:
        print(f"⚠️  Runtime verification warning: {e}")
    
    print()
    print("=" * 50)
    print("✅ All execution roles updated successfully!")
    print("=" * 50)
    print()
    print("Next steps:")
    print("1. Deploy the agent: agentcore launch --auto-update-on-conflict")
    print("2. Test invocation: agentcore invoke --agent trade_matching_ai '{...}'")
    print()
    
    return 0

if __name__ == "__main__":
    exit(main())
