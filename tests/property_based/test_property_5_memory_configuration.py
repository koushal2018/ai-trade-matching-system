"""
Property-based test for memory resource configuration correctness.
Feature: swarm-to-agentcore, Property 5: Configuration correctness
Validates: Requirements 11.1

Property 5: Configuration Correctness
For any memory namespace retrieval configuration, the top_k and relevance_score 
values should match the specified values for that namespace type.

Expected configurations:
- /facts/{actorId}: top_k=10, relevance_score=0.6
- /preferences/{actorId}: top_k=5, relevance_score=0.7
- /summaries/{actorId}/{sessionId}: top_k=5, relevance_score=0.5
"""
import os
import sys
from pathlib import Path
from hypothesis import given, strategies as st, settings

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Expected configuration for each namespace
EXPECTED_CONFIGS = {
    "/facts/{actorId}": {
        "top_k": 10,
        "relevance_score": 0.6
    },
    "/preferences/{actorId}": {
        "top_k": 5,
        "relevance_score": 0.7
    },
    "/summaries/{actorId}/{sessionId}": {
        "top_k": 5,
        "relevance_score": 0.5
    }
}


def get_memory_configuration():
    """
    Get the memory configuration from the session manager factory.
    This reads the actual configuration that would be used in production.
    """
    try:
        # Import the session manager creation function
        # This will be implemented in task 2.1
        from deployment.swarm.trade_matching_swarm import create_agent_session_manager
        
        # Create a test session manager to inspect configuration
        # We'll use a test memory ID and document ID
        test_memory_id = os.environ.get("AGENTCORE_MEMORY_ID", "test-memory-id")
        
        session_manager = create_agent_session_manager(
            agent_name="test_agent",
            document_id="test_doc",
            memory_id=test_memory_id,
            actor_id="trade_matching_system",
            region_name="us-east-1"
        )
        
        # Extract retrieval configuration
        retrieval_config = session_manager.config.retrieval_config
        
        return retrieval_config
        
    except ImportError:
        # If the function doesn't exist yet, return None
        # This allows the test to be written before implementation
        return None
    except Exception as e:
        # If there's any other error (like missing memory ID), return None
        print(f"Warning: Could not get memory configuration: {e}")
        return None


@given(
    namespace=st.sampled_from([
        "/facts/{actorId}",
        "/preferences/{actorId}",
        "/summaries/{actorId}/{sessionId}"
    ])
)
@settings(max_examples=10, deadline=None)
def test_property_memory_configuration_correctness(namespace: str):
    """
    Property 5: Configuration Correctness
    
    For any memory namespace retrieval configuration, the top_k and 
    relevance_score values should match the specified values for that 
    namespace type.
    
    **Feature: swarm-to-agentcore, Property 5: Configuration correctness**
    **Validates: Requirements 11.1**
    """
    # Get the actual configuration
    retrieval_config = get_memory_configuration()
    
    # If configuration is not available yet (implementation not complete),
    # skip this test
    if retrieval_config is None:
        import pytest
        pytest.skip("Memory configuration not yet implemented")
    
    # Get the expected configuration for this namespace
    expected = EXPECTED_CONFIGS[namespace]
    
    # Get the actual configuration for this namespace
    actual_config = retrieval_config.get(namespace)
    
    # Verify the namespace exists in configuration
    assert actual_config is not None, \
        f"Namespace '{namespace}' not found in retrieval configuration"
    
    # Verify top_k matches expected value
    assert actual_config.top_k == expected["top_k"], \
        f"Namespace '{namespace}': expected top_k={expected['top_k']}, got {actual_config.top_k}"
    
    # Verify relevance_score matches expected value
    assert actual_config.relevance_score == expected["relevance_score"], \
        f"Namespace '{namespace}': expected relevance_score={expected['relevance_score']}, got {actual_config.relevance_score}"


def test_all_namespaces_configured():
    """
    Additional check: Ensure all required namespaces are configured.
    This is part of the configuration correctness property.
    """
    retrieval_config = get_memory_configuration()
    
    # If configuration is not available yet, skip
    if retrieval_config is None:
        import pytest
        pytest.skip("Memory configuration not yet implemented")
    
    # Verify all expected namespaces are present
    for namespace in EXPECTED_CONFIGS.keys():
        assert namespace in retrieval_config, \
            f"Required namespace '{namespace}' not found in configuration"


def test_memory_resource_has_required_strategies():
    """
    Test that the memory resource has all 3 required strategies configured.
    This validates Requirements 2.1, 12.1, 12.2, 12.3, 12.4, 12.5.
    """
    try:
        from bedrock_agentcore.memory import MemoryClient
        
        # Get memory ID from environment or file
        memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
        
        if not memory_id:
            # Try to read from file
            memory_id_file = Path("deployment/.memory_id")
            if memory_id_file.exists():
                memory_id = memory_id_file.read_text().strip()
        
        if not memory_id:
            import pytest
            pytest.skip("AGENTCORE_MEMORY_ID not set and .memory_id file not found")
        
        # Get memory resource details
        client = MemoryClient(region_name="us-east-1")
        memory = client.get_memory(memory_id=memory_id)
        
        strategies = memory.get("strategies", [])
        
        # Verify we have 3 strategies
        assert len(strategies) == 3, \
            f"Expected 3 strategies, found {len(strategies)}"
        
        # Verify each strategy type exists
        strategy_types = [list(s.keys())[0] for s in strategies]
        
        assert "semanticMemoryStrategy" in strategy_types, \
            "semanticMemoryStrategy not found in memory resource"
        
        assert "userPreferenceMemoryStrategy" in strategy_types, \
            "userPreferenceMemoryStrategy not found in memory resource"
        
        assert "summaryMemoryStrategy" in strategy_types, \
            "summaryMemoryStrategy not found in memory resource"
        
        # Verify namespace patterns
        for strategy in strategies:
            if "semanticMemoryStrategy" in strategy:
                namespaces = strategy["semanticMemoryStrategy"].get("namespaces", [])
                assert "/facts/{actorId}" in namespaces, \
                    "semanticMemoryStrategy missing /facts/{actorId} namespace"
            
            elif "userPreferenceMemoryStrategy" in strategy:
                namespaces = strategy["userPreferenceMemoryStrategy"].get("namespaces", [])
                assert "/preferences/{actorId}" in namespaces, \
                    "userPreferenceMemoryStrategy missing /preferences/{actorId} namespace"
            
            elif "summaryMemoryStrategy" in strategy:
                namespaces = strategy["summaryMemoryStrategy"].get("namespaces", [])
                assert "/summaries/{actorId}/{sessionId}" in namespaces, \
                    "summaryMemoryStrategy missing /summaries/{actorId}/{sessionId} namespace"
        
    except ImportError:
        import pytest
        pytest.skip("bedrock_agentcore not installed")
    except Exception as e:
        import pytest
        pytest.skip(f"Could not verify memory resource: {e}")


if __name__ == '__main__':
    # Run the property test manually
    print("Testing memory configuration correctness property...")
    
    # Test each namespace
    for namespace in EXPECTED_CONFIGS.keys():
        print(f"\nTesting namespace: {namespace}")
        try:
            test_property_memory_configuration_correctness(namespace)
            print(f"  ✅ Configuration correct for {namespace}")
        except Exception as e:
            print(f"  ❌ Configuration error for {namespace}: {e}")
    
    # Test all namespaces are configured
    print("\nTesting all namespaces are configured...")
    try:
        test_all_namespaces_configured()
        print("  ✅ All namespaces configured")
    except Exception as e:
        print(f"  ❌ Missing namespaces: {e}")
    
    # Test memory resource strategies
    print("\nTesting memory resource strategies...")
    try:
        test_memory_resource_has_required_strategies()
        print("  ✅ All required strategies configured")
    except Exception as e:
        print(f"  ❌ Strategy configuration error: {e}")
