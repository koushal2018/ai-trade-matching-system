"""
Unit tests for memory error handling module.

Tests the MemoryFallbackHandler, create_session_manager_safe,
retrieve_with_timeout, and store_pattern_safe functions.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from memory_error_handling import (
    MemoryFallbackHandler,
    get_fallback_handler,
    create_session_manager_safe,
    retrieve_with_timeout,
    store_pattern_safe
)


class TestMemoryFallbackHandler:
    """Test suite for MemoryFallbackHandler class."""
    
    def test_initialization(self):
        """Test that handler initializes with correct defaults."""
        handler = MemoryFallbackHandler()
        
        assert handler.max_retries == 3
        assert handler.backoff_factor == 2.0
        assert handler.circuit_breaker_threshold == 5
        assert handler.circuit_breaker_failures == 0
        assert handler.circuit_breaker_open is False
    
    def test_successful_operation(self):
        """Test that successful operations reset failure count."""
        handler = MemoryFallbackHandler(max_retries=2)
        handler.circuit_breaker_failures = 3
        
        def successful_op():
            return "success"
        
        result = handler.execute_with_fallback(
            successful_op,
            operation_name="test_op"
        )
        
        assert result == "success"
        assert handler.circuit_breaker_failures == 0
    
    def test_retry_with_exponential_backoff(self):
        """Test that operations retry with exponential backoff."""
        handler = MemoryFallbackHandler(max_retries=3, backoff_factor=2.0)
        
        call_count = 0
        call_times = []
        
        def failing_then_success():
            nonlocal call_count
            call_times.append(time.time())
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        start_time = time.time()
        result = handler.execute_with_fallback(
            failing_then_success,
            operation_name="test_retry"
        )
        
        assert result == "success"
        assert call_count == 3
        
        # Verify exponential backoff (1s, 2s between retries)
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            assert delay1 >= 1.0  # First retry after 2^0 = 1s
            assert delay2 >= 2.0  # Second retry after 2^1 = 2s
    
    def test_circuit_breaker_opens_after_threshold(self):
        """Test that circuit breaker opens after threshold failures."""
        handler = MemoryFallbackHandler(
            max_retries=1,
            circuit_breaker_threshold=2
        )
        
        def always_fails():
            raise Exception("Always fails")
        
        # First failure
        result1 = handler.execute_with_fallback(
            always_fails,
            operation_name="test_circuit"
        )
        assert result1 is None
        assert handler.circuit_breaker_failures == 1
        assert handler.circuit_breaker_open is False
        
        # Second failure - should open circuit
        result2 = handler.execute_with_fallback(
            always_fails,
            operation_name="test_circuit"
        )
        assert result2 is None
        assert handler.circuit_breaker_failures == 2
        assert handler.circuit_breaker_open is True
    
    def test_circuit_breaker_prevents_execution(self):
        """Test that open circuit breaker prevents operation execution."""
        handler = MemoryFallbackHandler()
        handler.circuit_breaker_open = True
        handler.circuit_breaker_opened_at = datetime.utcnow()
        
        call_count = 0
        
        def should_not_be_called():
            nonlocal call_count
            call_count += 1
            return "should not execute"
        
        result = handler.execute_with_fallback(
            should_not_be_called,
            operation_name="test_open_circuit"
        )
        
        assert result is None
        assert call_count == 0  # Operation should not be called
    
    def test_manual_reset(self):
        """Test manual circuit breaker reset."""
        handler = MemoryFallbackHandler()
        handler.circuit_breaker_open = True
        handler.circuit_breaker_failures = 5
        handler.circuit_breaker_opened_at = datetime.utcnow()
        
        handler.reset_circuit_breaker()
        
        assert handler.circuit_breaker_open is False
        assert handler.circuit_breaker_failures == 0
        assert handler.circuit_breaker_opened_at is None
    
    def test_get_status(self):
        """Test status reporting."""
        handler = MemoryFallbackHandler(max_retries=5, backoff_factor=3.0)
        handler.circuit_breaker_failures = 2
        
        status = handler.get_status()
        
        assert status["circuit_breaker_open"] is False
        assert status["circuit_breaker_failures"] == 2
        assert status["max_retries"] == 5
        assert status["backoff_factor"] == 3.0


class TestCreateSessionManagerSafe:
    """Test suite for create_session_manager_safe function."""
    
    @patch('memory_error_handling.create_agent_session_manager')
    def test_successful_creation(self, mock_create):
        """Test successful session manager creation."""
        mock_session_manager = Mock()
        mock_create.return_value = mock_session_manager
        
        result = create_session_manager_safe(
            agent_name="test_agent",
            document_id="test_doc_123",
            memory_id="test_memory_id"
        )
        
        assert result == mock_session_manager
        mock_create.assert_called_once()
    
    @patch('memory_error_handling.create_agent_session_manager')
    def test_value_error_handling(self, mock_create):
        """Test that ValueError is caught and None is returned."""
        mock_create.side_effect = ValueError("Invalid memory ID")
        
        result = create_session_manager_safe(
            agent_name="test_agent",
            document_id="test_doc_123",
            memory_id="invalid_id"
        )
        
        assert result is None
    
    @patch('memory_error_handling.create_agent_session_manager')
    def test_generic_exception_handling(self, mock_create):
        """Test that generic exceptions are caught and None is returned."""
        mock_create.side_effect = Exception("Network error")
        
        result = create_session_manager_safe(
            agent_name="test_agent",
            document_id="test_doc_123",
            memory_id="test_memory_id"
        )
        
        assert result is None


class TestRetrieveWithTimeout:
    """Test suite for retrieve_with_timeout async function."""
    
    @pytest.mark.asyncio
    async def test_successful_retrieval(self):
        """Test successful memory retrieval within timeout."""
        mock_session_manager = Mock()
        mock_session_manager.retrieve = Mock(return_value=[
            {"pattern": "test_pattern", "relevance": 0.8}
        ])
        
        result = await retrieve_with_timeout(
            session_manager=mock_session_manager,
            query="test query",
            namespace="/facts/{actorId}",
            timeout_seconds=2.0
        )
        
        assert result is not None
        assert len(result) == 1
        assert result[0]["pattern"] == "test_pattern"
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that timeout returns None."""
        mock_session_manager = Mock()
        
        async def slow_retrieve(*args, **kwargs):
            await asyncio.sleep(5.0)  # Longer than timeout
            return [{"pattern": "test"}]
        
        mock_session_manager.retrieve = slow_retrieve
        
        result = await retrieve_with_timeout(
            session_manager=mock_session_manager,
            query="test query",
            timeout_seconds=0.5
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Test that exceptions return None."""
        mock_session_manager = Mock()
        mock_session_manager.retrieve = Mock(side_effect=Exception("Retrieval error"))
        
        result = await retrieve_with_timeout(
            session_manager=mock_session_manager,
            query="test query",
            timeout_seconds=2.0
        )
        
        assert result is None


class TestStorePatternSafe:
    """Test suite for store_pattern_safe function."""
    
    def test_successful_storage(self):
        """Test successful pattern storage."""
        mock_session_manager = Mock()
        mock_session_manager.store = Mock()
        
        pattern = {"field": "notional", "technique": "regex"}
        namespace = "/facts/{actorId}"
        
        result = store_pattern_safe(
            session_manager=mock_session_manager,
            pattern=pattern,
            namespace=namespace
        )
        
        assert result is True
        mock_session_manager.store.assert_called_once_with(
            pattern,
            namespace=namespace
        )
    
    def test_storage_failure(self):
        """Test that storage failures return False."""
        mock_session_manager = Mock()
        mock_session_manager.store = Mock(side_effect=Exception("Storage error"))
        
        pattern = {"field": "notional", "technique": "regex"}
        namespace = "/facts/{actorId}"
        
        result = store_pattern_safe(
            session_manager=mock_session_manager,
            pattern=pattern,
            namespace=namespace
        )
        
        assert result is False


class TestGlobalFallbackHandler:
    """Test suite for global fallback handler."""
    
    def test_get_fallback_handler_singleton(self):
        """Test that get_fallback_handler returns singleton instance."""
        handler1 = get_fallback_handler()
        handler2 = get_fallback_handler()
        
        assert handler1 is handler2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
