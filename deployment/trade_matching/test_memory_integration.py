#!/usr/bin/env python3
"""
Test AgentCore Memory Integration

Verifies that the Trade Matching Agent can connect to and use
the existing AgentCore Memory resource.

Usage:
    python test_memory_integration.py
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MEMORY_ID = "trade_matching_agent_mem-SxPFir3bbF"
REGION = "us-east-1"

def test_memory_connection():
    """Test connection to AgentCore Memory."""
    try:
        from bedrock_agentcore.memory.session import MemorySessionManager
        from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole
        
        logger.info(f"Testing connection to memory: {MEMORY_ID}")
        
        # Initialize memory session
        session_manager = MemorySessionManager(
            memory_id=MEMORY_ID,
            region_name=REGION
        )
        
        logger.info("✓ Memory session manager initialized successfully")
        
        # Create a test session
        session = session_manager.create_memory_session(
            actor_id="test-agent",
            session_id=f"test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        logger.info("✓ Test memory session created successfully")
        
        # Store a test decision
        test_message = f"""Test Matching Decision
Trade ID: TEST_001
Classification: MATCHED
Confidence: 95%
Timestamp: {datetime.utcnow().isoformat()}Z
"""
        
        session.add_turns(
            messages=[
                ConversationalMessage(
                    test_message,
                    MessageRole.ASSISTANT
                )
            ]
        )
        
        logger.info("✓ Test decision stored in memory")
        
        # Try to retrieve recent turns
        turns = session.get_last_k_turns(k=1)
        logger.info(f"✓ Retrieved {len(turns)} turn(s) from memory")
        
        logger.info("\n✅ All memory integration tests passed!")
        logger.info(f"Memory resource {MEMORY_ID} is working correctly")
        return True
        
    except ImportError as e:
        logger.error(f"❌ AgentCore Memory SDK not installed: {e}")
        logger.info("Install with: pip install bedrock-agentcore")
        return False
    except Exception as e:
        logger.error(f"❌ Memory integration test failed: {e}")
        logger.exception("Full error:")
        return False

if __name__ == "__main__":
    success = test_memory_connection()
    sys.exit(0 if success else 1)
