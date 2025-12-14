#!/usr/bin/env python3
"""
AgentCore Memory Resource Setup Script

This script creates the AgentCore Memory resource for the Trade Matching Swarm
with semantic memory strategy for long-term pattern learning.

Usage:
    python setup_memory.py [--region REGION]

The script will:
1. Create the memory resource with 3 built-in strategies
2. Wait for the resource to become available
3. Output the memory ID
4. Provide export command for environment variable
"""

import os
import sys
import argparse
import logging
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bedrock_agentcore.memory import MemoryClient
except ImportError:
    print("ERROR: bedrock-agentcore package not installed")
    print("Install with: pip install bedrock-agentcore[strands-agents]")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_trade_matching_memory(region_name: str = "us-east-1") -> str:
    """
    Create AgentCore Memory resource with built-in memory strategies.
    
    This creates a memory resource with three strategies:
    1. Semantic Memory: For factual trade information and patterns
    2. User Preference Memory: For learned processing preferences
    3. Summary Memory: For session-specific summaries
    
    Args:
        region_name: AWS region (default: us-east-1)
        
    Returns:
        Memory ID for use in agent configuration
        
    Raises:
        Exception: If memory creation fails
    """
    logger.info(f"Creating AgentCore Memory resource in {region_name}...")
    
    try:
        client = MemoryClient(region_name=region_name)
        
        logger.info("Configuring memory strategies...")
        
        # Create memory with 3 built-in strategies
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
        
        memory_id = memory.get('id')
        
        if not memory_id:
            raise ValueError("Memory creation succeeded but no ID was returned")
        
        logger.info(f"✓ Memory resource created successfully")
        logger.info(f"  Memory ID: {memory_id}")
        logger.info(f"  Region: {region_name}")
        logger.info(f"  Strategies: 3 (semantic, user preference, summary)")
        
        return memory_id
        
    except Exception as e:
        logger.error(f"Failed to create memory resource: {e}")
        raise


def main():
    """Main entry point for the setup script."""
    parser = argparse.ArgumentParser(
        description="Create AgentCore Memory resource for Trade Matching Swarm"
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create the memory resource
        memory_id = create_trade_matching_memory(region_name=args.region)
        
        # Print success message and export command
        print("\n" + "="*70)
        print("AgentCore Memory Setup Complete!")
        print("="*70)
        print(f"\nMemory ID: {memory_id}")
        print(f"Region: {args.region}")
        print("\nTo use this memory resource, set the environment variable:")
        print(f"\n  export AGENTCORE_MEMORY_ID={memory_id}")
        print("\nOr add to your .env file:")
        print(f"\n  AGENTCORE_MEMORY_ID={memory_id}")
        print("\nYou can also add this to your agentcore.yaml:")
        print(f"\n  environment:")
        print(f"    AGENTCORE_MEMORY_ID: {memory_id}")
        print("\n" + "="*70)
        
        return 0
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print("\n" + "="*70)
        print("Setup Failed!")
        print("="*70)
        print(f"\nError: {e}")
        print("\nPlease check:")
        print("  1. AWS credentials are configured")
        print("  2. You have permissions to create AgentCore Memory resources")
        print("  3. The bedrock-agentcore package is installed")
        print("\n" + "="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
