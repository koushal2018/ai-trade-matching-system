#!/usr/bin/env python3
"""
Development testing script for Trade Extraction Agent.

This script tests the agent running in development mode via HTTP requests.
"""

import json
import requests
import time
import uuid
from typing import Dict, Any


def test_agent_dev_server(port: int = 8080, host: str = "localhost") -> None:
    """Test the agent development server."""
    base_url = f"http://{host}:{port}"
    
    print(f"🧪 Testing Trade Extraction Agent Development Server")
    print(f"URL: {base_url}")
    print("=" * 60)
    
    # Test health check
    print("1. Testing health check...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/health", timeout=10)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response time: {response_time_ms}ms")
            print(f"   Response: {response.text[:100]}...")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        print("Make sure the development server is running: ./dev.sh")
        return
    
    # Test agent invocation
    print("\n2. Testing agent invocation...")
    
    test_payload = {
        "document_id": "dev_test_001",
        "canonical_output_location": "s3://trade-matching-system-agentcore-production/extracted/BANK/dev_test_001.json",
        "source_type": "BANK",
        "correlation_id": f"dev_test_{uuid.uuid4().hex[:8]}"
    }
    
    print(f"Test payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/invoke",
            json=test_payload,
            timeout=60
        )
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        
        print(f"Response status: {response.status_code}")
        print(f"Processing time: {processing_time}ms")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Agent invocation successful")
            print(f"Response: {json.dumps(result, indent=2, default=str)}")
            
            # Validate response structure
            required_fields = ['success', 'correlation_id']
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                print(f"⚠️  Missing response fields: {missing_fields}")
            else:
                print("✅ Response structure valid")
                
        else:
            print(f"❌ Agent invocation failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Agent invocation failed: {e}")
    
    # Test table routing
    print("\n3. Testing table routing...")
    
    routing_tests = [
        {"source_type": "BANK", "expected_table": "BankTradeData"},
        {"source_type": "COUNTERPARTY", "expected_table": "CounterpartyTradeData"},
        {"source_type": "INVALID", "expected_success": False}
    ]
    
    for test_case in routing_tests:
        test_payload = {
            "document_id": f"routing_test_{test_case['source_type'].lower()}",
            "canonical_output_location": f"s3://test-bucket/extracted/{test_case['source_type']}/test.json",
            "source_type": test_case['source_type'],
            "correlation_id": f"routing_test_{uuid.uuid4().hex[:8]}"
        }
        
        try:
            response = requests.post(
                f"{base_url}/invoke",
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                
                if test_case.get('expected_success', True):
                    if success:
                        print(f"✅ {test_case['source_type']}: Routing successful")
                    else:
                        print(f"❌ {test_case['source_type']}: Expected success but got failure")
                else:
                    if not success:
                        print(f"✅ {test_case['source_type']}: Expected failure handled correctly")
                    else:
                        print(f"❌ {test_case['source_type']}: Expected failure but got success")
            else:
                print(f"❌ {test_case['source_type']}: HTTP error {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {test_case['source_type']}: Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Development testing completed!")
    print("\nUseful development commands:")
    print("  ./dev.sh                    # Start development server")
    print("  python test_dev.py          # Run this test script")
    print("  curl http://localhost:8080/health  # Quick health check")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Trade Extraction Agent development server")
    parser.add_argument("--port", type=int, default=8080, help="Development server port")
    parser.add_argument("--host", default="localhost", help="Development server host")
    
    args = parser.parse_args()
    
    test_agent_dev_server(args.port, args.host)


if __name__ == "__main__":
    main()