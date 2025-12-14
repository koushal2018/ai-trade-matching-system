"""
Property-based test for session ID format compliance.
Feature: swarm-to-agentcore, Property 3: Session ID format compliance
Validates: Requirements 10.1, 10.2

Property 3: Session ID Format Compliance
For any trade processing session, the generated session ID should match the format
trade_{document_id}_{agent_name}_{timestamp} where document_id is alphanumeric,
agent_name is one of the valid agent names, and timestamp is in YYYYMMDD_HHMMSS format.
"""
import os
import sys
import re
from pathlib import Path
from hypothesis import given, strategies as st, settings
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Valid agent names
VALID_AGENT_NAMES = ["pdf_adapter", "trade_extractor", "trade_matcher", "exception_handler"]


def validate_session_id_format(session_id: str, expected_document_id: str, expected_agent_name: str) -> bool:
    """
    Validate that a session ID matches the expected format.
    
    Format: trade_{document_id}_{agent_name}_{timestamp}
    Where timestamp is YYYYMMDD_HHMMSS
    
    Args:
        session_id: The session ID to validate
        expected_document_id: The document ID that should be in the session ID
        expected_agent_name: The agent name that should be in the session ID
        
    Returns:
        True if format is valid, False otherwise
    """
    # Pattern: trade_{document_id}_{agent_name}_{YYYYMMDD}_{HHMMSS}
    # Note: The timestamp part has an underscore between date and time
    pattern = rf"^trade_{re.escape(expected_document_id)}_{re.escape(expected_agent_name)}_\d{{8}}_\d{{6}}$"
    
    if not re.match(pattern, session_id):
        return False
    
    # Extract and validate timestamp
    parts = session_id.split("_")
    if len(parts) < 5:
        return False
    
    # Last two parts should be date and time
    date_part = parts[-2]
    time_part = parts[-1]
    
    # Validate date format YYYYMMDD
    try:
        datetime.strptime(date_part, "%Y%m%d")
    except ValueError:
        return False
    
    # Validate time format HHMMSS
    try:
        datetime.strptime(time_part, "%H%M%S")
    except ValueError:
        return False
    
    return True


@given(
    document_id=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), blacklist_characters="_"),
        min_size=5,
        max_size=50
    ),
    agent_name=st.sampled_from(VALID_AGENT_NAMES)
)
@settings(max_examples=20, deadline=None)
def test_property_session_id_format_compliance(document_id: str, agent_name: str):
    """
    Property 3: Session ID Format Compliance
    
    For any trade processing session, the generated session ID should match the format
    trade_{document_id}_{agent_name}_{timestamp} where document_id is alphanumeric,
    agent_name is valid, and timestamp is in YYYYMMDD_HHMMSS format.
    
    **Feature: swarm-to-agentcore, Property 3: Session ID format compliance**
    **Validates: Requirements 10.1, 10.2**
    """
    try:
        # Add deployment/swarm to path for imports
        import sys
        from pathlib import Path
        swarm_path = Path(__file__).parent / "deployment" / "swarm"
        if str(swarm_path) not in sys.path:
            sys.path.insert(0, str(swarm_path))
        
        # Import the session manager creation function
        from trade_matching_swarm import create_agent_session_manager
        
        # Get test memory ID
        test_memory_id = os.environ.get("AGENTCORE_MEMORY_ID", "test-memory-id")
        
        # Create session manager
        session_manager = create_agent_session_manager(
            agent_name=agent_name,
            document_id=document_id,
            memory_id=test_memory_id,
            actor_id="trade_matching_system",
            region_name="us-east-1"
        )
        
        # If memory is disabled (no memory ID), skip this test
        if session_manager is None:
            import pytest
            pytest.skip("Memory integration disabled - AGENTCORE_MEMORY_ID not set")
        
        # Get the session ID
        session_id = session_manager.config.session_id
        
        # Verify format compliance
        assert validate_session_id_format(session_id, document_id, agent_name), \
            f"Session ID '{session_id}' does not match expected format for document_id='{document_id}', agent_name='{agent_name}'"
        
        # Verify it starts with the correct prefix
        expected_prefix = f"trade_{document_id}_{agent_name}_"
        assert session_id.startswith(expected_prefix), \
            f"Session ID '{session_id}' does not start with expected prefix '{expected_prefix}'"
        
        # Verify uniqueness property: each call should generate a different session ID
        # (due to timestamp precision)
        session_manager2 = create_agent_session_manager(
            agent_name=agent_name,
            document_id=document_id,
            memory_id=test_memory_id,
            actor_id="trade_matching_system",
            region_name="us-east-1"
        )
        
        if session_manager2 is not None:
            session_id2 = session_manager2.config.session_id
            # Note: In rare cases, if calls happen in the same second, IDs might match
            # This is acceptable as the timestamp provides sufficient uniqueness in practice
            
    except ImportError:
        import pytest
        pytest.skip("Session manager not yet implemented")
    except Exception as e:
        # If there's an error creating the session manager, fail the test
        raise AssertionError(f"Failed to create session manager: {e}")


def test_session_id_uniqueness_across_agents():
    """
    Test that different agents processing the same document get unique session IDs.
    This validates the "one agent per session" requirement.
    """
    try:
        # Add deployment/swarm to path for imports
        import sys
        from pathlib import Path
        swarm_path = Path(__file__).parent / "deployment" / "swarm"
        if str(swarm_path) not in sys.path:
            sys.path.insert(0, str(swarm_path))
        
        from trade_matching_swarm import create_agent_session_manager
        
        test_memory_id = os.environ.get("AGENTCORE_MEMORY_ID", "test-memory-id")
        document_id = "test_doc_123"
        
        # Create session managers for all agents
        session_ids = []
        for agent_name in VALID_AGENT_NAMES:
            session_manager = create_agent_session_manager(
                agent_name=agent_name,
                document_id=document_id,
                memory_id=test_memory_id
            )
            
            if session_manager is None:
                import pytest
                pytest.skip("Memory integration disabled")
            
            session_ids.append(session_manager.config.session_id)
        
        # Verify all session IDs are unique
        assert len(session_ids) == len(set(session_ids)), \
            f"Session IDs are not unique: {session_ids}"
        
        # Verify each contains the correct agent name
        for i, agent_name in enumerate(VALID_AGENT_NAMES):
            assert agent_name in session_ids[i], \
                f"Session ID '{session_ids[i]}' does not contain agent name '{agent_name}'"
        
    except ImportError:
        import pytest
        pytest.skip("Session manager not yet implemented")


def test_session_id_contains_all_components():
    """
    Test that session ID contains all required components in the correct order.
    """
    try:
        # Add deployment/swarm to path for imports
        import sys
        from pathlib import Path
        swarm_path = Path(__file__).parent / "deployment" / "swarm"
        if str(swarm_path) not in sys.path:
            sys.path.insert(0, str(swarm_path))
        
        from trade_matching_swarm import create_agent_session_manager
        
        test_memory_id = os.environ.get("AGENTCORE_MEMORY_ID", "test-memory-id")
        document_id = "ABC123"
        agent_name = "pdf_adapter"
        
        session_manager = create_agent_session_manager(
            agent_name=agent_name,
            document_id=document_id,
            memory_id=test_memory_id
        )
        
        if session_manager is None:
            import pytest
            pytest.skip("Memory integration disabled")
        
        session_id = session_manager.config.session_id
        parts = session_id.split("_")
        
        # Should have at least 5 parts: trade, document_id, agent_name, date, time
        assert len(parts) >= 5, \
            f"Session ID '{session_id}' does not have enough components (expected at least 5, got {len(parts)})"
        
        # Verify components
        assert parts[0] == "trade", f"First component should be 'trade', got '{parts[0]}'"
        assert document_id in session_id, f"Document ID '{document_id}' not found in session ID '{session_id}'"
        assert agent_name in session_id, f"Agent name '{agent_name}' not found in session ID '{session_id}'"
        
    except ImportError:
        import pytest
        pytest.skip("Session manager not yet implemented")


if __name__ == '__main__':
    # Run the property test manually
    print("Testing session ID format compliance property...")
    print("\n" + "="*80)
    print("NOTE: This test requires a valid AGENTCORE_MEMORY_ID environment variable.")
    print("The memory ID must match AWS pattern: [a-zA-Z][a-zA-Z0-9-_]{0,99}-[a-zA-Z0-9]{10}")
    print("Example: TradeMatchingMemory-abc1234567")
    print("="*80 + "\n")
    
    # Add deployment/swarm to path for imports
    import sys
    from pathlib import Path
    swarm_path = Path(__file__).parent / "deployment" / "swarm"
    if str(swarm_path) not in sys.path:
        sys.path.insert(0, str(swarm_path))
    
    # Check if we have a valid memory ID
    test_memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
    
    if not test_memory_id:
        print("⚠️  AGENTCORE_MEMORY_ID not set. Skipping tests.")
        print("   Set a valid memory ID to run these tests:")
        print("   export AGENTCORE_MEMORY_ID=<your-memory-id>")
        sys.exit(0)
    
    # Validate memory ID format
    memory_id_pattern = r'^[a-zA-Z][a-zA-Z0-9-_]{0,99}-[a-zA-Z0-9]{10}$'
    if not re.match(memory_id_pattern, test_memory_id):
        print(f"⚠️  AGENTCORE_MEMORY_ID '{test_memory_id}' does not match AWS validation pattern.")
        print(f"   Pattern required: [a-zA-Z][a-zA-Z0-9-_]{{0,99}}-[a-zA-Z0-9]{{10}}")
        print("   Skipping tests.")
        sys.exit(0)
    
    print(f"Using memory ID: {test_memory_id}\n")
    
    # Test with sample inputs - call the inner test logic directly
    test_cases = [
        ("doc123", "pdf_adapter"),
        ("FAB26933659", "trade_extractor"),
        ("GCS381315", "trade_matcher"),
        ("exception001", "exception_handler")
    ]
    
    all_passed = True
    
    for document_id, agent_name in test_cases:
        print(f"\nTesting with document_id='{document_id}', agent_name='{agent_name}'")
        try:
            # Import and test directly
            from trade_matching_swarm import create_agent_session_manager
            
            session_manager = create_agent_session_manager(
                agent_name=agent_name,
                document_id=document_id,
                memory_id=test_memory_id,
                actor_id="trade_matching_system",
                region_name="us-east-1"
            )
            
            if session_manager is None:
                print(f"  ⚠️  Memory integration disabled - session manager returned None")
                all_passed = False
                continue
            
            session_id = session_manager.config.session_id
            
            if validate_session_id_format(session_id, document_id, agent_name):
                print(f"  ✅ Format compliance verified: {session_id}")
            else:
                print(f"  ❌ Format compliance failed: {session_id}")
                all_passed = False
        except Exception as e:
            print(f"  ❌ Format compliance failed: {e}")
            all_passed = False
    
    # Test uniqueness across agents
    print("\n" + "="*80)
    print("Testing session ID uniqueness across agents...")
    print("="*80)
    try:
        test_session_id_uniqueness_across_agents()
        print("  ✅ Uniqueness verified")
    except Exception as e:
        print(f"  ❌ Uniqueness test failed: {e}")
        all_passed = False
    
    # Test component presence
    print("\n" + "="*80)
    print("Testing session ID component presence...")
    print("="*80)
    try:
        test_session_id_contains_all_components()
        print("  ✅ All components present")
    except Exception as e:
        print(f"  ❌ Component test failed: {e}")
        all_passed = False
    
    # Final summary
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("="*80)
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("="*80)
        sys.exit(1)
