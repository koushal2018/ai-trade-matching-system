"""
Performance Test: Memory Retrieval Latency

This test verifies that memory retrieval operations complete within the required
500ms latency threshold as specified in Requirement 2.5.

**Validates: Requirements 2.5**
"""

import os
import time
import pytest
import logging
from typing import Dict, List
from datetime import datetime

# AgentCore Memory imports
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_MEMORY_ID = os.environ.get("AGENTCORE_MEMORY_ID")
TEST_ACTOR_ID = "test_performance_actor"
TEST_REGION = "us-east-1"

# Performance thresholds
MAX_RETRIEVAL_LATENCY_MS = 500  # Requirement 2.5


def create_test_session_manager(session_id: str) -> AgentCoreMemorySessionManager:
    """Create a test session manager with standard retrieval configs."""
    if not TEST_MEMORY_ID:
        pytest.skip("AGENTCORE_MEMORY_ID environment variable not set")
    
    config = AgentCoreMemoryConfig(
        memory_id=TEST_MEMORY_ID,
        session_id=session_id,
        actor_id=TEST_ACTOR_ID,
        retrieval_config={
            "/facts/{actorId}": RetrievalConfig(
                top_k=10,
                relevance_score=0.6
            ),
            "/preferences/{actorId}": RetrievalConfig(
                top_k=5,
                relevance_score=0.7
            ),
            "/summaries/{actorId}/{sessionId}": RetrievalConfig(
                top_k=5,
                relevance_score=0.5
            )
        }
    )
    
    return AgentCoreMemorySessionManager(
        agentcore_memory_config=config,
        region_name=TEST_REGION
    )


def measure_retrieval_latency(
    session_manager: AgentCoreMemorySessionManager,
    query: str,
    namespace: str
) -> float:
    """
    Measure the latency of a single memory retrieval operation.
    
    Args:
        session_manager: Session manager instance
        query: Query string
        namespace: Memory namespace to query
        
    Returns:
        Latency in milliseconds
    """
    start_time = time.time()
    
    try:
        # Perform retrieval
        results = session_manager.retrieve(
            query=query,
            namespace=namespace
        )
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        logger.info(
            f"Retrieval completed in {latency_ms:.2f}ms "
            f"(query: '{query[:50]}...', namespace: {namespace}, "
            f"results: {len(results) if results else 0})"
        )
        
        return latency_ms
        
    except Exception as e:
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        logger.error(f"Retrieval failed after {latency_ms:.2f}ms: {e}")
        raise


class TestMemoryRetrievalPerformance:
    """Performance tests for memory retrieval operations."""
    
    def test_facts_namespace_retrieval_latency(self):
        """
        Test that retrieval from /facts namespace completes within 500ms.
        
        **Validates: Requirements 2.5**
        """
        session_manager = create_test_session_manager(
            session_id=f"perf_test_facts_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Test query for trade patterns
        query = "trade matching decision for currency swap with notional mismatch"
        namespace = "/facts/{actorId}"
        
        latency_ms = measure_retrieval_latency(session_manager, query, namespace)
        
        assert latency_ms < MAX_RETRIEVAL_LATENCY_MS, (
            f"Facts retrieval took {latency_ms:.2f}ms, "
            f"exceeds limit of {MAX_RETRIEVAL_LATENCY_MS}ms"
        )
    
    def test_preferences_namespace_retrieval_latency(self):
        """
        Test that retrieval from /preferences namespace completes within 500ms.
        
        **Validates: Requirements 2.5**
        """
        session_manager = create_test_session_manager(
            session_id=f"perf_test_prefs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Test query for processing preferences
        query = "extraction threshold for notional field in bank confirmations"
        namespace = "/preferences/{actorId}"
        
        latency_ms = measure_retrieval_latency(session_manager, query, namespace)
        
        assert latency_ms < MAX_RETRIEVAL_LATENCY_MS, (
            f"Preferences retrieval took {latency_ms:.2f}ms, "
            f"exceeds limit of {MAX_RETRIEVAL_LATENCY_MS}ms"
        )
    
    def test_summaries_namespace_retrieval_latency(self):
        """
        Test that retrieval from /summaries namespace completes within 500ms.
        
        **Validates: Requirements 2.5**
        """
        session_manager = create_test_session_manager(
            session_id=f"perf_test_summ_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Test query for session summaries
        query = "trade processing summary for document with extraction errors"
        namespace = "/summaries/{actorId}/{sessionId}"
        
        latency_ms = measure_retrieval_latency(session_manager, query, namespace)
        
        assert latency_ms < MAX_RETRIEVAL_LATENCY_MS, (
            f"Summaries retrieval took {latency_ms:.2f}ms, "
            f"exceeds limit of {MAX_RETRIEVAL_LATENCY_MS}ms"
        )
    
    def test_multiple_sequential_retrievals_latency(self):
        """
        Test that multiple sequential retrievals each complete within 500ms.
        
        This simulates an agent querying multiple namespaces during processing.
        
        **Validates: Requirements 2.5**
        """
        session_manager = create_test_session_manager(
            session_id=f"perf_test_multi_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        test_cases = [
            ("trade extraction pattern for counterparty confirmations", "/facts/{actorId}"),
            ("OCR quality preferences for PDF processing", "/preferences/{actorId}"),
            ("recent trade processing outcomes", "/summaries/{actorId}/{sessionId}")
        ]
        
        latencies = []
        for query, namespace in test_cases:
            latency_ms = measure_retrieval_latency(session_manager, query, namespace)
            latencies.append(latency_ms)
            
            assert latency_ms < MAX_RETRIEVAL_LATENCY_MS, (
                f"Retrieval from {namespace} took {latency_ms:.2f}ms, "
                f"exceeds limit of {MAX_RETRIEVAL_LATENCY_MS}ms"
            )
        
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        logger.info(
            f"Sequential retrievals - "
            f"Average: {avg_latency:.2f}ms, "
            f"Max: {max_latency:.2f}ms, "
            f"All under {MAX_RETRIEVAL_LATENCY_MS}ms threshold"
        )
    
    def test_retrieval_latency_with_complex_query(self):
        """
        Test retrieval latency with a complex, detailed query.
        
        Complex queries should still complete within the 500ms threshold.
        
        **Validates: Requirements 2.5**
        """
        session_manager = create_test_session_manager(
            session_id=f"perf_test_complex_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Complex query with multiple concepts
        query = """
        Trade matching decision for interest rate swap with the following characteristics:
        - Notional amount mismatch of approximately 2%
        - Currency is USD
        - Maturity date within 2 days tolerance
        - Counterparty name fuzzy match required
        - Previous classification was PROBABLE_MATCH
        - HITL review was requested
        """
        namespace = "/facts/{actorId}"
        
        latency_ms = measure_retrieval_latency(session_manager, query, namespace)
        
        assert latency_ms < MAX_RETRIEVAL_LATENCY_MS, (
            f"Complex query retrieval took {latency_ms:.2f}ms, "
            f"exceeds limit of {MAX_RETRIEVAL_LATENCY_MS}ms"
        )
    
    def test_retrieval_latency_percentiles(self):
        """
        Test retrieval latency across multiple samples to measure percentiles.
        
        Ensures consistent performance, not just occasional fast retrievals.
        
        **Validates: Requirements 2.5**
        """
        session_manager = create_test_session_manager(
            session_id=f"perf_test_percentile_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Run 20 retrievals to get statistical distribution
        num_samples = 20
        latencies = []
        
        queries = [
            "trade matching pattern",
            "extraction technique for notional field",
            "severity classification for date mismatch",
            "OCR quality improvement strategy",
            "counterparty name fuzzy matching threshold"
        ]
        
        namespace = "/facts/{actorId}"
        
        for i in range(num_samples):
            query = queries[i % len(queries)] + f" sample {i}"
            latency_ms = measure_retrieval_latency(session_manager, query, namespace)
            latencies.append(latency_ms)
        
        # Calculate percentiles
        latencies_sorted = sorted(latencies)
        p50 = latencies_sorted[len(latencies_sorted) // 2]
        p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]
        p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)]
        avg = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        logger.info(
            f"Latency percentiles over {num_samples} samples:\n"
            f"  Average: {avg:.2f}ms\n"
            f"  P50 (median): {p50:.2f}ms\n"
            f"  P95: {p95:.2f}ms\n"
            f"  P99: {p99:.2f}ms\n"
            f"  Max: {max_latency:.2f}ms"
        )
        
        # All retrievals should be under threshold
        assert max_latency < MAX_RETRIEVAL_LATENCY_MS, (
            f"Maximum latency {max_latency:.2f}ms exceeds limit of {MAX_RETRIEVAL_LATENCY_MS}ms"
        )
        
        # P95 should be well under threshold (with some margin)
        assert p95 < MAX_RETRIEVAL_LATENCY_MS * 0.9, (
            f"P95 latency {p95:.2f}ms is too close to limit of {MAX_RETRIEVAL_LATENCY_MS}ms"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
