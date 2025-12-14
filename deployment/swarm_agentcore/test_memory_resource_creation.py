"""
Unit Tests for Memory Resource Creation

Tests the create_trade_matching_memory() function to ensure:
- Valid memory ID is returned
- Memory resource has semantic strategy
- Memory resource has user preference strategy
- Memory resource has summary strategy

Validates: Requirements 2.1, 12.1, 12.2, 12.3, 12.4, 12.5
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from setup_memory import create_trade_matching_memory


class TestMemoryResourceCreation:
    """Unit tests for memory resource creation."""
    
    def test_create_memory_returns_valid_id(self):
        """
        Test that create_trade_matching_memory() returns a valid memory ID.
        
        Validates: Requirements 2.1, 12.1, 12.4
        """
        with patch('setup_memory.MemoryClient') as mock_client_class:
            # Mock the client instance
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock the create_memory_and_wait response
            mock_memory = {
                'id': 'mem_test_12345',
                'name': 'TradeMatchingMemory',
                'status': 'AVAILABLE'
            }
            mock_client.create_memory_and_wait.return_value = mock_memory
            
            # Call the function
            memory_id = create_trade_matching_memory(region_name="us-east-1")
            
            # Verify memory ID is returned
            assert memory_id is not None
            assert len(memory_id) > 0
            assert memory_id == 'mem_test_12345'
            
            # Verify client was created with correct region
            mock_client_class.assert_called_once_with(region_name="us-east-1")
    
    def test_memory_resource_has_semantic_strategy(self):
        """
        Test that memory resource includes semantic memory strategy.
        
        Validates: Requirements 2.1, 12.2
        """
        with patch('setup_memory.MemoryClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            mock_memory = {'id': 'mem_test_12345'}
            mock_client.create_memory_and_wait.return_value = mock_memory
            
            # Call the function
            create_trade_matching_memory()
            
            # Get the call arguments
            call_args = mock_client.create_memory_and_wait.call_args
            strategies = call_args.kwargs['strategies']
            
            # Verify semantic strategy is present
            semantic_strategies = [
                s for s in strategies 
                if 'semanticMemoryStrategy' in s
            ]
            assert len(semantic_strategies) == 1
            
            # Verify semantic strategy configuration
            semantic_strategy = semantic_strategies[0]['semanticMemoryStrategy']
            assert semantic_strategy['name'] == 'TradeFacts'
            assert '/facts/{actorId}' in semantic_strategy['namespaces']
    
    def test_memory_resource_has_user_preference_strategy(self):
        """
        Test that memory resource includes user preference memory strategy.
        
        Validates: Requirements 2.1, 12.3
        """
        with patch('setup_memory.MemoryClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            mock_memory = {'id': 'mem_test_12345'}
            mock_client.create_memory_and_wait.return_value = mock_memory
            
            # Call the function
            create_trade_matching_memory()
            
            # Get the call arguments
            call_args = mock_client.create_memory_and_wait.call_args
            strategies = call_args.kwargs['strategies']
            
            # Verify user preference strategy is present
            preference_strategies = [
                s for s in strategies 
                if 'userPreferenceMemoryStrategy' in s
            ]
            assert len(preference_strategies) == 1
            
            # Verify user preference strategy configuration
            preference_strategy = preference_strategies[0]['userPreferenceMemoryStrategy']
            assert preference_strategy['name'] == 'ProcessingPreferences'
            assert '/preferences/{actorId}' in preference_strategy['namespaces']
    
    def test_memory_resource_has_summary_strategy(self):
        """
        Test that memory resource includes summary memory strategy.
        
        Validates: Requirements 2.1, 12.4
        """
        with patch('setup_memory.MemoryClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            mock_memory = {'id': 'mem_test_12345'}
            mock_client.create_memory_and_wait.return_value = mock_memory
            
            # Call the function
            create_trade_matching_memory()
            
            # Get the call arguments
            call_args = mock_client.create_memory_and_wait.call_args
            strategies = call_args.kwargs['strategies']
            
            # Verify summary strategy is present
            summary_strategies = [
                s for s in strategies 
                if 'summaryMemoryStrategy' in s
            ]
            assert len(summary_strategies) == 1
            
            # Verify summary strategy configuration
            summary_strategy = summary_strategies[0]['summaryMemoryStrategy']
            assert summary_strategy['name'] == 'SessionSummaries'
            assert '/summaries/{actorId}/{sessionId}' in summary_strategy['namespaces']
    
    def test_memory_resource_has_all_three_strategies(self):
        """
        Test that memory resource includes all three strategies.
        
        Validates: Requirements 2.1, 12.2, 12.3, 12.4
        """
        with patch('setup_memory.MemoryClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            mock_memory = {'id': 'mem_test_12345'}
            mock_client.create_memory_and_wait.return_value = mock_memory
            
            # Call the function
            create_trade_matching_memory()
            
            # Get the call arguments
            call_args = mock_client.create_memory_and_wait.call_args
            strategies = call_args.kwargs['strategies']
            
            # Verify all three strategies are present
            assert len(strategies) == 3
            
            strategy_types = [list(s.keys())[0] for s in strategies]
            assert 'semanticMemoryStrategy' in strategy_types
            assert 'userPreferenceMemoryStrategy' in strategy_types
            assert 'summaryMemoryStrategy' in strategy_types
    
    def test_memory_creation_uses_correct_name(self):
        """
        Test that memory resource is created with correct name.
        
        Validates: Requirements 12.1
        """
        with patch('setup_memory.MemoryClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            mock_memory = {'id': 'mem_test_12345'}
            mock_client.create_memory_and_wait.return_value = mock_memory
            
            # Call the function
            create_trade_matching_memory()
            
            # Verify name is correct
            call_args = mock_client.create_memory_and_wait.call_args
            assert call_args.kwargs['name'] == 'TradeMatchingMemory'
    
    def test_memory_creation_error_handling(self):
        """
        Test that memory creation handles errors appropriately.
        
        Validates: Requirements 12.5
        """
        with patch('setup_memory.MemoryClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Simulate an error
            mock_client.create_memory_and_wait.side_effect = Exception("Service unavailable")
            
            # Verify exception is raised
            with pytest.raises(Exception) as exc_info:
                create_trade_matching_memory()
            
            assert "Service unavailable" in str(exc_info.value)
    
    def test_memory_creation_missing_id_error(self):
        """
        Test that memory creation handles missing ID in response.
        
        Validates: Requirements 12.4
        """
        with patch('setup_memory.MemoryClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Return memory without ID
            mock_memory = {'name': 'TradeMatchingMemory'}
            mock_client.create_memory_and_wait.return_value = mock_memory
            
            # Verify ValueError is raised
            with pytest.raises(ValueError) as exc_info:
                create_trade_matching_memory()
            
            assert "no ID was returned" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
