"""
Simple validation script for memory error handling module.
Tests basic functionality without requiring pytest.
"""

import sys
import time
from datetime import datetime

# Import the error handling module
try:
    from memory_error_handling import (
        MemoryFallbackHandler,
        get_fallback_handler,
        store_pattern_safe
    )
    print("✓ Successfully imported memory_error_handling module")
except ImportError as e:
    print(f"✗ Failed to import memory_error_handling: {e}")
    sys.exit(1)


def test_handler_initialization():
    """Test MemoryFallbackHandler initialization."""
    print("\n--- Testing MemoryFallbackHandler Initialization ---")
    
    handler = MemoryFallbackHandler(
        max_retries=3,
        backoff_factor=2.0,
        circuit_breaker_threshold=5
    )
    
    assert handler.max_retries == 3, "max_retries not set correctly"
    assert handler.backoff_factor == 2.0, "backoff_factor not set correctly"
    assert handler.circuit_breaker_threshold == 5, "threshold not set correctly"
    assert handler.circuit_breaker_open is False, "circuit should start closed"
    assert handler.circuit_breaker_failures == 0, "failures should start at 0"
    
    print("✓ Handler initialized correctly")
    return True


def test_successful_operation():
    """Test successful operation execution."""
    print("\n--- Testing Successful Operation ---")
    
    handler = MemoryFallbackHandler(max_retries=2)
    
    def successful_op():
        return "success"
    
    result = handler.execute_with_fallback(
        successful_op,
        operation_name="test_success"
    )
    
    assert result == "success", f"Expected 'success', got {result}"
    assert handler.circuit_breaker_failures == 0, "Failures should be 0 after success"
    
    print("✓ Successful operation executed correctly")
    return True


def test_retry_logic():
    """Test retry logic with eventual success."""
    print("\n--- Testing Retry Logic ---")
    
    handler = MemoryFallbackHandler(max_retries=3, backoff_factor=1.5)
    
    call_count = 0
    
    def failing_then_success():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception(f"Attempt {call_count} failed")
        return "success"
    
    result = handler.execute_with_fallback(
        failing_then_success,
        operation_name="test_retry"
    )
    
    assert result == "success", f"Expected 'success', got {result}"
    assert call_count == 3, f"Expected 3 calls, got {call_count}"
    
    print(f"✓ Retry logic worked correctly ({call_count} attempts)")
    return True


def test_circuit_breaker():
    """Test circuit breaker functionality."""
    print("\n--- Testing Circuit Breaker ---")
    
    handler = MemoryFallbackHandler(
        max_retries=1,
        circuit_breaker_threshold=2
    )
    
    def always_fails():
        raise Exception("Always fails")
    
    # First failure
    result1 = handler.execute_with_fallback(
        always_fails,
        operation_name="test_circuit_1"
    )
    assert result1 is None, "Should return None on failure"
    assert handler.circuit_breaker_failures == 1, "Should have 1 failure"
    assert not handler.circuit_breaker_open, "Circuit should still be closed"
    
    # Second failure - should open circuit
    result2 = handler.execute_with_fallback(
        always_fails,
        operation_name="test_circuit_2"
    )
    assert result2 is None, "Should return None on failure"
    assert handler.circuit_breaker_failures == 2, "Should have 2 failures"
    assert handler.circuit_breaker_open, "Circuit should be open"
    
    print("✓ Circuit breaker opened after threshold")
    
    # Third attempt - should not execute due to open circuit
    call_count = 0
    
    def should_not_execute():
        nonlocal call_count
        call_count += 1
        return "executed"
    
    result3 = handler.execute_with_fallback(
        should_not_execute,
        operation_name="test_circuit_3"
    )
    assert result3 is None, "Should return None with open circuit"
    assert call_count == 0, "Should not execute with open circuit"
    
    print("✓ Circuit breaker prevented execution when open")
    return True


def test_manual_reset():
    """Test manual circuit breaker reset."""
    print("\n--- Testing Manual Reset ---")
    
    handler = MemoryFallbackHandler()
    handler.circuit_breaker_open = True
    handler.circuit_breaker_failures = 5
    handler.circuit_breaker_opened_at = datetime.utcnow()
    
    handler.reset_circuit_breaker()
    
    assert not handler.circuit_breaker_open, "Circuit should be closed"
    assert handler.circuit_breaker_failures == 0, "Failures should be reset"
    assert handler.circuit_breaker_opened_at is None, "Timestamp should be cleared"
    
    print("✓ Manual reset worked correctly")
    return True


def test_get_status():
    """Test status reporting."""
    print("\n--- Testing Status Reporting ---")
    
    handler = MemoryFallbackHandler(max_retries=5, backoff_factor=3.0)
    handler.circuit_breaker_failures = 2
    
    status = handler.get_status()
    
    assert "circuit_breaker_open" in status, "Status missing circuit_breaker_open"
    assert "circuit_breaker_failures" in status, "Status missing failures"
    assert "max_retries" in status, "Status missing max_retries"
    assert status["max_retries"] == 5, "max_retries incorrect in status"
    assert status["circuit_breaker_failures"] == 2, "failures incorrect in status"
    
    print("✓ Status reporting works correctly")
    return True


def test_global_handler():
    """Test global fallback handler singleton."""
    print("\n--- Testing Global Handler Singleton ---")
    
    handler1 = get_fallback_handler()
    handler2 = get_fallback_handler()
    
    assert handler1 is handler2, "Should return same instance"
    
    print("✓ Global handler is a singleton")
    return True


def test_store_pattern_safe():
    """Test store_pattern_safe with mock."""
    print("\n--- Testing store_pattern_safe ---")
    
    # Create a mock session manager
    class MockSessionManager:
        def __init__(self, should_fail=False):
            self.should_fail = should_fail
            self.stored_patterns = []
        
        def store(self, pattern, namespace):
            if self.should_fail:
                raise Exception("Storage failed")
            self.stored_patterns.append((pattern, namespace))
    
    # Test successful storage
    mock_manager = MockSessionManager(should_fail=False)
    pattern = {"field": "notional", "technique": "regex"}
    namespace = "/facts/{actorId}"
    
    result = store_pattern_safe(mock_manager, pattern, namespace)
    
    assert result is True, "Should return True on success"
    assert len(mock_manager.stored_patterns) == 1, "Should store pattern"
    
    print("✓ store_pattern_safe succeeded")
    
    # Test failed storage
    mock_manager_fail = MockSessionManager(should_fail=True)
    result_fail = store_pattern_safe(mock_manager_fail, pattern, namespace)
    
    assert result_fail is False, "Should return False on failure"
    
    print("✓ store_pattern_safe handled failure correctly")
    return True


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Memory Error Handling Validation")
    print("=" * 60)
    
    tests = [
        test_handler_initialization,
        test_successful_operation,
        test_retry_logic,
        test_circuit_breaker,
        test_manual_reset,
        test_get_status,
        test_global_handler,
        test_store_pattern_safe
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
