#!/usr/bin/env python3
"""
Local testing script for HTTP Agent Orchestrator.
Tests the orchestration logic without deploying to AgentCore Runtime.

Usage:
    python test_local_orchestrator.py <document_id> <source_type>
    
Example:
    python test_local_orchestrator.py FAB_26933659 BANK
"""

import sys
import os
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from http_agent_orchestrator import TradeMatchingHTTPOrchestrator


def verify_environment():
    """Verify required environment variables and AWS credentials."""
    print("🔍 Verifying environment...")
    
    required_vars = {
        "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
        "S3_BUCKET_NAME": os.getenv("S3_BUCKET_NAME", 
                                    "trade-matching-system-agentcore-production"),
        "PDF_ADAPTER_AGENT_ARN": os.getenv("PDF_ADAPTER_AGENT_ARN"),
        "TRADE_EXTRACTION_AGENT_ARN": os.getenv("TRADE_EXTRACTION_AGENT_ARN"),
        "TRADE_MATCHING_AGENT_ARN": os.getenv("TRADE_MATCHING_AGENT_ARN"),
        "EXCEPTION_MANAGEMENT_AGENT_ARN": os.getenv("EXCEPTION_MANAGEMENT_AGENT_ARN"),
    }
    
    missing = []
    for var, value in required_vars.items():
        if value:
            print(f"  ✅ {var}: ...{value[-40:] if len(value) > 40 else value}")
        else:
            print(f"  ❌ {var}: NOT SET")
            missing.append(var)
    
    if missing:
        print(f"\n❌ Missing required environment variables: {missing}")
        print("\nSet them in .env file or export them:")
        for var in missing:
            print(f"  export {var}=<value>")
        sys.exit(1)
    
    # Verify AWS credentials
    import boto3
    try:
        sts = boto3.client('sts', region_name=required_vars["AWS_REGION"])
        identity = sts.get_caller_identity()
        print(f"  ✅ AWS credentials valid (Account: {identity['Account']})")
        return required_vars
    except Exception as e:
        print(f"  ❌ AWS credentials invalid: {e}")
        sys.exit(1)


async def test_orchestrator():
    """Test the HTTP orchestrator with a document."""
    
    if len(sys.argv) < 3:
        print("Usage: python test_local_orchestrator.py <document_id> <source_type>")
        print("\nExamples:")
        print("  python test_local_orchestrator.py FAB_26933659 BANK")
        print("  python test_local_orchestrator.py GCS_12345678 COUNTERPARTY")
        sys.exit(1)
    
    document_id = sys.argv[1]
    source_type = sys.argv[2].upper()
    
    if source_type not in ["BANK", "COUNTERPARTY"]:
        print(f"❌ Invalid source type: {source_type}")
        print("Must be BANK or COUNTERPARTY")
        sys.exit(1)
    
    # Verify environment
    config = verify_environment()
    
    # Construct document path
    bucket = config["S3_BUCKET_NAME"]
    document_path = f"s3://{bucket}/{source_type}/{document_id}.pdf"
    
    print("\n" + "=" * 80)
    print("Testing HTTP Agent Orchestrator")
    print("=" * 80)
    print(f"Document ID: {document_id}")
    print(f"Document Path: {document_path}")
    print(f"Source Type: {source_type}")
    print(f"Region: {config['AWS_REGION']}")
    print("=" * 80)
    
    # Create orchestrator
    orchestrator = TradeMatchingHTTPOrchestrator()
    
    # Test orchestration
    print("\n🤖 Starting orchestration...")
    start_time = datetime.now(timezone.utc)
    
    try:
        result = await orchestrator.process_trade_confirmation(
            document_path=document_path,
            source_type=source_type,
            document_id=document_id,
            correlation_id=f"test_local_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )
        
        elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        # Print results
        print("\n" + "=" * 80)
        print("ORCHESTRATION RESULT")
        print("=" * 80)
        print(json.dumps(result, indent=2, default=str))
        print("=" * 80)
        
        if result.get("success"):
            print("\n✅ ORCHESTRATION SUCCESSFUL!")
            print(f"Total processing time: {elapsed_ms:.2f}ms")
            print(f"Match classification: {result.get('match_classification', 'N/A')}")
            print(f"Confidence score: {result.get('confidence_score', 0)}%")
            
            # Show workflow steps
            workflow_steps = result.get("workflow_steps", {})
            print(f"\nWorkflow steps executed: {len(workflow_steps)}")
            for step_name, step_result in workflow_steps.items():
                success = step_result.get("success", False)
                status = "✅" if success else "❌"
                print(f"  {status} {step_name}")
        else:
            print("\n❌ ORCHESTRATION FAILED!")
            print(f"Failed at step: {result.get('failed_step', 'unknown')}")
            print(f"Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        print("\n" + "=" * 80)
        print("ORCHESTRATION ERROR")
        print("=" * 80)
        print(f"Exception: {type(e).__name__}")
        print(f"Message: {e}")
        print(f"Elapsed time: {elapsed_ms:.2f}ms")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
