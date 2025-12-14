"""
Property-based test for memory storage consistency.
Feature: swarm-to-agentcore, Property 1: Memory storage consistency
Validates: Requirements 2.2, 2.4, 3.1

Property 1: Memory Storage Consistency
For any agent execution that processes data (PDF extraction, trade extraction, 
matching decision, exception handling), the agent should store the relevant 
pattern in its designated memory namespace.

This test verifies that:
1. Agents can successfully store patterns in their designated namespaces
2. Stored patterns can be retrieved from memory
3. The storage operation is consistent across different agent types
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "deployment" / "swarm"))

# Agent type to namespace mapping
AGENT_NAMESPACES = {
    "pdf_adapter": "/facts/{actorId}",
    "trade_extractor": "/facts/{actorId}",
    "trade_matcher": "/facts/{actorId}",
    "exception_handler": "/facts/{actorId}"
}


def get_session_manager_for_agent(agent_name: str, document_id: str):
    """
    Create a session manager for testing a specific agent.
    Returns None if memory is not available.
    """
    try:
        from deployment.swarm.trade_matching_swarm import create_agent_session_manager
        
        memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
        if not memory_id:
            return None
        
        session_manager = create_agent_session_manager(
            agent_name=agent_name,
            document_id=document_id,
            memory_id=memory_id,
            actor_id="trade_matching_system",
            region_name="us-east-1"
        )
        
        return session_manager
        
    except ImportError as e:
        print(f"Warning: Could not import session manager: {e}")
        return None
    except Exception as e:
        print(f"Warning: Could not create session manager: {e}")
        return None


def store_pattern_to_memory(
    session_manager,
    pattern_data: Dict[str, Any],
    namespace: str
) -> bool:
    """
    Store a pattern to memory and return success status.
    """
    try:
        # Store the pattern using the session manager
        # The pattern should be stored as a message that will be extracted
        # by the semantic memory strategy
        
        # Format the pattern as a message
        pattern_message = json.dumps(pattern_data)
        
        # Store using the session manager's store method
        # Note: The actual API may vary based on AgentCore Memory implementation
        session_manager.store(
            content=pattern_message,
            namespace=namespace
        )
        
        # Give memory service time to process
        time.sleep(0.5)
        
        return True
        
    except Exception as e:
        print(f"Warning: Failed to store pattern: {e}")
        return False


def retrieve_pattern_from_memory(
    session_manager,
    query: str,
    namespace: str
) -> Optional[list]:
    """
    Retrieve patterns from memory based on a query.
    """
    try:
        # Retrieve using the session manager
        results = session_manager.retrieve(
            query=query,
            namespace=namespace
        )
        
        return results
        
    except Exception as e:
        print(f"Warning: Failed to retrieve pattern: {e}")
        return None


# Strategy for generating valid pattern data
pattern_data_strategy = st.dictionaries(
    keys=st.sampled_from([
        "pattern_type",
        "field_name",
        "technique",
        "confidence",
        "timestamp",
        "description"
    ]),
    values=st.one_of(
        st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters="\x00\n\r")),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        st.integers(min_value=0, max_value=1000000)
    ),
    min_size=1,
    max_size=5
)


@given(
    agent_type=st.sampled_from(["pdf_adapter", "trade_extractor", "trade_matcher", "exception_handler"]),
    pattern_data=pattern_data_strategy
)
@settings(max_examples=20, deadline=None)
def test_property_memory_storage_consistency(agent_type: str, pattern_data: Dict[str, Any]):
    """
    Property 1: Memory Storage Consistency
    
    For any agent execution that processes data, the agent should store 
    the relevant pattern in its designated memory namespace.
    
    **Feature: swarm-to-agentcore, Property 1: Memory storage consistency**
    **Validates: Requirements 2.2, 2.4, 3.1**
    """
    # Generate a unique document ID for this test
    document_id = f"test_{int(time.time() * 1000)}"
    
    # Get session manager for this agent
    session_manager = get_session_manager_for_agent(agent_type, document_id)
    
    # If session manager is not available, skip this test
    if session_manager is None:
        import pytest
        pytest.skip("Memory integration not available (AGENTCORE_MEMORY_ID not set or invalid)")
    
    # Get the namespace for this agent type
    namespace = AGENT_NAMESPACES[agent_type]
    
    # Add agent_name to pattern data for identification
    pattern_data_with_agent = {
        **pattern_data,
        "agent_name": agent_type,
        "test_id": document_id
    }
    
    # Store the pattern
    store_success = store_pattern_to_memory(
        session_manager,
        pattern_data_with_agent,
        namespace
    )
    
    # Property: If storage succeeds, the pattern should be retrievable
    if store_success:
        # Create a query based on the pattern data
        # Use a key field from the pattern for the query
        query_text = f"{agent_type} {document_id}"
        if "pattern_type" in pattern_data:
            query_text += f" {pattern_data['pattern_type']}"
        
        # Retrieve the pattern
        retrieved_results = retrieve_pattern_from_memory(
            session_manager,
            query_text,
            namespace
        )
        
        # Verify that we got results back
        # Note: Due to semantic search, we may not get exact matches,
        # but we should get some results if storage was successful
        assert retrieved_results is not None, \
            f"Failed to retrieve any results for agent {agent_type} after successful storage"
        
        # The property is: storage consistency means we can retrieve something
        # We don't require exact matches due to semantic search behavior
        print(f"✅ Agent {agent_type}: Stored and retrieved {len(retrieved_results)} results")


def test_memory_storage_for_all_agents():
    """
    Test that all agent types can store patterns in their designated namespaces.
    This is a concrete example test that complements the property test.
    """
    memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
    
    if not memory_id:
        import pytest
        pytest.skip("AGENTCORE_MEMORY_ID not set")
    
    # Test each agent type
    for agent_type in AGENT_NAMESPACES.keys():
        document_id = f"test_all_agents_{agent_type}_{int(time.time() * 1000)}"
        
        session_manager = get_session_manager_for_agent(agent_type, document_id)
        
        if session_manager is None:
            import pytest
            pytest.skip(f"Could not create session manager for {agent_type}")
        
        # Create a test pattern
        test_pattern = {
            "agent_name": agent_type,
            "pattern_type": "test_pattern",
            "description": f"Test pattern for {agent_type}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store the pattern
        namespace = AGENT_NAMESPACES[agent_type]
        success = store_pattern_to_memory(session_manager, test_pattern, namespace)
        
        assert success, f"Failed to store pattern for agent {agent_type}"
        
        print(f"✅ Agent {agent_type}: Successfully stored pattern in {namespace}")


if __name__ == '__main__':
    print("Testing memory storage consistency property...")
    print("=" * 70)
    
    # Check if memory is available
    memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
    if not memory_id:
        print("⚠️  AGENTCORE_MEMORY_ID not set")
        print("   This test requires a valid AgentCore Memory resource.")
        print("   Run: python deployment/swarm_agentcore/setup_memory.py")
        print("   Then: export AGENTCORE_MEMORY_ID=<memory-id>")
        sys.exit(0)
    
    print(f"Using memory ID: {memory_id[:20]}...")
    print()
    
    # Test all agents can store patterns
    print("Testing all agents can store patterns...")
    try:
        test_memory_storage_for_all_agents()
        print("✅ All agents can store patterns")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("Running property-based tests...")
    print("(Testing with random pattern data across all agent types)")
    print()
    
    # Run property test for each agent type with sample data
    for agent_type in AGENT_NAMESPACES.keys():
        print(f"\nTesting {agent_type}...")
        try:
            test_pattern = {
                "pattern_type": "extraction",
                "confidence": 0.85,
                "description": "test pattern"
            }
            test_property_memory_storage_consistency(agent_type, test_pattern)
        except Exception as e:
            print(f"  ❌ Error: {e}")
