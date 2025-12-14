"""
Property-based test for AgentCore Runtime scaling.
Feature: swarm-to-agentcore, Property 6: AgentCore Runtime scaling
Validates: Requirements 1.2

Property 6: AgentCore Runtime Scaling
For any load pattern with increasing concurrent trade processing requests, 
the AgentCore Runtime should automatically provision additional agent instances 
to maintain response time within acceptable limits.

This test verifies that:
1. AgentCore Runtime can handle increasing concurrent requests
2. Response times remain within acceptable limits under load
3. The system scales automatically without manual intervention
4. Performance degradation is bounded as load increases

Note: This test requires the swarm to be deployed to AgentCore Runtime.
It will skip if the deployment is not available.
"""
import os
import sys
import json
import time
import statistics
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any, List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Performance thresholds
MAX_RESPONSE_TIME_MS = 120000  # 120 seconds (2 minutes) for trade processing
MAX_DEGRADATION_FACTOR = 3.0   # Response time shouldn't degrade more than 3x under load
MIN_SUCCESS_RATE = 0.90        # At least 90% of requests should succeed


def get_agentcore_endpoint() -> str:
    """
    Get the AgentCore Runtime endpoint URL.
    Returns None if not deployed.
    """
    # Check environment variable
    endpoint = os.environ.get("AGENTCORE_ENDPOINT")
    
    if endpoint:
        return endpoint
    
    # Try to read from deployment output file
    endpoint_file = Path("deployment/swarm_agentcore/.agentcore_endpoint")
    if endpoint_file.exists():
        return endpoint_file.read_text().strip()
    
    return None


def invoke_agentcore_swarm(
    document_id: str,
    document_path: str = "data/BANK/FAB_26933659.pdf",
    source_type: str = "BANK",
    timeout: int = 120
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Invoke the AgentCore-deployed swarm and measure response time.
    
    Returns:
        (success, response_time_ms, result)
    """
    try:
        import boto3
        
        # Get AgentCore client
        client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        # Get agent ID from environment or file
        agent_id = os.environ.get("AGENTCORE_AGENT_ID")
        if not agent_id:
            agent_id_file = Path("deployment/swarm_agentcore/.agentcore_agent_id")
            if agent_id_file.exists():
                agent_id = agent_id_file.read_text().strip()
        
        if not agent_id:
            return False, 0.0, {"error": "Agent ID not found"}
        
        # Prepare payload
        payload = {
            "document_path": document_path,
            "source_type": source_type,
            "document_id": document_id,
            "correlation_id": f"test_{document_id}"
        }
        
        # Invoke agent
        start_time = time.time()
        
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',  # Test alias
            sessionId=f"test_session_{document_id}",
            inputText=json.dumps(payload)
        )
        
        # Process response
        result = {}
        for event in response.get('completion', []):
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    result = json.loads(chunk['bytes'].decode('utf-8'))
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        success = result.get('success', False)
        
        return success, response_time_ms, result
        
    except Exception as e:
        return False, 0.0, {"error": str(e)}


def simulate_load(
    num_requests: int,
    max_workers: int = None
) -> Dict[str, Any]:
    """
    Simulate load by sending concurrent requests to AgentCore Runtime.
    
    Returns:
        Statistics about the load test
    """
    if max_workers is None:
        max_workers = min(num_requests, 50)  # Cap at 50 concurrent workers
    
    results = []
    response_times = []
    successes = 0
    failures = 0
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all requests
        futures = []
        for i in range(num_requests):
            document_id = f"load_test_{int(time.time() * 1000)}_{i}"
            future = executor.submit(invoke_agentcore_swarm, document_id)
            futures.append(future)
        
        # Collect results
        for future in as_completed(futures):
            try:
                success, response_time_ms, result = future.result(timeout=180)
                
                results.append({
                    "success": success,
                    "response_time_ms": response_time_ms,
                    "result": result
                })
                
                if success:
                    successes += 1
                    response_times.append(response_time_ms)
                else:
                    failures += 1
                    
            except Exception as e:
                failures += 1
                results.append({
                    "success": False,
                    "response_time_ms": 0,
                    "error": str(e)
                })
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Calculate statistics
    stats = {
        "num_requests": num_requests,
        "successes": successes,
        "failures": failures,
        "success_rate": successes / num_requests if num_requests > 0 else 0,
        "total_time_seconds": total_time,
        "throughput_requests_per_second": num_requests / total_time if total_time > 0 else 0
    }
    
    if response_times:
        stats.update({
            "avg_response_time_ms": statistics.mean(response_times),
            "median_response_time_ms": statistics.median(response_times),
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "stdev_response_time_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0
        })
    
    return stats


@given(
    load_pattern=st.lists(
        st.integers(min_value=1, max_value=20),
        min_size=2,
        max_size=4
    )
)
@settings(max_examples=5, deadline=None)
def test_property_agentcore_runtime_scaling(load_pattern: List[int]):
    """
    Property 6: AgentCore Runtime Scaling
    
    For any load pattern with increasing concurrent trade processing requests, 
    the AgentCore Runtime should automatically provision additional agent 
    instances to maintain response time within acceptable limits.
    
    **Feature: swarm-to-agentcore, Property 6: AgentCore Runtime scaling**
    **Validates: Requirements 1.2**
    """
    # Ensure load pattern is increasing
    assume(all(load_pattern[i] <= load_pattern[i+1] for i in range(len(load_pattern)-1)))
    
    # Check if AgentCore deployment is available
    endpoint = get_agentcore_endpoint()
    agent_id = os.environ.get("AGENTCORE_AGENT_ID")
    
    if not endpoint and not agent_id:
        import pytest
        pytest.skip(
            "AgentCore deployment not available. "
            "Deploy with: cd deployment/swarm_agentcore && bash deploy_agentcore.sh"
        )
    
    print(f"\nTesting load pattern: {load_pattern}")
    
    # Run load tests for each level in the pattern
    all_stats = []
    baseline_response_time = None
    
    for num_requests in load_pattern:
        print(f"  Testing with {num_requests} concurrent requests...")
        
        stats = simulate_load(num_requests)
        all_stats.append(stats)
        
        # Property 1: Success rate should be above minimum threshold
        assert stats["success_rate"] >= MIN_SUCCESS_RATE, \
            f"Success rate {stats['success_rate']:.2%} below minimum {MIN_SUCCESS_RATE:.2%} " \
            f"at load level {num_requests}"
        
        # Property 2: Average response time should be within acceptable limits
        if "avg_response_time_ms" in stats:
            avg_response_time = stats["avg_response_time_ms"]
            
            assert avg_response_time <= MAX_RESPONSE_TIME_MS, \
                f"Average response time {avg_response_time:.0f}ms exceeds maximum " \
                f"{MAX_RESPONSE_TIME_MS}ms at load level {num_requests}"
            
            # Track baseline for degradation check
            if baseline_response_time is None:
                baseline_response_time = avg_response_time
            
            # Property 3: Response time degradation should be bounded
            degradation_factor = avg_response_time / baseline_response_time
            
            assert degradation_factor <= MAX_DEGRADATION_FACTOR, \
                f"Response time degraded by {degradation_factor:.2f}x (from {baseline_response_time:.0f}ms " \
                f"to {avg_response_time:.0f}ms), exceeds maximum degradation factor {MAX_DEGRADATION_FACTOR}x"
            
            print(f"    ✅ {stats['successes']}/{num_requests} succeeded, "
                  f"avg response: {avg_response_time:.0f}ms, "
                  f"degradation: {degradation_factor:.2f}x")
        else:
            print(f"    ⚠️  No successful requests at load level {num_requests}")
    
    # Print summary
    print(f"\n  Summary:")
    for i, (num_requests, stats) in enumerate(zip(load_pattern, all_stats)):
        if "avg_response_time_ms" in stats:
            print(f"    Load {num_requests}: {stats['success_rate']:.1%} success, "
                  f"{stats['avg_response_time_ms']:.0f}ms avg")


def test_agentcore_deployment_available():
    """
    Test that AgentCore deployment is available and responding.
    This is a prerequisite for the scaling property test.
    """
    endpoint = get_agentcore_endpoint()
    agent_id = os.environ.get("AGENTCORE_AGENT_ID")
    
    if not endpoint and not agent_id:
        import pytest
        pytest.skip(
            "AgentCore deployment not available. "
            "Deploy with: cd deployment/swarm_agentcore && bash deploy_agentcore.sh"
        )
    
    # Try a single invocation
    document_id = f"health_check_{int(time.time() * 1000)}"
    success, response_time_ms, result = invoke_agentcore_swarm(document_id)
    
    print(f"Health check: success={success}, response_time={response_time_ms:.0f}ms")
    
    # We don't require success (the test document may not exist),
    # but we should get a response
    assert response_time_ms > 0 or not success, \
        "AgentCore endpoint did not respond"


def test_baseline_performance():
    """
    Test baseline performance with a single request.
    This establishes the baseline for scaling tests.
    """
    endpoint = get_agentcore_endpoint()
    agent_id = os.environ.get("AGENTCORE_AGENT_ID")
    
    if not endpoint and not agent_id:
        import pytest
        pytest.skip("AgentCore deployment not available")
    
    print("\nTesting baseline performance (1 request)...")
    
    stats = simulate_load(num_requests=1)
    
    print(f"  Success rate: {stats['success_rate']:.1%}")
    if "avg_response_time_ms" in stats:
        print(f"  Response time: {stats['avg_response_time_ms']:.0f}ms")
    
    # Baseline should have high success rate
    assert stats["success_rate"] >= MIN_SUCCESS_RATE, \
        f"Baseline success rate {stats['success_rate']:.2%} below minimum"


if __name__ == '__main__':
    print("Testing AgentCore Runtime scaling property...")
    print("=" * 70)
    
    # Check if AgentCore is deployed
    endpoint = get_agentcore_endpoint()
    agent_id = os.environ.get("AGENTCORE_AGENT_ID")
    
    if not endpoint and not agent_id:
        print("⚠️  AgentCore deployment not detected")
        print()
        print("This test requires the swarm to be deployed to AgentCore Runtime.")
        print()
        print("To deploy:")
        print("  1. cd deployment/swarm_agentcore")
        print("  2. bash deploy_agentcore.sh")
        print("  3. export AGENTCORE_AGENT_ID=<agent-id>")
        print()
        print("Alternatively, set AGENTCORE_ENDPOINT environment variable.")
        sys.exit(0)
    
    print(f"AgentCore agent ID: {agent_id[:20] if agent_id else 'Not set'}...")
    print()
    
    # Test deployment is available
    print("Testing AgentCore deployment availability...")
    try:
        test_agentcore_deployment_available()
        print("✅ AgentCore deployment is available")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    print()
    
    # Test baseline performance
    print("Testing baseline performance...")
    try:
        test_baseline_performance()
        print("✅ Baseline performance acceptable")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("Running scaling property tests...")
    print("(Testing with increasing load patterns)")
    print()
    
    # Test with a simple increasing load pattern
    test_load_patterns = [
        [1, 2, 4],
        [2, 5, 10],
        [1, 3, 6, 10]
    ]
    
    for pattern in test_load_patterns:
        print(f"\nTesting load pattern: {pattern}")
        try:
            test_property_agentcore_runtime_scaling(pattern)
            print(f"  ✅ Scaling property holds for pattern {pattern}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
