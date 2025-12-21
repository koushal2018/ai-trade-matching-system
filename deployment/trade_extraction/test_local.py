#!/usr/bin/env python3
"""
Local testing script for Trade Extraction Agent.

This script allows testing the agent logic locally without deploying to AgentCore,
following AWS best practices for local development and testing.
"""

import os
import sys
import json
import uuid
import time
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up environment for local testing
os.environ["BYPASS_TOOL_CONSENT"] = "true"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["S3_BUCKET_NAME"] = "trade-matching-system-agentcore-production"
os.environ["DYNAMODB_BANK_TABLE"] = "BankTradeData"
os.environ["DYNAMODB_COUNTERPARTY_TABLE"] = "CounterpartyTradeData"
os.environ["DEPLOYMENT_STAGE"] = "development"

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agent import invoke, create_extraction_agent
    from table_router import TableRouter
    from trade_data_validator import TradeDataValidator
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)


def test_table_routing():
    """Test table routing logic locally."""
    print("🧪 Testing table routing...")
    
    router = TableRouter()
    
    # Test valid source types
    valid_tests = ['BANK', 'COUNTERPARTY', 'bank', 'counterparty']
    print(f"Testing {len(valid_tests)} valid source types...")
    
    for source_type in valid_tests:
        success, table_name, error = router.get_target_table(source_type)
        status = '✅' if success else '❌'
        print(f"  {source_type}: {status} -> {table_name}")
        
        if not success:
            print(f"    ERROR: {error}")
            logger.error(f"TEST_ROUTING_FAILED - Valid source type failed", extra={
                'source_type': source_type,
                'expected_success': True,
                'actual_success': success,
                'error': error
            })
    
    # Test invalid source types
    invalid_tests = ['INVALID', '', None]
    print(f"Testing {len(invalid_tests)} invalid source types...")
    
    for invalid_type in invalid_tests:
        success, table_name, error = router.get_target_table(invalid_type)
        status = '✅' if not success else '❌'
        print(f"  {invalid_type}: {status} -> {error}")
        
        if success:
            print(f"    UNEXPECTED SUCCESS: Should have failed")
            logger.warning(f"TEST_ROUTING_UNEXPECTED - Invalid source type succeeded", extra={
                'source_type': invalid_type,
                'expected_success': False,
                'actual_success': success,
                'table_name': table_name
            })
        else:
            logger.debug(f"TEST_ROUTING_EXPECTED - Invalid source type correctly failed", extra={
                'source_type': invalid_type,
                'error': error
            })


def test_agent_invoke():
    """Test agent invocation locally with mock data."""
    print("\n🧪 Testing agent invocation...")
    
    test_payload = {
        "document_id": "local_test_001",
        "canonical_output_location": "s3://test-bucket/extracted/BANK/local_test_001.json",
        "source_type": "BANK",
        "correlation_id": f"local_test_{uuid.uuid4().hex[:8]}"
    }
    
    print(f"Test payload: {json.dumps(test_payload, indent=2)}")
    logger.info("TEST_AGENT_INVOKE_START - Starting agent invocation test", extra={
        'test_type': 'agent_invocation',
        'payload': test_payload,
        'test_environment': 'local'
    })
    
    start_time = time.time()
    
    try:
        result = invoke(test_payload)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        print(f"Result: {json.dumps(result, indent=2, default=str)}")
        
        if result.get('success'):
            print("✅ Agent invocation successful")
            logger.info("TEST_AGENT_INVOKE_SUCCESS - Agent invocation test passed", extra={
                'test_type': 'agent_invocation',
                'processing_time_ms': processing_time_ms,
                'correlation_id': result.get('correlation_id'),
                'token_usage': result.get('token_usage', {}),
                'result_keys': list(result.keys())
            })
        else:
            print(f"❌ Agent invocation failed: {result.get('error')}")
            logger.error("TEST_AGENT_INVOKE_FAILED - Agent invocation test failed", extra={
                'test_type': 'agent_invocation',
                'processing_time_ms': processing_time_ms,
                'error': result.get('error'),
                'error_type': result.get('error_type'),
                'correlation_id': result.get('correlation_id')
            })
            
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        print(f"❌ Agent invocation error: {e}")
        logger.error("TEST_AGENT_INVOKE_ERROR - Agent invocation test threw exception", extra={
            'test_type': 'agent_invocation',
            'processing_time_ms': processing_time_ms,
            'error_type': type(e).__name__,
            'error_message': str(e),
            'payload': test_payload
        }, exc_info=True)


def test_data_validation():
    """Test data validation logic locally."""
    print("\n🧪 Testing data validation...")
    
    try:
        validator = TradeDataValidator()
        
        # Test valid trade data (using lowercase trade_id and internal_reference to match DynamoDB schema)
        valid_data = {
            "trade_id": "TEST_001",
            "internal_reference": "REF_001",
            "TRADE_SOURCE": "BANK",
            "notional": "1000000",
            "currency": "USD",
            "counterparty": "Test Bank"
        }
        
        is_valid, errors = validator.validate_and_normalize(valid_data)
        print(f"Valid data test: {'✅' if is_valid else '❌'}")
        if errors:
            print(f"  Errors: {errors}")
            
    except ImportError:
        print("⚠️  TradeDataValidator not available for local testing")


def main():
    """Run local tests."""
    print("🚀 Trade Extraction Agent - Local Testing")
    print("=" * 50)
    
    # Check AWS credentials
    try:
        import boto3
        boto3.client('sts').get_caller_identity()
        print("✅ AWS credentials configured")
    except Exception as e:
        print(f"⚠️  AWS credentials not configured: {e}")
        print("Some tests may fail without AWS access")
    
    # Run tests
    test_table_routing()
    test_data_validation()
    
    # Only test agent invoke if in development mode
    if os.getenv("DEPLOYMENT_STAGE") == "development":
        test_agent_invoke()
    else:
        print("\n⚠️  Skipping agent invocation test (not in development mode)")
    
    print("\n✅ Local testing completed")


if __name__ == "__main__":
    main()