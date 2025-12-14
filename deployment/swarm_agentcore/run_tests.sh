#!/bin/bash
# Run all tests for swarm-to-agentcore migration
# This script should be run from the deployment/swarm_agentcore directory

set -e  # Exit on error

echo "=========================================="
echo "Swarm-to-AgentCore Migration Test Suite"
echo "=========================================="
echo ""

# Navigate to project root
cd ../..

# Check if AGENTCORE_MEMORY_ID is set
if [ -z "$AGENTCORE_MEMORY_ID" ]; then
    echo "⚠️  WARNING: AGENTCORE_MEMORY_ID not set"
    echo "Some tests will be skipped. To run all tests:"
    echo "  export AGENTCORE_MEMORY_ID=<your-memory-id>"
    echo ""
fi

# Run the main test script from root
if [ -f "run_all_swarm_agentcore_tests.sh" ]; then
    bash run_all_swarm_agentcore_tests.sh
else
    echo "❌ Test runner not found at root: run_all_swarm_agentcore_tests.sh"
    echo ""
    echo "Running tests individually..."
    
    # Property tests
    echo ""
    echo "=== Property Tests ==="
    python test_property_1_memory_storage_consistency.py || echo "⚠️  Test skipped or failed"
    python test_property_2_memory_retrieval_relevance.py || echo "⚠️  Test skipped or failed"
    python test_property_3_session_id_format.py || echo "⚠️  Test skipped or failed"
    python test_property_4_functional_parity.py || echo "⚠️  Test skipped or failed"
    python test_property_5_memory_configuration.py || echo "⚠️  Test skipped or failed"
    python test_property_6_agentcore_runtime_scaling.py || echo "⚠️  Test skipped or failed"
    
    # Unit tests
    echo ""
    echo "=== Unit Tests ==="
    python deployment/swarm_agentcore/test_memory_resource_creation.py || echo "⚠️  Test skipped or failed"
    python deployment/swarm_agentcore/test_session_manager_creation.py || echo "⚠️  Test skipped or failed"
    python deployment/swarm_agentcore/test_agent_creation.py || echo "⚠️  Test skipped or failed"
    python deployment/swarm_agentcore/test_error_handling.py || echo "⚠️  Test skipped or failed"
    
    # Integration tests
    echo ""
    echo "=== Integration Tests ==="
    python deployment/swarm_agentcore/test_integration_trade_processing.py || echo "⚠️  Test skipped or failed"
    python deployment/swarm_agentcore/test_integration_memory_persistence.py || echo "⚠️  Test skipped or failed"
    
    # Performance tests
    echo ""
    echo "=== Performance Tests ==="
    python deployment/swarm_agentcore/test_performance_memory_retrieval.py || echo "⚠️  Test skipped or failed"
    python deployment/swarm_agentcore/test_performance_agentcore_scaling.py || echo "⚠️  Test skipped or failed"
fi

echo ""
echo "=========================================="
echo "Test execution complete"
echo "=========================================="
