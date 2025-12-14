#!/bin/bash
# Run all tests for swarm-to-agentcore migration
# This script runs property tests and unit tests to verify the implementation

set -e  # Exit on error

echo "=========================================="
echo "Swarm-to-AgentCore Migration Test Suite"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo ""
    echo "=========================================="
    echo "Running: $test_name"
    echo "=========================================="
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ]; then
            echo -e "${YELLOW}⚠️  SKIPPED: $test_name${NC}"
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
        else
            echo -e "${RED}❌ FAILED: $test_name${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        return 1
    fi
}

# Check if AGENTCORE_MEMORY_ID is set
if [ -z "$AGENTCORE_MEMORY_ID" ]; then
    echo -e "${YELLOW}⚠️  WARNING: AGENTCORE_MEMORY_ID not set${NC}"
    echo "Some tests will be skipped. To run all tests, set:"
    echo "  export AGENTCORE_MEMORY_ID=<your-memory-id>"
    echo ""
fi

# Property Test 1: Memory Storage Consistency
run_test "Property 1: Memory Storage Consistency" \
    "python test_property_1_memory_storage_consistency.py"

# Property Test 2: Memory Retrieval Relevance
run_test "Property 2: Memory Retrieval Relevance" \
    "python test_property_2_memory_retrieval_relevance.py"

# Property Test 3: Session ID Format Compliance
run_test "Property 3: Session ID Format Compliance" \
    "python test_property_3_session_id_format.py"

# Property Test 4: Functional Parity
run_test "Property 4: Functional Parity Preservation" \
    "python test_property_4_functional_parity.py"

# Property Test 5: Memory Configuration
run_test "Property 5: Memory Configuration Correctness" \
    "python test_property_5_memory_configuration.py"

# Property Test 6: AgentCore Runtime Scaling
run_test "Property 6: AgentCore Runtime Scaling" \
    "python test_property_6_agentcore_runtime_scaling.py"

# Unit Test: Session Manager
run_test "Unit Test: Session Manager" \
    "python test_session_manager_simple.py"

# Memory Error Handling Tests
run_test "Memory Error Handling Tests" \
    "python deployment/swarm/test_memory_error_handling.py"

# Validate Error Handling
run_test "Validate Error Handling Implementation" \
    "python deployment/swarm/validate_error_handling.py"

# Print summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Total Tests:   $TOTAL_TESTS"
echo -e "${GREEN}Passed:        $PASSED_TESTS${NC}"
echo -e "${RED}Failed:        $FAILED_TESTS${NC}"
echo -e "${YELLOW}Skipped:       $SKIPPED_TESTS${NC}"
echo "=========================================="

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED OR SKIPPED${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi
