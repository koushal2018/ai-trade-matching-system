#!/usr/bin/env python3
"""
Local testing script for PDF Adapter Agent.
Bypasses the AgentCore CLI to test the agent directly.

Usage:
    python test_local.py <path_to_pdf>                    # Test with local file (uploads to S3 first)
    python test_local.py s3://bucket/key --s3-only         # Test with existing S3 file
"""

import sys
import os
import json
import boto3
from pathlib import Path
from pdf_adapter_agent_strands import invoke


def verify_environment():
    """Verify required environment variables and AWS credentials."""
    print("🔍 Verifying environment...")
    
    # Check environment variables
    required_vars = {
        "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
        "S3_BUCKET_NAME": os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production"),
        "BEDROCK_MODEL_ID": os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
    }
    
    for var, value in required_vars.items():
        status = "✅" if os.getenv(var) else "⚠️  (using default)"
        print(f"  {status} {var}: {value}")
    
    # Verify AWS credentials
    try:
        sts = boto3.client('sts', region_name=required_vars["AWS_REGION"])
        identity = sts.get_caller_identity()
        print(f"  ✅ AWS credentials valid (Account: {identity['Account']})")
        return required_vars
    except Exception as e:
        print(f"  ❌ AWS credentials invalid: {e}")
        print("\nPlease configure AWS credentials:")
        print("  export AWS_ACCESS_KEY_ID=your-key")
        print("  export AWS_SECRET_ACCESS_KEY=your-secret")
        sys.exit(1)


def upload_to_s3_if_local(pdf_path: str, source_type: str, config: dict) -> str:
    """
    Upload local PDF to S3 if needed, or return S3 path as-is.
    
    Args:
        pdf_path: Local file path or S3 URI
        source_type: BANK or COUNTERPARTY
        config: Environment configuration
        
    Returns:
        S3 URI (s3://bucket/key)
    """
    # If already an S3 path, return as-is
    if pdf_path.startswith("s3://"):
        return pdf_path
    
    # Upload local file to S3
    print(f"\n📤 Uploading local file to S3...")
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)
    
    s3_client = boto3.client('s3', region_name=config["AWS_REGION"])
    bucket = config["S3_BUCKET_NAME"]
    
    # Generate S3 key
    filename = os.path.basename(pdf_path)
    s3_key = f"{source_type}/{filename}"
    
    try:
        s3_client.upload_file(pdf_path, bucket, s3_key)
        s3_uri = f"s3://{bucket}/{s3_key}"
        print(f"  ✅ Uploaded to: {s3_uri}")
        return s3_uri
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        sys.exit(1)


def test_pdf_adapter():
    """Test the PDF adapter agent with a local or S3 PDF file."""
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python test_local.py <path_to_pdf> [--s3-only]")
        print("\nExamples:")
        print("  # Test with local file (uploads to S3 first)")
        print("  python test_local.py data/BANK/FAB_26933659.pdf")
        print()
        print("  # Test with existing S3 file")
        print("  python test_local.py s3://bucket/BANK/FAB_26933659.pdf --s3-only")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    s3_only = "--s3-only" in sys.argv
    
    # Verify environment
    config = verify_environment()
    
    # Determine source type from path
    if "/BANK/" in pdf_path or pdf_path.startswith("BANK/"):
        source_type = "BANK"
    elif "/COUNTERPARTY/" in pdf_path or pdf_path.startswith("COUNTERPARTY/"):
        source_type = "COUNTERPARTY"
    else:
        print("\n⚠️  Cannot determine source type from path.")
        print("Please ensure path contains '/BANK/' or '/COUNTERPARTY/'")
        source_type = input("Enter source type (BANK/COUNTERPARTY): ").upper()
        if source_type not in ["BANK", "COUNTERPARTY"]:
            print("❌ Invalid source type")
            sys.exit(1)
    
    # Extract document ID from filename
    if pdf_path.startswith("s3://"):
        document_id = Path(pdf_path.split("/")[-1]).stem
    else:
        document_id = Path(pdf_path).stem
    
    # Upload to S3 if local file
    if not s3_only:
        s3_path = upload_to_s3_if_local(pdf_path, source_type, config)
    else:
        s3_path = pdf_path
    
    # Create test payload
    payload = {
        "document_id": document_id,
        "document_path": s3_path,
        "source_type": source_type,
        "correlation_id": "test_local_001"
    }
    
    print("\n" + "=" * 80)
    print("Testing PDF Adapter Agent")
    print("=" * 80)
    print(f"Document ID: {document_id}")
    print(f"S3 Path: {s3_path}")
    print(f"Source Type: {source_type}")
    print(f"Model: {config['BEDROCK_MODEL_ID']}")
    print("=" * 80)
    
    # Invoke the agent
    print("\n🤖 Invoking agent...")
    result = invoke(payload, context=None)
    
    # Print results
    print("\n" + "=" * 80)
    print("RESULT")
    print("=" * 80)
    print(json.dumps(result, indent=2, default=str))
    print("=" * 80)
    
    if result.get("success"):
        print("\n✅ SUCCESS!")
        print(f"Processing time: {result.get('processing_time_ms', 0):.2f}ms")
        if "token_usage" in result:
            tokens = result["token_usage"]
            print(f"Token usage: {tokens.get('input_tokens', 0)} in / {tokens.get('output_tokens', 0)} out")
        
        # Show agent response summary
        if "agent_response" in result:
            response = result["agent_response"]
            if len(response) > 200:
                print(f"\nAgent response (truncated): {response[:200]}...")
            else:
                print(f"\nAgent response: {response}")
    else:
        print("\n❌ FAILED!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        if "error_type" in result:
            print(f"Error type: {result['error_type']}")
        sys.exit(1)


if __name__ == "__main__":
    test_pdf_adapter()
