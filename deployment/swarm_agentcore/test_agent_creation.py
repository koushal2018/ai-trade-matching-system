"""
Unit Tests for Agent Creation

Tests the agent factory functions to ensure:
- Agents are created with session managers
- Each agent has unique session ID
- All agents share same memory resource

Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from trade_matching_swarm import (
    create_pdf_adapter_agent,
    create_trade_extractor_agent,
    create_trade_matcher_agent,
    create_exception_handler_agent,
    create_trade_matching_swarm_with_memory
)


class TestAgentCreation:
    """Unit tests for agent creation with memory integration."""
    
    def test_agents_are_created_with_session_managers(self):
        """
        Test that agents are created with session managers.
        
        Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5
        """
        with patch('trade_matching_swarm.create_agent_session_manager') as mock_create_sm:
            with patch('trade_matching_swarm.Agent') as mock_agent_class:
                with patch('trade_matching_swarm.create_bedrock_model'):
                    # Mock session manager
                    mock_session_manager = Mock()
                    mock_create_sm.return_value = mock_session_manager
                    
                    # Mock agent instance
                    mock_agent = Mock()
                    mock_agent_class.return_value = mock_agent
                    
                    # Test PDF Adapter
                    agent = create_pdf_adapter_agent(
                        document_id="test_doc",
                        memory_id="mem_test_12345"
                    )
                    
                    # Verify session manager was created
                    mock_create_sm.assert_called_with(
                        agent_name="pdf_adapter",
                        document_id="test_doc",
                        memory_id="mem_test_12345"
                    )
                    
                    # Verify agent was created with session manager
                    agent_call_kwargs = mock_agent_class.call_args.kwargs
                    assert agent_call_kwargs.get('session_manager') == mock_session_manager
    
    def test_all_agent_types_have_session_managers(self):
        """
        Test that all four agent types are created with session managers.
        
        Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5
        """
        with patch('trade_matching_swarm.create_agent_session_manager') as mock_create_sm:
            with patch('trade_matching_swarm.Agent') as mock_agent_class:
                with patch('trade_matching_swarm.create_bedrock_model'):
                    mock_session_manager = Mock()
                    mock_create_sm.return_value = mock_session_manager
                    
                    mock_agent = Mock()
                    mock_agent_class.return_value = mock_agent
                    
                    # Test all agent types
                    agent_factories = [
                        ("pdf_adapter", create_pdf_adapter_agent),
                        ("trade_extractor", create_trade_extractor_agent),
                        ("trade_matcher", create_trade_matcher_agent),
                        ("exception_handler", create_exception_handler_agent)
                    ]
                    
                    for agent_name, factory_func in agent_factories:
                        mock_create_sm.reset_mock()
                        mock_agent_class.reset_mock()
                        
                        # Create agent
                        agent = factory_func(
                            document_id="test_doc",
                            memory_id="mem_test_12345"
                        )
                        
                        # Verify session manager was created for this agent
                        mock_create_sm.assert_called_once_with(
                            agent_name=agent_name,
                            document_id="test_doc",
                            memory_id="mem_test_12345"
                        )
                        
                        # Verify agent has session manager
                        agent_call_kwargs = mock_agent_class.call_args.kwargs
                        assert agent_call_kwargs.get('session_manager') == mock_session_manager
    
    def test_each_agent_has_unique_session_id(self):
        """
        Test that each agent gets a unique session ID.
        
        Validates: Requirements 13.1
        """
        with patch('trade_matching_swarm.create_agent_session_manager') as mock_create_sm:
            with patch('trade_matching_swarm.Agent'):
                with patch('trade_matching_swarm.create_bedrock_model'):
                    # Track session manager calls
                    session_manager_calls = []
                    
                    def track_calls(*args, **kwargs):
                        session_manager_calls.append(kwargs.get('agent_name'))
                        mock_sm = Mock()
                        # Create unique session ID for each agent
                        mock_sm.config = Mock()
                        mock_sm.config.session_id = f"trade_test_doc_{kwargs.get('agent_name')}_20240101_120000"
                        return mock_sm
                    
                    mock_create_sm.side_effect = track_calls
                    
                    # Create all four agents
                    pdf_adapter = create_pdf_adapter_agent("test_doc", "mem_test_12345")
                    trade_extractor = create_trade_extractor_agent("test_doc", "mem_test_12345")
                    trade_matcher = create_trade_matcher_agent("test_doc", "mem_test_12345")
                    exception_handler = create_exception_handler_agent("test_doc", "mem_test_12345")
                    
                    # Verify each agent got a session manager call
                    assert len(session_manager_calls) == 4
                    assert "pdf_adapter" in session_manager_calls
                    assert "trade_extractor" in session_manager_calls
                    assert "trade_matcher" in session_manager_calls
                    assert "exception_handler" in session_manager_calls
                    
                    # Verify all agent names are unique (which ensures unique session IDs)
                    assert len(set(session_manager_calls)) == 4
    
    def test_all_agents_share_same_memory_resource(self):
        """
        Test that all agents share the same memory resource ID.
        
        Validates: Requirements 13.1
        """
        with patch('trade_matching_swarm.create_agent_session_manager') as mock_create_sm:
            with patch('trade_matching_swarm.Agent'):
                with patch('trade_matching_swarm.create_bedrock_model'):
                    mock_session_manager = Mock()
                    mock_create_sm.return_value = mock_session_manager
                    
                    memory_id = "mem_shared_12345"
                    
                    # Create all four agents with same memory ID
                    create_pdf_adapter_agent("test_doc", memory_id)
                    create_trade_extractor_agent("test_doc", memory_id)
                    create_trade_matcher_agent("test_doc", memory_id)
                    create_exception_handler_agent("test_doc", memory_id)
                    
                    # Verify all calls used the same memory ID
                    for call_obj in mock_create_sm.call_args_list:
                        assert call_obj.kwargs.get('memory_id') == memory_id
    
    def test_agents_have_correct_names(self):
        """
        Test that agents are created with correct names.
        
        Validates: Requirements 13.2, 13.3, 13.4, 13.5
        """
        with patch('trade_matching_swarm.create_agent_session_manager'):
            with patch('trade_matching_swarm.Agent') as mock_agent_class:
                with patch('trade_matching_swarm.create_bedrock_model'):
                    mock_agent = Mock()
                    mock_agent_class.return_value = mock_agent
                    
                    # Test each agent type
                    test_cases = [
                        (create_pdf_adapter_agent, "pdf_adapter"),
                        (create_trade_extractor_agent, "trade_extractor"),
                        (create_trade_matcher_agent, "trade_matcher"),
                        (create_exception_handler_agent, "exception_handler")
                    ]
                    
                    for factory_func, expected_name in test_cases:
                        mock_agent_class.reset_mock()
                        
                        # Create agent
                        agent = factory_func("test_doc", "mem_test_12345")
                        
                        # Verify agent name
                        agent_call_kwargs = mock_agent_class.call_args.kwargs
                        assert agent_call_kwargs.get('name') == expected_name
    
    def test_agents_have_tools_configured(self):
        """
        Test that agents are created with appropriate tools.
        
        Validates: Requirements 13.2, 13.3, 13.4, 13.5
        """
        with patch('trade_matching_swarm.create_agent_session_manager'):
            with patch('trade_matching_swarm.Agent') as mock_agent_class:
                with patch('trade_matching_swarm.create_bedrock_model'):
                    mock_agent = Mock()
                    mock_agent_class.return_value = mock_agent
                    
                    # Test PDF Adapter tools
                    create_pdf_adapter_agent("test_doc", "mem_test_12345")
                    agent_call_kwargs = mock_agent_class.call_args.kwargs
                    tools = agent_call_kwargs.get('tools', [])
                    assert len(tools) == 3  # download_pdf, extract_text, save_canonical
                    
                    # Test Trade Extractor tools
                    mock_agent_class.reset_mock()
                    create_trade_extractor_agent("test_doc", "mem_test_12345")
                    agent_call_kwargs = mock_agent_class.call_args.kwargs
                    tools = agent_call_kwargs.get('tools', [])
                    assert len(tools) == 2  # store_trade, use_aws
                    
                    # Test Trade Matcher tools
                    mock_agent_class.reset_mock()
                    create_trade_matcher_agent("test_doc", "mem_test_12345")
                    agent_call_kwargs = mock_agent_class.call_args.kwargs
                    tools = agent_call_kwargs.get('tools', [])
                    assert len(tools) == 3  # scan_trades, save_report, use_aws
                    
                    # Test Exception Handler tools
                    mock_agent_class.reset_mock()
                    create_exception_handler_agent("test_doc", "mem_test_12345")
                    agent_call_kwargs = mock_agent_class.call_args.kwargs
                    tools = agent_call_kwargs.get('tools', [])
                    assert len(tools) == 3  # get_guidelines, store_exception, use_aws
    
    def test_swarm_creates_all_agents_with_memory(self):
        """
        Test that swarm creation initializes all agents with memory.
        
        Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5
        """
        with patch('trade_matching_swarm.create_pdf_adapter_agent') as mock_pdf:
            with patch('trade_matching_swarm.create_trade_extractor_agent') as mock_extractor:
                with patch('trade_matching_swarm.create_trade_matcher_agent') as mock_matcher:
                    with patch('trade_matching_swarm.create_exception_handler_agent') as mock_exception:
                        with patch('trade_matching_swarm.Swarm') as mock_swarm_class:
                            # Mock agent instances
                            mock_pdf.return_value = Mock(name="pdf_adapter")
                            mock_extractor.return_value = Mock(name="trade_extractor")
                            mock_matcher.return_value = Mock(name="trade_matcher")
                            mock_exception.return_value = Mock(name="exception_handler")
                            
                            # Create swarm
                            swarm = create_trade_matching_swarm_with_memory(
                                document_id="test_doc",
                                memory_id="mem_test_12345"
                            )
                            
                            # Verify all agents were created with correct parameters
                            mock_pdf.assert_called_once_with("test_doc", "mem_test_12345")
                            mock_extractor.assert_called_once_with("test_doc", "mem_test_12345")
                            mock_matcher.assert_called_once_with("test_doc", "mem_test_12345")
                            mock_exception.assert_called_once_with("test_doc", "mem_test_12345")
    
    def test_agents_without_memory_id_still_work(self):
        """
        Test that agents can be created without memory ID (backward compatibility).
        
        Validates: Requirements 13.1
        """
        with patch('trade_matching_swarm.create_agent_session_manager') as mock_create_sm:
            with patch('trade_matching_swarm.Agent') as mock_agent_class:
                with patch('trade_matching_swarm.create_bedrock_model'):
                    # Session manager returns None when memory_id is None
                    mock_create_sm.return_value = None
                    
                    mock_agent = Mock()
                    mock_agent_class.return_value = mock_agent
                    
                    # Create agent without memory ID
                    agent = create_pdf_adapter_agent(
                        document_id="test_doc",
                        memory_id=None
                    )
                    
                    # Verify agent was still created
                    assert agent is not None
                    
                    # Verify session manager is None
                    agent_call_kwargs = mock_agent_class.call_args.kwargs
                    assert agent_call_kwargs.get('session_manager') is None
    
    def test_agents_use_correct_bedrock_model(self):
        """
        Test that agents use the correct Bedrock model configuration.
        
        Validates: Requirements 13.2, 13.3, 13.4, 13.5
        """
        with patch('trade_matching_swarm.create_agent_session_manager'):
            with patch('trade_matching_swarm.Agent') as mock_agent_class:
                with patch('trade_matching_swarm.create_bedrock_model') as mock_create_model:
                    mock_model = Mock()
                    mock_create_model.return_value = mock_model
                    
                    mock_agent = Mock()
                    mock_agent_class.return_value = mock_agent
                    
                    # Test each agent type
                    agent_types = [
                        (create_pdf_adapter_agent, "pdf_adapter"),
                        (create_trade_extractor_agent, "trade_extractor"),
                        (create_trade_matcher_agent, "trade_matcher"),
                        (create_exception_handler_agent, "exception_handler")
                    ]
                    
                    for factory_func, agent_name in agent_types:
                        mock_create_model.reset_mock()
                        mock_agent_class.reset_mock()
                        
                        # Create agent
                        agent = factory_func("test_doc", "mem_test_12345")
                        
                        # Verify model was created with agent name
                        mock_create_model.assert_called_once_with(agent_name)
                        
                        # Verify agent uses the model
                        agent_call_kwargs = mock_agent_class.call_args.kwargs
                        assert agent_call_kwargs.get('model') == mock_model


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
