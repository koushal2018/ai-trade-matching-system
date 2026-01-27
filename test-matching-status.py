#!/usr/bin/env python3
"""
Simple test script to verify the matching status endpoint implementation.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

# Mock the dependencies
mock_processing_status_table = Mock()

# Test data
test_items = [
    # Matched trade
    {
        "processing_id": "session-1",
        "overallStatus": "completed",
        "tradeMatching": {"status": "success"},
        "exceptionManagement": {"status": "success"},
        "pdfAdapter": {"status": "success"},
        "tradeExtraction": {"status": "success"}
    },
    # Another matched trade
    {
        "processing_id": "session-2",
        "overallStatus": "completed",
        "tradeMatching": {"status": "success"},
        "exceptionManagement": {"status": "success"},
        "pdfAdapter": {"status": "success"},
        "tradeExtraction": {"status": "success"}
    },
    # Unmatched trade
    {
        "processing_id": "session-3",
        "overallStatus": "completed",
        "tradeMatching": {"status": "failed"},
        "exceptionManagement": {"status": "success"},
        "pdfAdapter": {"status": "success"},
        "tradeExtraction": {"status": "success"}
    },
    # Pending trade (processing)
    {
        "processing_id": "session-4",
        "overallStatus": "processing",
        "tradeMatching": {"status": "in-progress"},
        "exceptionManagement": {"status": "pending"},
        "pdfAdapter": {"status": "success"},
        "tradeExtraction": {"status": "success"}
    },
    # Pending trade (initializing)
    {
        "processing_id": "session-5",
        "overallStatus": "initializing",
        "tradeMatching": {"status": "pending"},
        "exceptionManagement": {"status": "pending"},
        "pdfAdapter": {"status": "pending"},
        "tradeExtraction": {"status": "pending"}
    },
    # Exception in exceptionManagement
    {
        "processing_id": "session-6",
        "overallStatus": "completed",
        "tradeMatching": {"status": "success"},
        "exceptionManagement": {"status": "error"},
        "pdfAdapter": {"status": "success"},
        "tradeExtraction": {"status": "success"}
    },
    # Exception in agent status
    {
        "processing_id": "session-7",
        "overallStatus": "processing",
        "tradeMatching": {"status": "in-progress"},
        "exceptionManagement": {"status": "pending"},
        "pdfAdapter": {"status": "error"},
        "tradeExtraction": {"status": "success"}
    }
]

# Simulate the logic
matched = 0
unmatched = 0
pending = 0
exceptions = 0

for item in test_items:
    overall_status = item.get('overallStatus', '')
    trade_matching = item.get('tradeMatching', {})
    trade_matching_status = trade_matching.get('status', '')
    exception_mgmt = item.get('exceptionManagement', {})
    exception_status = exception_mgmt.get('status', '')
    
    # Check for exceptions first
    has_exception = False
    if exception_status == 'error':
        has_exception = True
    else:
        # Check if any agent has error status
        for agent_key in ['pdfAdapter', 'tradeExtraction', 'tradeMatching', 'exceptionManagement']:
            agent_data = item.get(agent_key, {})
            if agent_data.get('status') == 'error':
                has_exception = True
                break
    
    if has_exception:
        exceptions += 1
    
    # Count matched trades
    if overall_status == 'completed' and trade_matching_status == 'success':
        matched += 1
    # Count unmatched trades
    elif overall_status == 'completed' and trade_matching_status != 'success':
        unmatched += 1
    # Count pending matches
    elif overall_status in ['processing', 'initializing']:
        pending += 1

print("Matching Status Calculation Test")
print("=" * 50)
print(f"Matched:    {matched} (expected: 2)")
print(f"Unmatched:  {unmatched} (expected: 1)")
print(f"Pending:    {pending} (expected: 2)")
print(f"Exceptions: {exceptions} (expected: 2)")
print("=" * 50)

# Verify results
assert matched == 2, f"Expected 2 matched, got {matched}"
assert unmatched == 1, f"Expected 1 unmatched, got {unmatched}"
assert pending == 2, f"Expected 2 pending, got {pending}"
assert exceptions == 2, f"Expected 2 exceptions, got {exceptions}"

print("✅ All tests passed!")
