#!/usr/bin/env python3
"""
Setup script for creating AgentCore Memory resources.
Run this before deploying agents.

This script creates a memory resource with 3 built-in strategies:
1. Semantic Memory: For factual trade information and patterns
2. User Preference Memory: For learned processing preferences
3. Summary Memory: For session-specific summaries
"""

import os
import sys
from bedrock_agentcore.memory import MemoryClient


def create_trade_matching_memory(region_name: str = "us-east-1") -> str:
    """
    Create AgentCore Memory resource with built-in memory strategies.
    This is a one-time setup operation.
    
    Args:
        region_name: AWS region (default: us-east-1)
    
    Returns:
        Memory ID for use in agent configuration
    """
    client = MemoryClient(region_name=region_name)
    
    print(f"Creating AgentCore Memory resource in {region_name}...")
    print("\nConfiguring 3 built-in memory strategies:")
    print("  1. Semantic Memory: /facts/{actorId}")
    print("  2. User Preference Memory: /preferences/{actorId}")
    print("  3. Summary Memory: /summaries/{actorId}/{sessionId}")
    
    memory = client.create_memory_and_wait(
        name="TradeMatchingMemory",
        description="Multi-strategy memory for trade matching system with pattern learning",
        strategies=[
            {
                "semanticMemoryStrategy": {
                    "name": "TradeFacts",
                    "namespaces": ["/facts/{actorId}"]
                }
            },
            {
                "userPreferenceMemoryStrategy": {
                    "name": "ProcessingPreferences",
                    "namespaces": ["/preferences/{actorId}"]
                }
            },
            {
                "summaryMemoryStrategy": {
                    "name": "SessionSummaries",
                    "namespaces": ["/summaries/{actorId}/{sessionId}"]
                }
            }
        ]
    )
    
    memory_id = memory.get('memoryId')
    print(f"\n✅ Created AgentCore Memory with ID: {memory_id}")
    
    return memory_id


def main():
    """Create AgentCore Memory resources for the trade matching system."""
    
    try:
        # Create memory resource
        memory_id = create_trade_matching_memory(region_name="us-east-1")
        
        # Save the memory ID to a file for later use
        memory_id_file = "deployment/.memory_id"
        with open(memory_id_file, "w") as f:
            f.write(memory_id)
        print(f"\n💾 Memory ID saved to: {memory_id_file}")
        
        # Print configuration instructions
        print("\n" + "="*70)
        print("CONFIGURATION INSTRUCTIONS")
        print("="*70)
        print("\nSet this environment variable before deploying agents:")
        print(f"\n  export AGENTCORE_MEMORY_ID={memory_id}")
        print("\nOr add to your .env file:")
        print(f"\n  AGENTCORE_MEMORY_ID={memory_id}")
        print("\n" + "="*70)
        
        print("\n✅ Memory setup complete!")
        
    except Exception as e:
        print(f"\n❌ Error creating memory: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
