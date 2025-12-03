#!/usr/bin/env python3
"""
Setup script for creating AgentCore Memory resources.
Run this before deploying agents.
"""

import os
import sys
from bedrock_agentcore.memory import MemoryClient

def main():
    """Create AgentCore Memory resources for the trade matching system."""
    
    # Initialize Memory client for us-east-1
    print("Initializing AgentCore Memory client...")
    client = MemoryClient(region_name="us-east-1")
    
    # Create memory with semantic strategy for trade patterns
    print("\n1. Creating trade patterns memory (semantic)...")
    try:
        trade_memory = client.create_memory_and_wait(
            name="trade-matching-trade-patterns",
            description="Semantic memory for trade patterns and historical context",
            strategies=[
                {
                    "semanticMemoryStrategy": {
                        "name": "trade-patterns-strategy",
                        "description": "Store and retrieve trade patterns",
                        "namespaces": ["trade/patterns/{actorId}/{sessionId}"]
                    }
                }
            ],
            event_expiry_days=90
        )
        print(f"✅ Created trade patterns memory: {trade_memory['memoryId']}")
        memory_arn = f"arn:aws:bedrock:us-east-1:{get_account_id()}:memory/{trade_memory['memoryId']}"
        print(f"   ARN: {memory_arn}")
        
        # Save the ARN to a file for later use
        with open("deployment/.memory_arn", "w") as f:
            f.write(memory_arn)
        
        print("\n✅ Memory setup complete!")
        print(f"\nTo deploy agents, set this environment variable:")
        print(f"export AGENTCORE_MEMORY_ARN='{memory_arn}'")
        
    except Exception as e:
        print(f"❌ Error creating memory: {e}")
        sys.exit(1)

def get_account_id():
    """Get AWS account ID."""
    import boto3
    sts = boto3.client('sts', region_name='us-east-1')
    return sts.get_caller_identity()['Account']

if __name__ == "__main__":
    main()
