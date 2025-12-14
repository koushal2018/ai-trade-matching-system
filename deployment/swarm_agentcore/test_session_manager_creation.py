"""
Unit Tests for Session Manager Creation

Tests the create_agent_session_manager() function to ensure:
- Valid session manager is returned
- Session ID format is correct
- Retrieval configs are set correctly
- Error handling for missing memory ID

Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5
"""

import pytest
import os
import re
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from trade_matching_swarm import create_agent_session_manager


class TestSessionManagerCreation:
    """Unit tests for session manager creation."""
    
    def test_create_session_manager_returns_valid_instance(self):
        """
        Test that create_agent_session_manager() returns a valid session manager.
        
        Validates: Requirements 10.1, 10.3
        """
        with patch('trade_matching_swarm.AgentCoreMemorySessionManager') as mock_sm_class:
            # Mock the session manager instance
            mock_session_manager = Mock()
            mock_sm_class.return_value = mock_session_manager
            
            # Call the function
            session_manager = create_agent_session_manager(
                agent_name="pdf_adapter",
                document_id="test_doc_123",
                memory_id="mem_test_12345"
            )
            
            # Verify session manager is returned
            assert session_manager is not None
            assert session_manager == mock_session_manager
            
            # Verify session manager was created
            mock_sm_class.assert_called_once()
    
    def test_session_id_format_is_correct(self):
        """
        Test that session ID follows the correct format: trade_{document_id}_{agent_name}_{timestamp}.
        
        Validates: Requirements 10.1, 10.2
        """
        with patch('trade_matching_swarm.AgentCoreMemorySessionManager') as mock_sm_class:
            with patch('trade_matching_swarm.AgentCoreMemoryConfig') as mock_config_class:
                mock_session_manager = Mock()
                mock_sm_class.return_value = mock_session_manager
                
                # Capture the config that was created
                captured_config = None
                def capture_config(*args, **kwargs):
                    nonlocal captured_config
                    captured_config = Mock()
                    captured_config.session_id = kwargs.get('session_id')
                    return captured_config
                
                mock_config_class.side_effect = capture_config
                
                # Call the function
                session_manager = create_agent_session_manager(
                    agent_name="trade_extractor",
                    document_id="doc_abc_123",
                    memory_id="mem_test_12345"
                )
                
                # Verify session ID format
                session_id = captured_config.session_id
                assert session_id is not None
                
                # Check format: trade_{document_id}_{agent_name}_{timestamp}
                assert session_id.startswith("trade_doc_abc_123_trade_extractor_")
                
                # Extract timestamp part
                parts = session_id.split("_")
                assert len(parts) >= 5  # trade, doc, abc, 123, trade, extractor, timestamp
                
                # Verify timestamp format (YYYYMMDD_HHMMSS)
                timestamp_part = "_".join(parts[-2:])  # Last two parts should be date_time
                assert re.match(r'\d{8}_\d{6}', timestamp_part), \
                    f"Timestamp part '{timestamp_part}' doesn't match YYYYMMDD_HHMMSS format"
    
    def test_session_id_includes_agent_name(self):
        """
        Test that session ID includes the agent name.
        
        Validates: Requirements 10.1, 10.2
        """
        with patch('trade_matching_swarm.AgentCoreMemorySessionManager') as mock_sm_class:
            with patch('trade_matching_swarm.AgentCoreMemoryConfig') as mock_config_class:
                mock_session_manager = Mock()
                mock_sm_class.return_value = mock_session_manager
                
                captured_config = None
                def capture_config(*args, **kwargs):
                    nonlocal captured_config
                    captured_config = Mock()
                    captured_config.session_id = kwargs.get('session_id')
                    return captured_config
                
                mock_config_class.side_effect = capture_config
                
                # Test with different agent names
                for agent_name in ["pdf_adapter", "trade_extractor", "trade_matcher", "exception_handler"]:
                    session_manager = create_agent_session_manager(
                        agent_name=agent_name,
                        document_id="test_doc",
                        memory_id="mem_test_12345"
                    )
                    
                    session_id = captured_config.session_id
                    assert agent_name in session_id, \
                        f"Agent name '{agent_name}' not found in session ID '{session_id}'"
    
    def test_retrieval_configs_are_set_correctly(self):
        """
        Test that retrieval configs are set correctly for all namespaces.
        
        Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5
        """
        with patch('trade_matching_swarm.AgentCoreMemorySessionManager') as mock_sm_class:
            with patch('trade_matching_swarm.AgentCoreMemoryConfig') as mock_config_class:
                with patch('trade_matching_swarm.RetrievalConfig') as mock_retrieval_config_class:
                    mock_session_manager = Mock()
                    mock_sm_class.return_value = mock_session_manager
                    
                    captured_retrieval_configs = {}
                    
                    def capture_retrieval_config(*args, **kwargs):
                        config = Mock()
                        config.top_k = kwargs.get('top_k')
                        config.relevance_score = kwargs.get('relevance_score')
                        return config
                    
                    mock_retrieval_config_class.side_effect = capture_retrieval_config
                    
                    captured_config = None
                    def capture_config(*args, **kwargs):
                        nonlocal captured_config
                        captured_config = Mock()
                        captured_config.retrieval_config = kwargs.get('retrieval_config', {})
                        return captured_config
                    
                    mock_config_class.side_effect = capture_config
                    
                    # Call the function
                    session_manager = create_agent_session_manager(
                        agent_name="pdf_adapter",
                        document_id="test_doc",
                        memory_id="mem_test_12345"
                    )
                    
                    # Verify retrieval configs
                    retrieval_config = captured_config.retrieval_config
                    
                    # Check /facts/{actorId} config
                    facts_config = retrieval_config.get("/facts/{actorId}")
                    assert facts_config is not None
                    assert facts_config.top_k == 10
                    assert facts_config.relevance_score == 0.6
                    
                    # Check /preferences/{actorId} config
                    prefs_config = retrieval_config.get("/preferences/{actorId}")
                    assert prefs_config is not None
                    assert prefs_config.top_k == 5
                    assert prefs_config.relevance_score == 0.7
                    
                    # Check /summaries/{actorId}/{sessionId} config
                    summaries_config = retrieval_config.get("/summaries/{actorId}/{sessionId}")
                    assert summaries_config is not None
                    assert summaries_config.top_k == 5
                    assert summaries_config.relevance_score == 0.5
    
    def test_error_handling_for_missing_memory_id(self):
        """
        Test error handling when memory ID is missing.
        
        Validates: Requirements 10.4, 10.5
        """
        # Clear environment variable if set
        original_memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
        if "AGENTCORE_MEMORY_ID" in os.environ:
            del os.environ["AGENTCORE_MEMORY_ID"]
        
        try:
            # Call without memory_id parameter and without environment variable
            session_manager = create_agent_session_manager(
                agent_name="pdf_adapter",
                document_id="test_doc",
                memory_id=None  # Explicitly None
            )
            
            # Should return None when memory ID is missing
            assert session_manager is None
            
        finally:
            # Restore original environment variable
            if original_memory_id:
                os.environ["AGENTCORE_MEMORY_ID"] = original_memory_id
    
    def test_session_manager_uses_environment_memory_id(self):
        """
        Test that session manager uses memory ID from environment if not provided.
        
        Validates: Requirements 10.3, 10.4
        """
        with patch('trade_matching_swarm.AgentCoreMemorySessionManager') as mock_sm_class:
            with patch('trade_matching_swarm.AgentCoreMemoryConfig') as mock_config_class:
                mock_session_manager = Mock()
                mock_sm_class.return_value = mock_session_manager
                
                captured_config = None
                def capture_config(*args, **kwargs):
                    nonlocal captured_config
                    captured_config = Mock()
                    captured_config.memory_id = kwargs.get('memory_id')
                    return captured_config
                
                mock_config_class.side_effect = capture_config
                
                # Set environment variable
                os.environ["AGENTCORE_MEMORY_ID"] = "mem_from_env_12345"
                
                try:
                    # Call without memory_id parameter
                    session_manager = create_agent_session_manager(
                        agent_name="pdf_adapter",
                        document_id="test_doc",
                        memory_id=None
                    )
                    
                    # Verify memory ID from environment was used
                    assert captured_config.memory_id == "mem_from_env_12345"
                    
                finally:
                    # Clean up environment variable
                    if "AGENTCORE_MEMORY_ID" in os.environ:
                        del os.environ["AGENTCORE_MEMORY_ID"]
    
    def test_session_manager_uses_correct_actor_id(self):
        """
        Test that session manager uses the correct actor ID.
        
        Validates: Requirements 10.3
        """
        with patch('trade_matching_swarm.AgentCoreMemorySessionManager') as mock_sm_class:
            with patch('trade_matching_swarm.AgentCoreMemoryConfig') as mock_config_class:
                mock_session_manager = Mock()
                mock_sm_class.return_value = mock_session_manager
                
                captured_config = None
                def capture_config(*args, **kwargs):
                    nonlocal captured_config
                    captured_config = Mock()
                    captured_config.actor_id = kwargs.get('actor_id')
                    return captured_config
                
                mock_config_class.side_effect = capture_config
                
                # Call with default actor_id
                session_manager = create_agent_session_manager(
                    agent_name="pdf_adapter",
                    document_id="test_doc",
                    memory_id="mem_test_12345"
                )
                
                # Verify default actor ID
                assert captured_config.actor_id == "trade_matching_system"
                
                # Call with custom actor_id
                session_manager = create_agent_session_manager(
                    agent_name="pdf_adapter",
                    document_id="test_doc",
                    memory_id="mem_test_12345",
                    actor_id="custom_actor"
                )
                
                # Verify custom actor ID
                assert captured_config.actor_id == "custom_actor"
    
    def test_session_manager_uses_correct_region(self):
        """
        Test that session manager uses the correct AWS region.
        
        Validates: Requirements 10.5
        """
        with patch('trade_matching_swarm.AgentCoreMemorySessionManager') as mock_sm_class:
            mock_session_manager = Mock()
            mock_sm_class.return_value = mock_session_manager
            
            # Call with default region
            session_manager = create_agent_session_manager(
                agent_name="pdf_adapter",
                document_id="test_doc",
                memory_id="mem_test_12345"
            )
            
            # Verify default region
            call_kwargs = mock_sm_class.call_args.kwargs
            assert call_kwargs.get('region_name') == "us-east-1"
            
            # Call with custom region
            session_manager = create_agent_session_manager(
                agent_name="pdf_adapter",
                document_id="test_doc",
                memory_id="mem_test_12345",
                region_name="eu-west-1"
            )
            
            # Verify custom region
            call_kwargs = mock_sm_class.call_args.kwargs
            assert call_kwargs.get('region_name') == "eu-west-1"
    
    def test_unique_session_ids_for_different_agents(self):
        """
        Test that different agents get unique session IDs.
        
        Validates: Requirements 10.1, 10.2
        """
        with patch('trade_matching_swarm.AgentCoreMemorySessionManager') as mock_sm_class:
            with patch('trade_matching_swarm.AgentCoreMemoryConfig') as mock_config_class:
                mock_session_manager = Mock()
                mock_sm_class.return_value = mock_session_manager
                
                session_ids = []
                
                def capture_config(*args, **kwargs):
                    config = Mock()
                    config.session_id = kwargs.get('session_id')
                    session_ids.append(config.session_id)
                    return config
                
                mock_config_class.side_effect = capture_config
                
                # Create session managers for different agents
                agents = ["pdf_adapter", "trade_extractor", "trade_matcher", "exception_handler"]
                for agent_name in agents:
                    create_agent_session_manager(
                        agent_name=agent_name,
                        document_id="test_doc",
                        memory_id="mem_test_12345"
                    )
                
                # Verify all session IDs are unique
                assert len(session_ids) == len(set(session_ids)), \
                    "Session IDs are not unique across agents"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
