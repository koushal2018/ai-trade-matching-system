#!/usr/bin/env python3
"""
Integration Test for Trade Data Extraction Agent

This script tests the Trade Data Extraction Agent with sample data.
It verifies that the LLM extraction tool and trade source classifier work correctly.
"""

import json
import os
from datetime import datetime

# Set up environment
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")

from src.latest_trade_matching_agent.tools.llm_extraction_tool import LLMExtractionTool
from src.latest_trade_matching_agent.tools.trade_source_classifier import TradeSourceClassifier
from src.latest_trade_matching_agent.models.trade import CanonicalTradeModel


def test_llm_extraction_tool():
    """Test LLM extraction tool with sample text."""
    print("\n" + "="*80)
    print("TEST 1: LLM Extraction Tool")
    print("="*80)
    
    sample_text = """
    Trade Confirmation
    
    Trade ID: GCS382857
    Trade Date: 2024-10-15
    Effective Date: 2024-10-17
    Maturity Date: 2025-10-17
    
    Notional: 1,000,000 USD
    Currency: USD
    Counterparty: Goldman Sachs
    Product Type: SWAP
    Commodity Type: CRUDE_OIL
    Settlement Type: CASH
    Payment Frequency: MONTHLY
    Fixed Rate: 3.5%
    Floating Rate Index: BRENT
    
    Broker: XYZ Brokers
    Trader: John Smith
    Trader Email: john.smith@example.com
    """
    
    print("\nSample Text:")
    print("-" * 80)
    print(sample_text)
    print("-" * 80)
    
    try:
        tool = LLMExtractionTool(region_name="us-east-1")
        
        print("\nExtracting trade fields...")
        result = tool.extract_trade_fields(
            extracted_text=sample_text,
            source_type="COUNTERPARTY",
            document_id="test_doc_001"
        )
        
        print("\nExtraction Result:")
        print(json.dumps(result, indent=2, default=str))
        
        if result["success"]:
            print("\n✅ LLM Extraction Tool: PASSED")
            print(f"   - Trade ID: {result['trade_data']['Trade_ID']}")
            print(f"   - Confidence: {result['extraction_confidence']}")
            print(f"   - Fields Extracted: {len([k for k, v in result['trade_data'].items() if v is not None])}")
            return True
        else:
            print("\n❌ LLM Extraction Tool: FAILED")
            print(f"   - Error: {result.get('error')}")
            return False
    
    except Exception as e:
        print(f"\n❌ LLM Extraction Tool: EXCEPTION")
        print(f"   - Error: {e}")
        return False


def test_trade_source_classifier():
    """Test trade source classifier with sample text."""
    print("\n" + "="*80)
    print("TEST 2: Trade Source Classifier")
    print("="*80)
    
    # Test COUNTERPARTY classification
    counterparty_text = """
    Trade Confirmation from Goldman Sachs
    
    Their Reference: GCS382857
    Client Confirmation
    Received from: Goldman Sachs Trading Desk
    """
    
    print("\nSample Text (COUNTERPARTY):")
    print("-" * 80)
    print(counterparty_text)
    print("-" * 80)
    
    try:
        classifier = TradeSourceClassifier(region_name="us-east-1")
        
        print("\nClassifying trade source...")
        result = classifier.classify_trade_source(
            extracted_text=counterparty_text,
            document_path="s3://bucket/COUNTERPARTY/trade.pdf"
        )
        
        print("\nClassification Result:")
        print(json.dumps(result, indent=2, default=str))
        
        if result["success"] and result["source_type"] == "COUNTERPARTY":
            print("\n✅ Trade Source Classifier (COUNTERPARTY): PASSED")
            print(f"   - Source Type: {result['source_type']}")
            print(f"   - Confidence: {result['confidence']}")
            print(f"   - Method: {result['method']}")
            counterparty_passed = True
        else:
            print("\n❌ Trade Source Classifier (COUNTERPARTY): FAILED")
            print(f"   - Expected: COUNTERPARTY, Got: {result.get('source_type')}")
            counterparty_passed = False
    
    except Exception as e:
        print(f"\n❌ Trade Source Classifier (COUNTERPARTY): EXCEPTION")
        print(f"   - Error: {e}")
        counterparty_passed = False
    
    # Test BANK classification
    bank_text = """
    Trade Confirmation from First Abu Dhabi Bank
    
    Our Reference: FAB26933659
    Our Trade ID: FAB26933659
    Internal Trade Confirmation
    We confirm the following trade...
    """
    
    print("\n" + "-"*80)
    print("Sample Text (BANK):")
    print("-" * 80)
    print(bank_text)
    print("-" * 80)
    
    try:
        print("\nClassifying trade source...")
        result = classifier.classify_trade_source(
            extracted_text=bank_text,
            document_path="s3://bucket/BANK/trade.pdf"
        )
        
        print("\nClassification Result:")
        print(json.dumps(result, indent=2, default=str))
        
        if result["success"] and result["source_type"] == "BANK":
            print("\n✅ Trade Source Classifier (BANK): PASSED")
            print(f"   - Source Type: {result['source_type']}")
            print(f"   - Confidence: {result['confidence']}")
            print(f"   - Method: {result['method']}")
            bank_passed = True
        else:
            print("\n❌ Trade Source Classifier (BANK): FAILED")
            print(f"   - Expected: BANK, Got: {result.get('source_type')}")
            bank_passed = False
    
    except Exception as e:
        print(f"\n❌ Trade Source Classifier (BANK): EXCEPTION")
        print(f"   - Error: {e}")
        bank_passed = False
    
    return counterparty_passed and bank_passed


def test_canonical_trade_model():
    """Test canonical trade model validation."""
    print("\n" + "="*80)
    print("TEST 3: Canonical Trade Model Validation")
    print("="*80)
    
    # Test valid trade data
    valid_trade_data = {
        "Trade_ID": "GCS382857",
        "TRADE_SOURCE": "COUNTERPARTY",
        "trade_date": "2024-10-15",
        "notional": 1000000.0,
        "currency": "USD",
        "counterparty": "Goldman Sachs",
        "product_type": "SWAP",
        "effective_date": "2024-10-17",
        "maturity_date": "2025-10-17",
        "commodity_type": "CRUDE_OIL",
        "settlement_type": "CASH"
    }
    
    print("\nValid Trade Data:")
    print(json.dumps(valid_trade_data, indent=2))
    
    try:
        trade = CanonicalTradeModel(**valid_trade_data)
        print("\n✅ Canonical Trade Model (Valid): PASSED")
        print(f"   - Trade ID: {trade.Trade_ID}")
        print(f"   - Source: {trade.TRADE_SOURCE}")
        print(f"   - Notional: {trade.notional} {trade.currency}")
        valid_passed = True
    except Exception as e:
        print(f"\n❌ Canonical Trade Model (Valid): FAILED")
        print(f"   - Error: {e}")
        valid_passed = False
    
    # Test invalid trade data (missing mandatory field)
    invalid_trade_data = {
        "Trade_ID": "GCS382857",
        "TRADE_SOURCE": "COUNTERPARTY",
        # Missing trade_date (mandatory)
        "notional": 1000000.0,
        "currency": "USD",
        "counterparty": "Goldman Sachs",
        "product_type": "SWAP"
    }
    
    print("\n" + "-"*80)
    print("Invalid Trade Data (missing trade_date):")
    print(json.dumps(invalid_trade_data, indent=2))
    
    try:
        trade = CanonicalTradeModel(**invalid_trade_data)
        print("\n❌ Canonical Trade Model (Invalid): FAILED")
        print("   - Should have raised validation error")
        invalid_passed = False
    except Exception as e:
        print(f"\n✅ Canonical Trade Model (Invalid): PASSED")
        print(f"   - Correctly rejected invalid data: {type(e).__name__}")
        invalid_passed = True
    
    # Test DynamoDB format conversion
    print("\n" + "-"*80)
    print("Testing DynamoDB format conversion...")
    
    try:
        trade = CanonicalTradeModel(**valid_trade_data)
        dynamodb_format = trade.to_dynamodb_format()
        
        print("\nDynamoDB Format (sample):")
        sample_fields = {k: v for k, v in list(dynamodb_format.items())[:5]}
        print(json.dumps(sample_fields, indent=2))
        
        # Verify format
        assert "Trade_ID" in dynamodb_format
        assert dynamodb_format["Trade_ID"]["S"] == "GCS382857"
        assert dynamodb_format["notional"]["N"] == "1000000.0"
        
        print("\n✅ DynamoDB Format Conversion: PASSED")
        dynamodb_passed = True
    except Exception as e:
        print(f"\n❌ DynamoDB Format Conversion: FAILED")
        print(f"   - Error: {e}")
        dynamodb_passed = False
    
    return valid_passed and invalid_passed and dynamodb_passed


def main():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("TRADE DATA EXTRACTION AGENT - INTEGRATION TESTS")
    print("="*80)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print(f"Region: us-east-1")
    
    results = []
    
    # Test 1: LLM Extraction Tool
    try:
        result = test_llm_extraction_tool()
        results.append(("LLM Extraction Tool", result))
    except Exception as e:
        print(f"\n❌ LLM Extraction Tool: EXCEPTION - {e}")
        results.append(("LLM Extraction Tool", False))
    
    # Test 2: Trade Source Classifier
    try:
        result = test_trade_source_classifier()
        results.append(("Trade Source Classifier", result))
    except Exception as e:
        print(f"\n❌ Trade Source Classifier: EXCEPTION - {e}")
        results.append(("Trade Source Classifier", False))
    
    # Test 3: Canonical Trade Model
    try:
        result = test_canonical_trade_model()
        results.append(("Canonical Trade Model", result))
    except Exception as e:
        print(f"\n❌ Canonical Trade Model: EXCEPTION - {e}")
        results.append(("Canonical Trade Model", False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    
    print("-" * 80)
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    print("="*80)
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
