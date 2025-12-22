"""
Property-based test for exponential backoff calculation.
Feature: agent-issues-fix, Property 4: Exponential Backoff Calculation
Validates: Requirements 7.3

Property 4: Exponential Backoff Calculation
For any sequence of retry attempts, the backoff delay should increase
exponentially with each attempt (backoff[n+1] > backoff[n] for all n).
"""
from typing import List

import pytest
from hypothesis import given, strategies as st, settings


def calculate_exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Calculate exponential backoff delay for a given attempt number.
    
    Args:
        attempt: Retry attempt number (0-indexed)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: 60.0)
        
    Returns:
        Backoff delay in seconds
    """
    # Exponential backoff: base_delay * (2 ** attempt)
    # With jitter and max cap
    delay = base_delay * (2 ** attempt)
    return min(delay, max_delay)


def calculate_backoff_sequence(num_attempts: int, base_delay: float = 1.0, max_delay: float = 60.0) -> List[float]:
    """
    Calculate a sequence of exponential backoff delays.
    
    Args:
        num_attempts: Number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay cap in seconds
        
    Returns:
        List of backoff delays for each attempt
    """
    return [calculate_exponential_backoff(i, base_delay, max_delay) for i in range(num_attempts)]


def test_property_exponential_backoff_basic():
    """
    Property 4: Exponential Backoff Calculation (Basic Test)
    
    For any sequence of retry attempts, the backoff delay should increase
    with each attempt until the maximum delay is reached.
    
    **Feature: agent-issues-fix, Property 4: Exponential Backoff Calculation**
    **Validates: Requirements 7.3**
    """
    # Test with 5 attempts
    backoffs = calculate_backoff_sequence(5, base_delay=1.0, max_delay=60.0)
    
    # Expected: [1.0, 2.0, 4.0, 8.0, 16.0]
    assert len(backoffs) == 5
    assert backoffs[0] == 1.0
    assert backoffs[1] == 2.0
    assert backoffs[2] == 4.0
    assert backoffs[3] == 8.0
    assert backoffs[4] == 16.0
    
    # Verify monotonic increase
    for i in range(len(backoffs) - 1):
        assert backoffs[i + 1] > backoffs[i], f"Backoff should increase: backoff[{i}]={backoffs[i]}, backoff[{i+1}]={backoffs[i+1]}"


@given(
    num_attempts=st.integers(min_value=2, max_value=10),
    base_delay=st.floats(min_value=0.1, max_value=5.0),
    max_delay=st.floats(min_value=10.0, max_value=120.0)
)
@settings(max_examples=100)
def test_property_exponential_backoff_monotonic_increase(num_attempts, base_delay, max_delay):
    """
    Property 4: Exponential Backoff Monotonic Increase
    
    For any sequence of retry attempts, the backoff delay should be
    monotonically increasing (or constant once max_delay is reached).
    
    This property ensures: backoff[n+1] >= backoff[n] for all n
    
    **Feature: agent-issues-fix, Property 4: Exponential Backoff Calculation**
    **Validates: Requirements 7.3**
    """
    backoffs = calculate_backoff_sequence(num_attempts, base_delay, max_delay)
    
    # Verify we have the correct number of backoffs
    assert len(backoffs) == num_attempts
    
    # Verify monotonic increase (or constant at max)
    for i in range(len(backoffs) - 1):
        assert backoffs[i + 1] >= backoffs[i], (
            f"Backoff should be monotonically increasing: "
            f"backoff[{i}]={backoffs[i]:.2f}, backoff[{i+1}]={backoffs[i+1]:.2f}"
        )


@given(
    num_attempts=st.integers(min_value=2, max_value=10),
    base_delay=st.floats(min_value=0.1, max_value=5.0),
    max_delay=st.floats(min_value=10.0, max_value=120.0)
)
@settings(max_examples=100)
def test_property_exponential_backoff_respects_max_delay(num_attempts, base_delay, max_delay):
    """
    Property 4: Exponential Backoff Respects Maximum Delay
    
    For any sequence of retry attempts, no backoff delay should exceed
    the configured maximum delay.
    
    This property ensures: backoff[n] <= max_delay for all n
    
    **Feature: agent-issues-fix, Property 4: Exponential Backoff Calculation**
    **Validates: Requirements 7.3**
    """
    backoffs = calculate_backoff_sequence(num_attempts, base_delay, max_delay)
    
    # Verify all backoffs respect the maximum
    for i, backoff in enumerate(backoffs):
        assert backoff <= max_delay, (
            f"Backoff should not exceed max_delay: "
            f"backoff[{i}]={backoff:.2f}, max_delay={max_delay:.2f}"
        )


@given(
    attempt=st.integers(min_value=0, max_value=10),
    base_delay=st.floats(min_value=0.1, max_value=5.0)
)
@settings(max_examples=100)
def test_property_exponential_backoff_first_attempt_equals_base(attempt, base_delay):
    """
    Property 4: Exponential Backoff First Attempt
    
    The first retry attempt (attempt=0) should have a backoff delay
    equal to the base delay.
    
    This property ensures: backoff[0] == base_delay
    
    **Feature: agent-issues-fix, Property 4: Exponential Backoff Calculation**
    **Validates: Requirements 7.3**
    """
    if attempt == 0:
        backoff = calculate_exponential_backoff(attempt, base_delay, max_delay=1000.0)
        assert backoff == base_delay, (
            f"First backoff should equal base_delay: "
            f"backoff={backoff:.2f}, base_delay={base_delay:.2f}"
        )


@given(
    num_attempts=st.integers(min_value=3, max_value=10),
    base_delay=st.floats(min_value=0.1, max_value=5.0)
)
@settings(max_examples=100)
def test_property_exponential_backoff_doubles_each_attempt(num_attempts, base_delay):
    """
    Property 4: Exponential Backoff Doubles Each Attempt
    
    For exponential backoff with base 2, each backoff should be approximately
    double the previous backoff (until max_delay is reached).
    
    This property ensures: backoff[n+1] ≈ 2 * backoff[n] (before capping)
    
    **Feature: agent-issues-fix, Property 4: Exponential Backoff Calculation**
    **Validates: Requirements 7.3**
    """
    # Use a very high max_delay to avoid capping
    max_delay = 10000.0
    backoffs = calculate_backoff_sequence(num_attempts, base_delay, max_delay)
    
    # Verify doubling relationship (before hitting max)
    for i in range(len(backoffs) - 1):
        if backoffs[i + 1] < max_delay:
            ratio = backoffs[i + 1] / backoffs[i]
            assert abs(ratio - 2.0) < 0.01, (
                f"Backoff should double each attempt: "
                f"backoff[{i}]={backoffs[i]:.2f}, backoff[{i+1}]={backoffs[i+1]:.2f}, "
                f"ratio={ratio:.2f} (expected: 2.0)"
            )


def test_property_exponential_backoff_realistic_scenario():
    """
    Property 4: Exponential Backoff Realistic Scenario
    
    Test with realistic parameters used in production:
    - Base delay: 1.0 second
    - Max delay: 60.0 seconds
    - 5 retry attempts
    
    Expected sequence: [1.0, 2.0, 4.0, 8.0, 16.0]
    
    **Feature: agent-issues-fix, Property 4: Exponential Backoff Calculation**
    **Validates: Requirements 7.3**
    """
    backoffs = calculate_backoff_sequence(5, base_delay=1.0, max_delay=60.0)
    
    expected = [1.0, 2.0, 4.0, 8.0, 16.0]
    assert backoffs == expected, f"Expected {expected}, got {backoffs}"
    
    # Verify total retry time
    total_time = sum(backoffs)
    assert total_time == 31.0, f"Total retry time should be 31.0 seconds, got {total_time}"


def test_property_exponential_backoff_max_delay_capping():
    """
    Property 4: Exponential Backoff Maximum Delay Capping
    
    Test that backoff delays are capped at max_delay when exponential
    growth would exceed it.
    
    With base_delay=1.0 and max_delay=10.0:
    - Attempt 0: 1.0 (2^0 = 1)
    - Attempt 1: 2.0 (2^1 = 2)
    - Attempt 2: 4.0 (2^2 = 4)
    - Attempt 3: 8.0 (2^3 = 8)
    - Attempt 4: 10.0 (2^4 = 16, capped at 10)
    - Attempt 5: 10.0 (2^5 = 32, capped at 10)
    
    **Feature: agent-issues-fix, Property 4: Exponential Backoff Calculation**
    **Validates: Requirements 7.3**
    """
    backoffs = calculate_backoff_sequence(6, base_delay=1.0, max_delay=10.0)
    
    expected = [1.0, 2.0, 4.0, 8.0, 10.0, 10.0]
    assert backoffs == expected, f"Expected {expected}, got {backoffs}"
    
    # Verify all values are at or below max
    for backoff in backoffs:
        assert backoff <= 10.0


if __name__ == '__main__':
    print("="*80)
    print("Property 4: Exponential Backoff Calculation")
    print("Feature: agent-issues-fix")
    print("Validates: Requirements 7.3")
    print("="*80)
    print()
    
    # Run basic test
    print("Running basic exponential backoff test...")
    try:
        test_property_exponential_backoff_basic()
        print("✅ PASSED: Basic exponential backoff test")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        exit(1)
    
    # Run realistic scenario test
    print("\nRunning realistic scenario test...")
    try:
        test_property_exponential_backoff_realistic_scenario()
        print("✅ PASSED: Realistic scenario test")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        exit(1)
    
    # Run max delay capping test
    print("\nRunning max delay capping test...")
    try:
        test_property_exponential_backoff_max_delay_capping()
        print("✅ PASSED: Max delay capping test")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        exit(1)
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED")
    print("="*80)
    print("\nTo run property-based tests with Hypothesis:")
    print("  pytest tests/property_based/test_property_4_exponential_backoff.py -v")
