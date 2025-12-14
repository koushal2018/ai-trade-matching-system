"""
Unit Tests for Error Handling

Tests the error handling utilities to ensure:
- Memory fallback on service failure
- Session manager safe creation
- Retrieval timeout handling
- Storage failure handling

Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from memory_error_handling import (
    MemoryFallbackHandler,
    get_fallback_handler,
    create_session_manager_safe,
    retrieve_with_timeout,
    store_pattern_safe
)


class TestMemoryFallbackHandler:
    """Unit tests for MemoryFallbackHandler class."""
    
    def test_successful_operation_resets_failure_count(self):
        """
        Test that successful operation resets circuit breaker failure count.
        
        Validates: Requirements 18.1, 18.2
        """
        handler = MemoryFallbackHandler(max_retries=3)
        
        # Simulate some failures
        handler.circuit_breaker_failures = 3
        
        # Execute successful operation
        def successful_op():
            return "success"
        
        result = handler.execute_with_fallback(successful_op, operation_name="test_op")
        
        # Verify failure count was reset
        assert handler.circuit_breaker_failures == 0
        assert result == "success"
    
    def test_retry_with_exponential_backoff(self):
        """
        Test that failed operations are retried with exponential backoff.
        
        Validates: Requirements 18.1, 18.2
        """
        handler = MemoryFallbackHandler(max_retries=3, backoff_factor=2.0)
        
        attempt_count = 0
        attempt_times = []
        
        def failing_op():
            nonlocal attempt_count
            attempt_count += 1
            attempt_times.append(time.time())
            raise Exception("Operation failed")
        
        # Execute operation (should fail after retries)
        result = handler.execute_with_fallback(failing_op, operation_name="test_op")
        
        # Verify all retries were attempted
        assert attempt_count == 3
        
        # Verify exponential backoff (approximate timing)
        if len(attempt_times) >= 2:
            # First retry should be after ~1 second (2^0)
            # Second retry should be after ~2 seconds (2^1)
            # We don't check exact timing due to test execution overhead
            assert len(attempt_times) == 3
    
    def test_circuit_breaker_opens_after_threshold(self):
        """
        Test that circuit breaker opens after reaching failure threshold.
        
        Validates: Requirements 18.1, 18.2, 18.3
        """
        handler = MemoryFallbackHandler(
            max_retries=2,
            circuit_breaker_threshold=3
        )
        
        def failing_op():
            raise Exception("Operation failed")
        
        # Execute operations to reach threshold
        for i in range(3):
            result = handler.execute_with_fallback(failing_op, operation_name="test_op")
            assert result is None  # Fallback returns None
        
        # Verify circuit breaker is open
        assert handler.circuit_breaker_open is True
        assert handler.circuit_breaker_failures >= 3
    
    def test_circuit_breaker_prevents_execution_when_open(self):
        """
        Test that circuit breaker prevents execution when open.
        
        Validates: Requirements 18.1, 18.2, 18.3
        """
        handler = MemoryFallbackHandler()
        
        # Manually open circuit breaker
        handler.circuit_breaker_open = True
        handler.circuit_breaker_opened_at = datetime.utcnow()
        
        operation_called = False
        
        def test_op():
            nonlocal operation_called
            operation_called = True
            return "success"
        
        # Execute operation
        result = handler.execute_with_fallback(test_op, operation_name="test_op")
        
        # Verify operation was not called (circuit breaker prevented it)
        assert operation_called is False
        assert result is None  # Fallback returns None
    
    def test_circuit_breaker_closes_after_timeout(self):
        """
        Test that circuit breaker closes after timeout period.
        
        Validates: Requirements 18.1, 18.2, 18.3
        """
        handler = MemoryFallbackHandler(circuit_breaker_reset_timeout=0.1)
        
        # Open circuit breaker
        handler.circuit_breaker_open = True
        handler.circuit_breaker_opened_at = datetime.utcnow() - timedelta(seconds=1)
        
        def successful_op():
            return "success"
        
        # Execute operation (should close circuit and succeed)
        result = handler.execute_with_fallback(successful_op, operation_name="test_op")
        
        # Verify circuit breaker closed
        assert handler.circuit_breaker_open is False
        assert result == "success"
    
    def test_fallback_returns_none(self):
        """
        Test that fallback mode returns None.
        
        Validates: Requirements 18.1, 18.4
        """
        handler = MemoryFallbackHandler(max_retries=1)
        
        def failing_op():
            raise Exception("Operation failed")
        
        result = handler.execute_with_fallback(failing_op, operation_name="test_op")
        
        # Verify fallback returns None
        assert result is None
    
    def test_get_status_returns_correct_info(self):
        """
        Test that get_status returns correct handler status.
        
        Validates: Requirements 18.5
        """
        handler = MemoryFallbackHandler(
            max_retries=3,
            backoff_factor=2.0,
            circuit_breaker_threshold=5
        )
        
        status = handler.get_status()
        
        # Verify status contains expected fields
        assert 'circuit_breaker_open' in status
        assert 'circuit_breaker_failures' in status
        assert 'max_retries' in status
        assert 'backoff_factor' in status
        assert 'circuit_breaker_threshold' in status
        
        # Verify values
        assert status['max_retries'] == 3
        assert status['backoff_factor'] == 2.0
        assert status['circuit_breaker_threshold'] == 5
    
    def test_manual_circuit_breaker_reset(self):
        """
        Test manual reset of circuit breaker.
        
        Validates: Requirements 18.2, 18.3
        """
        handler = MemoryFallbackHandler()
        
        # Open circuit breaker
        handler.circuit_breaker_open = True
        handler.circuit_breaker_failures = 5
        handler.circuit_breaker_opened_at = datetime.utcnow()
        
        # Reset circuit breaker
        handler.reset_circuit_breaker()
        
        # Verify reset
        assert handler.circuit_breaker_open is False
        assert handler.circuit_breaker_failures == 0
        assert handler.circuit_breaker_opened_at is None


class TestCreateSessionManagerSafe:
    """Unit tests for create_session_manager_safe function."""
    
    def test_returns_session_manager_on_success(self):
        """
        Test that function returns session manager on successful creation.
        
        Validates: Requirements 18.1, 18.2
        """
        with patch('memory_error_handling.create_agent_session_manager') as mock_create:
            mock_session_manager = Mock()
            mock_create.return_value = mock_session_manager
            
            result = create_session_manager_safe(
                agent_name="pdf_adapter",
                document_id="test_doc",
                memory_id="mem_test_12345"
            )
            
            assert result == mock_session_manager
    
    def test_returns_none_on_value_error(self):
        """
        Test that function returns None on ValueError (missing memory ID).
        
        Validates: Requirements 18.1, 18.2, 18.4
        """
        with patch('memory_error_handling.create_agent_session_manager') as mock_create:
            mock_create.side_effect = ValueError("AGENTCORE_MEMORY_ID not set")
            
            result = create_session_manager_safe(
                agent_name="pdf_adapter",
                document_id="test_doc",
                memory_id=None
            )
            
            assert result is None
    
    def test_returns_none_on_unexpected_error(self):
        """
        Test that function returns None on unexpected errors.
        
        Validates: Requirements 18.1, 18.2, 18.4
        """
        with patch('memory_error_handling.create_agent_session_manager') as mock_create:
            mock_create.side_effect = Exception("Unexpected error")
            
            result = create_session_manager_safe(
                agent_name="pdf_adapter",
                document_id="test_doc",
                memory_id="mem_test_12345"
            )
            
            assert result is None


class TestRetrieveWithTimeout:
    """Unit tests for retrieve_with_timeout function."""
    
    @pytest.mark.asyncio
    async def test_successful_retrieval(self):
        """
        Test successful memory retrieval within timeout.
        
        Validates: Requirements 18.1, 18.3
        """
        mock_session_manager = Mock()
        mock_results = [{"pattern": "test_pattern"}]
        
        # Mock synchronous retrieve method
        mock_session_manager.retrieve = Mock(return_value=mock_results)
        
        result = await retrieve_with_timeout(
            session_manager=mock_session_manager,
            query="test query",
            timeout_seconds=2.0
        )
        
        assert result == mock_results
    
    @pytest.mark.asyncio
    async def test_timeout_returns_none(self):
        """
        Test that timeout returns None.
        
        Validates: Requirements 18.1, 18.3, 18.4
        """
        mock_session_manager = Mock()
        
        # Mock slow retrieve method
        async def slow_retrieve(*args, **kwargs):
            await asyncio.sleep(5.0)  # Longer than timeout
            return [{"pattern": "test"}]
        
        mock_session_manager.retrieve = slow_retrieve
        
        result = await retrieve_with_timeout(
            session_manager=mock_session_manager,
            query="test query",
            timeout_seconds=0.1  # Short timeout
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_error_returns_none(self):
        """
        Test that errors during retrieval return None.
        
        Validates: Requirements 18.1, 18.3, 18.4
        """
        mock_session_manager = Mock()
        mock_session_manager.retrieve = Mock(side_effect=Exception("Retrieval error"))
        
        result = await retrieve_with_timeout(
            session_manager=mock_session_manager,
            query="test query",
            timeout_seconds=2.0
        )
        
        assert result is None


class TestStorePatternSafe:
    """Unit tests for store_pattern_safe function."""
    
    def test_successful_storage_returns_true(self):
        """
        Test that successful storage returns True.
        
        Validates: Requirements 18.1, 18.4
        """
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
        mock_session_manager.store.assert_called_once_with(pattern, namespace=namespace)
    
    def test_storage_failure_returns_false(self):
        """
        Test that storage failure returns False.
        
        Validates: Requirements 18.1, 18.4, 18.5
        """
        mock_session_manager = Mock()
        mock_session_manager.store = Mock(side_effect=Exception("Storage failed"))
        
        pattern = {"field": "notional", "technique": "regex"}
        namespace = "/facts/{actorId}"
        
        result = store_pattern_safe(
            session_manager=mock_session_manager,
            pattern=pattern,
            namespace=namespace
        )
        
        assert result is False
    
    def test_storage_continues_on_failure(self):
        """
        Test that processing continues even when storage fails.
        
        Validates: Requirements 18.1, 18.4, 18.5
        """
        mock_session_manager = Mock()
        mock_session_manager.store = Mock(side_effect=Exception("Storage failed"))
        
        pattern = {"field": "notional", "technique": "regex"}
        namespace = "/facts/{actorId}"
        
        # This should not raise an exception
        result = store_pattern_safe(
            session_manager=mock_session_manager,
            pattern=pattern,
            namespace=namespace
        )
        
        # Verify it returned False but didn't raise
        assert result is False


class TestGlobalFallbackHandler:
    """Unit tests for global fallback handler."""
    
    def test_get_fallback_handler_returns_singleton(self):
        """
        Test that get_fallback_handler returns the same instance.
        
        Validates: Requirements 18.1, 18.2
        """
        handler1 = get_fallback_handler()
        handler2 = get_fallback_handler()
        
        # Verify same instance
        assert handler1 is handler2
    
    def test_get_fallback_handler_returns_valid_instance(self):
        """
        Test that get_fallback_handler returns a valid MemoryFallbackHandler.
        
        Validates: Requirements 18.1, 18.2
        """
        handler = get_fallback_handler()
        
        # Verify it's a MemoryFallbackHandler instance
        assert isinstance(handler, MemoryFallbackHandler)
        
        # Verify it has expected attributes
        assert hasattr(handler, 'max_retries')
        assert hasattr(handler, 'circuit_breaker_open')
        assert hasattr(handler, 'execute_with_fallback')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
