"""
Performance Test: AgentCore Runtime Scaling

This test verifies that AgentCore Runtime automatically scales agent instances
to handle increasing load without significant response time degradation,
as specified in Requirement 1.2.

**Validates: Requirements 1.2**

NOTE: This test requires an actual AgentCore Runtime deployment to test scaling behavior.
For local testing, it simulates load patterns and validates the swarm's ability to
handle concurrent requests efficiently.
"""

import os
import time
import json
import pytest
import logging
import statistics
from typing import Dict, List, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

# Import the swarm processing function
from trade_matching_swarm import (
    process_trade_confirmation,
    create_trade_matching_swarm_with_memory
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_MEMORY_ID = os.environ.get("AGENTCORE_MEMORY_ID")
TEST_S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
TEST_REGION = "us-east-1"

# Performance thresholds
MAX_RESPONSE_TIME_DEGRADATION_FACTOR = 2.0  # Response time shouldn't more than double under load
BASELINE_CONCURRENT_REQUESTS = 5
SCALED_CONCURRENT_REQUESTS = 20


def simulate_trade_processing(
    document_id: str,
    source_type: str = "BANK"
) -> Dict[str, Any]:
    """
    Simulate processing a trade confirmation.
    
    Args:
        document_id: Unique document identifier
        source_type: BANK or COUNTERPARTY
        
    Returns:
        Processing result with timing information
    """
    start_time = time.time()
    
    try:
        # For testing, we'll create a swarm and measure its initialization time
        # In production, this would invoke the AgentCore Runtime endpoint
        swarm = create_trade_matching_swarm_with_memory(
            document_id=document_id,
            memory_id=TEST_MEMORY_ID
        )
        
        end_time = time.time()
        processing_time_ms = (end_time - start_time) * 1000
        
        return {
            "success": True,
            "document_id": document_id,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        end_time = time.time()
        processing_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Processing failed for {document_id}: {e}")
        
        return {
            "success": False,
            "document_id": document_id,
            "processing_time_ms": processing_time_ms,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def run_concurrent_load_test(
    num_requests: int,
    max_workers: int = None
) -> Dict[str, Any]:
    """
    Run a concurrent load test with the specified number of requests.
    
    Args:
        num_requests: Number of concurrent requests to simulate
        max_workers: Maximum number of worker threads (defaults to num_requests)
        
    Returns:
        Dictionary with timing statistics
    """
    if max_workers is None:
        max_workers = num_requests
    
    logger.info(f"Starting load test with {num_requests} concurrent requests")
    
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all requests
        futures = []
        for i in range(num_requests):
            document_id = f"load_test_{uuid.uuid4().hex[:8]}"
            source_type = "BANK" if i % 2 == 0 else "COUNTERPARTY"
            
            future = executor.submit(
                simulate_trade_processing,
                document_id=document_id,
                source_type=source_type
            )
            futures.append(future)
        
        # Collect results as they complete
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Request failed: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "processing_time_ms": 0
                })
    
    end_time = time.time()
    total_time_ms = (end_time - start_time) * 1000
    
    # Calculate statistics
    successful_results = [r for r in results if r.get("success")]
    processing_times = [r["processing_time_ms"] for r in successful_results]
    
    if not processing_times:
        return {
            "num_requests": num_requests,
            "total_time_ms": total_time_ms,
            "success_count": 0,
            "failure_count": len(results),
            "error": "All requests failed"
        }
    
    stats = {
        "num_requests": num_requests,
        "total_time_ms": total_time_ms,
        "success_count": len(successful_results),
        "failure_count": len(results) - len(successful_results),
        "avg_processing_time_ms": statistics.mean(processing_times),
        "median_processing_time_ms": statistics.median(processing_times),
        "min_processing_time_ms": min(processing_times),
        "max_processing_time_ms": max(processing_times),
        "stdev_processing_time_ms": statistics.stdev(processing_times) if len(processing_times) > 1 else 0,
        "throughput_requests_per_sec": len(successful_results) / (total_time_ms / 1000)
    }
    
    logger.info(
        f"Load test completed:\n"
        f"  Requests: {stats['num_requests']}\n"
        f"  Success: {stats['success_count']}\n"
        f"  Failures: {stats['failure_count']}\n"
        f"  Avg processing time: {stats['avg_processing_time_ms']:.2f}ms\n"
        f"  Median processing time: {stats['median_processing_time_ms']:.2f}ms\n"
        f"  Max processing time: {stats['max_processing_time_ms']:.2f}ms\n"
        f"  Throughput: {stats['throughput_requests_per_sec']:.2f} req/s"
    )
    
    return stats


class TestAgentCoreRuntimeScaling:
    """Performance tests for AgentCore Runtime scaling behavior."""
    
    def test_baseline_performance(self):
        """
        Establish baseline performance with low concurrent load.
        
        This test measures the baseline response time with a small number
        of concurrent requests to establish a performance baseline.
        
        **Validates: Requirements 1.2**
        """
        stats = run_concurrent_load_test(num_requests=BASELINE_CONCURRENT_REQUESTS)
        
        assert stats["success_count"] > 0, "No successful requests in baseline test"
        assert stats["failure_count"] == 0, f"Baseline test had {stats['failure_count']} failures"
        
        logger.info(
            f"Baseline performance established: "
            f"{stats['avg_processing_time_ms']:.2f}ms average processing time"
        )
    
    def test_scaled_performance(self):
        """
        Test performance under increased load.
        
        This test measures response time with a higher number of concurrent
        requests to verify that the system can handle increased load.
        
        **Validates: Requirements 1.2**
        """
        stats = run_concurrent_load_test(num_requests=SCALED_CONCURRENT_REQUESTS)
        
        assert stats["success_count"] > 0, "No successful requests in scaled test"
        
        # Allow some failures under high load, but most should succeed
        success_rate = stats["success_count"] / stats["num_requests"]
        assert success_rate >= 0.8, (
            f"Success rate {success_rate:.1%} is too low under scaled load"
        )
        
        logger.info(
            f"Scaled performance: "
            f"{stats['avg_processing_time_ms']:.2f}ms average processing time "
            f"with {stats['num_requests']} concurrent requests"
        )
    
    def test_response_time_degradation_under_load(self):
        """
        Test that response time doesn't degrade significantly under increased load.
        
        This is the core scaling test: verify that as load increases, AgentCore
        Runtime scales to maintain acceptable response times.
        
        **Validates: Requirements 1.2**
        """
        # Run baseline test
        logger.info("Running baseline load test...")
        baseline_stats = run_concurrent_load_test(num_requests=BASELINE_CONCURRENT_REQUESTS)
        
        assert baseline_stats["success_count"] > 0, "Baseline test failed"
        baseline_avg_time = baseline_stats["avg_processing_time_ms"]
        
        # Run scaled test
        logger.info("Running scaled load test...")
        scaled_stats = run_concurrent_load_test(num_requests=SCALED_CONCURRENT_REQUESTS)
        
        assert scaled_stats["success_count"] > 0, "Scaled test failed"
        scaled_avg_time = scaled_stats["avg_processing_time_ms"]
        
        # Calculate degradation factor
        degradation_factor = scaled_avg_time / baseline_avg_time
        
        logger.info(
            f"Response time comparison:\n"
            f"  Baseline ({BASELINE_CONCURRENT_REQUESTS} concurrent): {baseline_avg_time:.2f}ms\n"
            f"  Scaled ({SCALED_CONCURRENT_REQUESTS} concurrent): {scaled_avg_time:.2f}ms\n"
            f"  Degradation factor: {degradation_factor:.2f}x\n"
            f"  Threshold: {MAX_RESPONSE_TIME_DEGRADATION_FACTOR:.2f}x"
        )
        
        # Verify response time doesn't degrade too much
        assert degradation_factor <= MAX_RESPONSE_TIME_DEGRADATION_FACTOR, (
            f"Response time degraded by {degradation_factor:.2f}x under load, "
            f"exceeds maximum allowed degradation of {MAX_RESPONSE_TIME_DEGRADATION_FACTOR:.2f}x"
        )
    
    def test_incremental_load_scaling(self):
        """
        Test response time across incrementally increasing load levels.
        
        This test verifies that the system scales gracefully as load increases
        incrementally, not just at two discrete load levels.
        
        **Validates: Requirements 1.2**
        """
        load_levels = [5, 10, 15, 20]
        results = []
        
        for num_requests in load_levels:
            logger.info(f"Testing with {num_requests} concurrent requests...")
            stats = run_concurrent_load_test(num_requests=num_requests)
            
            if stats["success_count"] > 0:
                results.append({
                    "load": num_requests,
                    "avg_time_ms": stats["avg_processing_time_ms"],
                    "max_time_ms": stats["max_processing_time_ms"],
                    "throughput": stats["throughput_requests_per_sec"],
                    "success_rate": stats["success_count"] / stats["num_requests"]
                })
        
        assert len(results) > 0, "No successful load tests"
        
        # Log scaling behavior
        logger.info("\nScaling behavior across load levels:")
        logger.info(f"{'Load':<10} {'Avg Time':<15} {'Max Time':<15} {'Throughput':<15} {'Success Rate':<15}")
        logger.info("-" * 70)
        for r in results:
            logger.info(
                f"{r['load']:<10} "
                f"{r['avg_time_ms']:<15.2f} "
                f"{r['max_time_ms']:<15.2f} "
                f"{r['throughput']:<15.2f} "
                f"{r['success_rate']:<15.1%}"
            )
        
        # Verify that average response time doesn't increase dramatically
        baseline_time = results[0]["avg_time_ms"]
        max_time = max(r["avg_time_ms"] for r in results)
        degradation = max_time / baseline_time
        
        assert degradation <= MAX_RESPONSE_TIME_DEGRADATION_FACTOR, (
            f"Maximum response time degradation {degradation:.2f}x "
            f"exceeds threshold of {MAX_RESPONSE_TIME_DEGRADATION_FACTOR:.2f}x"
        )
        
        # Verify throughput increases with load (system is scaling)
        throughputs = [r["throughput"] for r in results]
        assert throughputs[-1] > throughputs[0], (
            "Throughput did not increase with load - system may not be scaling"
        )
    
    def test_sustained_load_performance(self):
        """
        Test performance under sustained load over multiple iterations.
        
        This test verifies that the system maintains consistent performance
        over time, not just for a single burst of requests.
        
        **Validates: Requirements 1.2**
        """
        num_iterations = 3
        num_requests_per_iteration = 10
        iteration_results = []
        
        for i in range(num_iterations):
            logger.info(f"Running sustained load iteration {i+1}/{num_iterations}...")
            stats = run_concurrent_load_test(num_requests=num_requests_per_iteration)
            
            if stats["success_count"] > 0:
                iteration_results.append(stats["avg_processing_time_ms"])
            
            # Brief pause between iterations
            time.sleep(1)
        
        assert len(iteration_results) == num_iterations, (
            f"Only {len(iteration_results)}/{num_iterations} iterations succeeded"
        )
        
        # Calculate consistency metrics
        avg_time = statistics.mean(iteration_results)
        stdev_time = statistics.stdev(iteration_results)
        coefficient_of_variation = stdev_time / avg_time
        
        logger.info(
            f"Sustained load performance over {num_iterations} iterations:\n"
            f"  Average time: {avg_time:.2f}ms\n"
            f"  Std deviation: {stdev_time:.2f}ms\n"
            f"  Coefficient of variation: {coefficient_of_variation:.2%}"
        )
        
        # Verify consistent performance (CV < 30% indicates good consistency)
        assert coefficient_of_variation < 0.3, (
            f"Performance inconsistency too high: CV={coefficient_of_variation:.2%}"
        )
        
        # Verify no significant degradation over time
        first_iteration_time = iteration_results[0]
        last_iteration_time = iteration_results[-1]
        time_change = last_iteration_time / first_iteration_time
        
        assert time_change < 1.5, (
            f"Performance degraded {time_change:.2f}x over sustained load"
        )


class TestAgentCoreRuntimeScalingIntegration:
    """
    Integration tests for AgentCore Runtime scaling with actual endpoint.
    
    NOTE: These tests require an actual AgentCore Runtime deployment.
    They will be skipped if AGENTCORE_ENDPOINT environment variable is not set.
    """
    
    @pytest.mark.skipif(
        not os.environ.get("AGENTCORE_ENDPOINT"),
        reason="AGENTCORE_ENDPOINT not set - requires deployed AgentCore Runtime"
    )
    def test_agentcore_endpoint_scaling(self):
        """
        Test actual AgentCore Runtime endpoint scaling behavior.
        
        This test invokes the actual AgentCore Runtime endpoint to verify
        real-world scaling behavior.
        
        **Validates: Requirements 1.2**
        """
        import requests
        
        endpoint = os.environ.get("AGENTCORE_ENDPOINT")
        
        def invoke_agentcore_endpoint(document_id: str) -> Dict[str, Any]:
            """Invoke the AgentCore Runtime endpoint."""
            start_time = time.time()
            
            try:
                response = requests.post(
                    endpoint,
                    json={
                        "document_path": f"test/{document_id}.pdf",
                        "source_type": "BANK",
                        "document_id": document_id
                    },
                    timeout=60
                )
                
                end_time = time.time()
                processing_time_ms = (end_time - start_time) * 1000
                
                return {
                    "success": response.status_code == 200,
                    "processing_time_ms": processing_time_ms,
                    "status_code": response.status_code
                }
                
            except Exception as e:
                end_time = time.time()
                processing_time_ms = (end_time - start_time) * 1000
                
                return {
                    "success": False,
                    "processing_time_ms": processing_time_ms,
                    "error": str(e)
                }
        
        # Test with increasing load
        load_levels = [5, 10, 20]
        results = []
        
        for num_requests in load_levels:
            logger.info(f"Testing AgentCore endpoint with {num_requests} concurrent requests...")
            
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=num_requests) as executor:
                futures = [
                    executor.submit(invoke_agentcore_endpoint, f"endpoint_test_{uuid.uuid4().hex[:8]}")
                    for _ in range(num_requests)
                ]
                
                request_results = [f.result() for f in as_completed(futures)]
            
            end_time = time.time()
            
            successful = [r for r in request_results if r.get("success")]
            if successful:
                avg_time = statistics.mean([r["processing_time_ms"] for r in successful])
                results.append({
                    "load": num_requests,
                    "avg_time_ms": avg_time,
                    "success_count": len(successful)
                })
        
        assert len(results) > 0, "No successful AgentCore endpoint tests"
        
        # Verify scaling behavior
        baseline_time = results[0]["avg_time_ms"]
        max_time = max(r["avg_time_ms"] for r in results)
        degradation = max_time / baseline_time
        
        logger.info(
            f"AgentCore endpoint scaling test:\n"
            f"  Baseline time: {baseline_time:.2f}ms\n"
            f"  Max time under load: {max_time:.2f}ms\n"
            f"  Degradation factor: {degradation:.2f}x"
        )
        
        assert degradation <= MAX_RESPONSE_TIME_DEGRADATION_FACTOR, (
            f"AgentCore endpoint response time degraded by {degradation:.2f}x, "
            f"exceeds threshold of {MAX_RESPONSE_TIME_DEGRADATION_FACTOR:.2f}x"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
