#!/usr/bin/env python3
"""
Fix IAM permissions for AgentCore runtime roles to enable Memory service access.

This script adds the following permissions to all AgentCore runtime roles:
1. Bedrock AgentCore Memory service permissions (ListEvents, CreateEvent, GetMemory, RetrieveMemoryRecords)
2. KMS permissions for DynamoDB encryption (Decrypt, Encrypt, GenerateDataKey)

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3
"""

import boto3
import json
import sys
from typing import List, Dict, Any
from botocore.exceptions import ClientError


# Configuration
ACCOUNT_ID = "401552979575"
REGION = "us-east-1"
MEMORY_RESOURCE_ARN = f"arn:aws:bedrock-agentcore:{REGION}:{ACCOUNT_ID}:memory/trade_matching_decisions-Z3tG4b4Xsd"

# Target runtime roles
TARGET_ROLES = [
    "AmazonBedrockAgentCoreSDKRuntime-us-east-1-211bc0c422",
    "AmazonBedrockAgentCoreSDKRuntime-us-east-1-d49ec2442f",
    "AmazonBedrockAgentCoreSDKRuntime-us-east-1-0f9cb91bfb"
]

# IAM Policy for Memory Service Access
MEMORY_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BedrockAgentCoreMemoryAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:ListEvents",
                "bedrock-agentcore:CreateEvent",
                "bedrock-agentcore:GetMemory",
                "bedrock-agentcore:RetrieveMemoryRecords"
            ],
            "Resource": MEMORY_RESOURCE_ARN
        },
        {
            "Sid": "KMSAccessForDynamoDB",
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt",
                "kms:Encrypt",
                "kms:GenerateDataKey"
            ],
            "Resource": f"arn:aws:kms:{REGION}:{ACCOUNT_ID}:key/*"
        }
    ]
}


def create_or_update_policy(iam_client, policy_name: str, policy_document: Dict[str, Any]) -> str:
    """
    Create a new IAM policy or update existing one.
    
    Returns the policy ARN.
    """
    policy_arn = f"arn:aws:iam::{ACCOUNT_ID}:policy/{policy_name}"
    
    try:
        # Try to create the policy
        response = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
            Description="AgentCore Memory service and KMS permissions for trade matching system"
        )
        print(f"✅ Created new policy: {policy_name}")
        return response['Policy']['Arn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"⚠️  Policy {policy_name} already exists, updating...")
            
            # Get existing policy versions
            try:
                versions = iam_client.list_policy_versions(PolicyArn=policy_arn)
                
                # Delete oldest non-default version if we have 5 versions (AWS limit)
                if len(versions['Versions']) >= 5:
                    oldest_version = [v for v in versions['Versions'] if not v['IsDefaultVersion']][-1]
                    iam_client.delete_policy_version(
                        PolicyArn=policy_arn,
                        VersionId=oldest_version['VersionId']
                    )
                    print(f"   Deleted old policy version: {oldest_version['VersionId']}")
                
                # Create new version
                iam_client.create_policy_version(
                    PolicyArn=policy_arn,
                    PolicyDocument=json.dumps(policy_document),
                    SetAsDefault=True
                )
                print(f"✅ Updated policy: {policy_name}")
                return policy_arn
                
            except ClientError as update_error:
                print(f"❌ Failed to update policy: {update_error}")
                raise
        else:
            print(f"❌ Failed to create policy: {e}")
            raise


def attach_policy_to_role(iam_client, role_name: str, policy_arn: str) -> bool:
    """
    Attach a policy to an IAM role.
    
    Returns True if successful, False otherwise.
    """
    try:
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        print(f"✅ Attached policy to role: {role_name}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"❌ Role not found: {role_name}")
            return False
        else:
            print(f"❌ Failed to attach policy to {role_name}: {e}")
            return False


def verify_role_exists(iam_client, role_name: str) -> bool:
    """
    Verify that an IAM role exists.
    """
    try:
        iam_client.get_role(RoleName=role_name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return False
        raise


def main():
    """
    Main execution function.
    """
    print("=" * 80)
    print("AgentCore Memory Permissions Fix")
    print("=" * 80)
    print()
    print(f"Target Account: {ACCOUNT_ID}")
    print(f"Region: {REGION}")
    print(f"Memory Resource: {MEMORY_RESOURCE_ARN}")
    print()
    print("Target Roles:")
    for role in TARGET_ROLES:
        print(f"  - {role}")
    print()
    
    # Initialize IAM client
    iam_client = boto3.client('iam', region_name=REGION)
    
    # Step 1: Verify all roles exist
    print("Step 1: Verifying roles exist...")
    print("-" * 80)
    missing_roles = []
    for role_name in TARGET_ROLES:
        if verify_role_exists(iam_client, role_name):
            print(f"✅ Role exists: {role_name}")
        else:
            print(f"❌ Role not found: {role_name}")
            missing_roles.append(role_name)
    
    if missing_roles:
        print()
        print(f"⚠️  Warning: {len(missing_roles)} role(s) not found. Continuing with existing roles...")
        print()
    
    # Step 2: Create or update the policy
    print()
    print("Step 2: Creating/updating IAM policy...")
    print("-" * 80)
    policy_name = "AgentCoreMemoryAndKMSAccess"
    
    try:
        policy_arn = create_or_update_policy(iam_client, policy_name, MEMORY_POLICY)
    except Exception as e:
        print(f"❌ Failed to create/update policy: {e}")
        sys.exit(1)
    
    # Step 3: Attach policy to all roles
    print()
    print("Step 3: Attaching policy to roles...")
    print("-" * 80)
    success_count = 0
    for role_name in TARGET_ROLES:
        if role_name not in missing_roles:
            if attach_policy_to_role(iam_client, role_name, policy_arn):
                success_count += 1
    
    # Summary
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"✅ Policy created/updated: {policy_name}")
    print(f"✅ Successfully attached to {success_count}/{len(TARGET_ROLES) - len(missing_roles)} roles")
    
    if missing_roles:
        print(f"⚠️  Skipped {len(missing_roles)} missing role(s)")
    
    print()
    print("Next steps:")
    print("1. Verify agents can now access Memory service")
    print("2. Test with: agentcore dev (in any agent directory)")
    print("3. Check CloudWatch logs for Memory service access")
    print()


if __name__ == "__main__":
    main()
