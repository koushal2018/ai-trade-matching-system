#!/usr/bin/env python3
"""
End-to-End Test for AgentCore Trade Matching System

This script runs a full E2E test:
1. Upload PDF to S3
2. Invoke pdf_adapter_agent to convert PDF to images
3. Invoke trade_extraction_agent to extract trade data
4. Invoke trade_matching_agent to match trades

Usage:
    python scripts/e2e_agentcore_test.py --bank data/BANK/FAB_26933659.pdf
    python scripts/e2e_agentcore_test.py --counterparty data/COUNTERPARTY/GCS381315_V1.pdf
    python scripts/e2e_agentcore_test.py --both  # Process both and match
"""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Configuration
REGION = "us-east-1"
S3_BUCKET = "trade-matching-system-agentcore-production"

# Agent IDs from .bedrock_agentcore.yaml files
AGENTS = {
    "pdf_adapter": "pdf_adapter_agent-Az72YP53FJ",
    "trade_extraction": "trade_extraction_agent-KnAx4O4ezw", 
    "trade_matching": "trade_matching_agent-3aAvK64dQz"
}


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")


def print_step(step: int, description: str):
    """Print a step indicator."""
    print(f"\n[Step {step}] {description}")
    print("-" * 50)


def upload_to_s3(local_path: str, source_type: str) -> str:
    """Upload a file to S3 and return the S3 URI."""
    s3_client = boto3.client('s3', region_name=REGION)
    
    filename = Path(local_path).name
    s3_key = f"{source_type}/{filename}"
    
    print(f"  Uploading {local_path} to s3://{S3_BUCKET}/{s3_key}")
    
    s3_client.upload_file(local_path, S3_BUCKET, s3_key)
    
    s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
    print(f"  ✓ Uploaded to {s3_uri}")
    
    return s3_uri


def invoke_agent(agent_name: str, payload: dict) -> dict:
    """Invoke an AgentCore agent and return the response."""
    agent_id = AGENTS.get(agent_name)
    if not agent_id:
        raise ValueError(f"Unknown agent: {agent_name}")
    
    client = boto3.client('bedrock-agentcore-runtime', region_name=REGION)
    
    print(f"  Invoking {agent_name} (ID: {agent_id})")
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    
    start_time = time.time()
    
    response = client.invoke_agent_runtime(
        agentRuntimeId=agent_id,
        payload=json.dumps(payload)
    )
    
    elapsed = time.time() - start_time
    
    result = json.loads(response['body'].read().decode('utf-8'))
    
    print(f"  Response ({elapsed:.2f}s):")
    print(f"  {json.dumps(result, indent=2)}")
    
    return result


def process_pdf(local_path: str, source_type: str, correlation_id: str) -> dict:
    """
    Process a PDF through the full pipeline.
    
    Returns:
        dict with trade_id and extraction result
    """
    results = {
        "source_type": source_type,
        "local_path": local_path,
        "correlation_id": correlation_id
    }
    
    # Step 1: Upload to S3
    print_step(1, f"Upload {source_type} PDF to S3")
    s3_uri = upload_to_s3(local_path, source_type)
    results["s3_uri"] = s3_uri
    
    # Step 2: Invoke PDF Adapter
    print_step(2, "Invoke PDF Adapter Agent")
    
    # Extract document_id from filename
    filename = Path(local_path).stem
    document_id = filename.replace("FAB_", "").replace("_V1", "")
    
    pdf_payload = {
        "document_id": document_id,
        "s3_uri": s3_uri,
        "source_type": source_type,
        "correlation_id": correlation_id
    }
    
    pdf_result = invoke_agent("pdf_adapter", pdf_payload)
    results["pdf_adapter"] = pdf_result
    
    if not pdf_result.get("success"):
        print(f"  ❌ PDF Adapter failed: {pdf_result.get('error')}")
        return results
    
    print(f"  ✓ PDF converted to images")
    
    # Step 3: Invoke Trade Extraction
    print_step(3, "Invoke Trade Extraction Agent")
    
    # Get the canonical output location from PDF adapter
    canonical_output = pdf_result.get("canonical_output_location")
    if not canonical_output:
        # Construct it based on convention
        canonical_output = f"s3://{S3_BUCKET}/extracted/{source_type}/{document_id}.json"
    
    extraction_payload = {
        "document_id": document_id,
        "canonical_output_location": canonical_output,
        "source_type": source_type,
        "correlation_id": correlation_id
    }
    
    # If PDF adapter returned image paths, include them
    if pdf_result.get("image_paths"):
        extraction_payload["image_paths"] = pdf_result["image_paths"]
    
    extraction_result = invoke_agent("trade_extraction", extraction_payload)
    results["trade_extraction"] = extraction_result
    
    if not extraction_result.get("success"):
        print(f"  ❌ Trade Extraction failed: {extraction_result.get('error')}")
        return results
    
    trade_id = extraction_result.get("trade_id")
    results["trade_id"] = trade_id
    
    print(f"  ✓ Trade extracted: {trade_id}")
    print(f"    Source: {extraction_result.get('source_type')}")
    print(f"    Table: {extraction_result.get('table_name')}")
    print(f"    Confidence: {extraction_result.get('extraction_confidence')}")
    
    return results


def run_matching(trade_id: str, correlation_id: str) -> dict:
    """Run trade matching for a given trade ID."""
    print_step(4, "Invoke Trade Matching Agent")
    
    matching_payload = {
        "trade_id": trade_id,
        "correlation_id": correlation_id
    }
    
    matching_result = invoke_agent("trade_matching", matching_payload)
    
    if matching_result.get("success"):
        status = matching_result.get("status", matching_result.get("decision_status"))
        
        if status == "WAITING":
            print(f"  ⏳ Waiting for counterparty trade")
            print(f"    Message: {matching_result.get('message')}")
        else:
            print(f"  ✓ Matching completed")
            print(f"    Classification: {matching_result.get('classification')}")
            print(f"    Match Score: {matching_result.get('match_score')}")
            print(f"    Decision: {matching_result.get('decision_status')}")
            if matching_result.get("report_path"):
                print(f"    Report: {matching_result.get('report_path')}")
    else:
        print(f"  ❌ Matching failed: {matching_result.get('error')}")
    
    return matching_result


def run_e2e_test(bank_pdf: str = None, counterparty_pdf: str = None):
    """Run the full E2E test."""
    correlation_id = f"e2e_test_{uuid.uuid4().hex[:8]}"
    
    print_header("AgentCore E2E Test")
    print(f"Correlation ID: {correlation_id}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print(f"Region: {REGION}")
    print(f"S3 Bucket: {S3_BUCKET}")
    
    results = {
        "correlation_id": correlation_id,
        "timestamp": datetime.utcnow().isoformat(),
        "bank": None,
        "counterparty": None,
        "matching": None
    }
    
    trade_ids = []
    
    # Process Bank PDF
    if bank_pdf:
        print_header("Processing BANK Trade")
        bank_result = process_pdf(bank_pdf, "BANK", correlation_id)
        results["bank"] = bank_result
        if bank_result.get("trade_id"):
            trade_ids.append(("BANK", bank_result["trade_id"]))
    
    # Process Counterparty PDF
    if counterparty_pdf:
        print_header("Processing COUNTERPARTY Trade")
        cp_result = process_pdf(counterparty_pdf, "COUNTERPARTY", correlation_id)
        results["counterparty"] = cp_result
        if cp_result.get("trade_id"):
            trade_ids.append(("COUNTERPARTY", cp_result["trade_id"]))
    
    # Run Matching
    if trade_ids:
        print_header("Trade Matching")
        
        # Try matching with each extracted trade ID
        for source, trade_id in trade_ids:
            print(f"\nMatching trade from {source}: {trade_id}")
            matching_result = run_matching(trade_id, correlation_id)
            results["matching"] = matching_result
            
            # If we got a match or exception, we're done
            if matching_result.get("classification") in ["MATCHED", "PROBABLE_MATCH", "BREAK"]:
                break
    
    # Summary
    print_header("E2E Test Summary")
    
    print(f"\nCorrelation ID: {correlation_id}")
    
    if results["bank"]:
        bank_status = "✓" if results["bank"].get("trade_id") else "❌"
        print(f"\nBank Trade: {bank_status}")
        if results["bank"].get("trade_id"):
            print(f"  Trade ID: {results['bank']['trade_id']}")
    
    if results["counterparty"]:
        cp_status = "✓" if results["counterparty"].get("trade_id") else "❌"
        print(f"\nCounterparty Trade: {cp_status}")
        if results["counterparty"].get("trade_id"):
            print(f"  Trade ID: {results['counterparty']['trade_id']}")
    
    if results["matching"]:
        match_status = results["matching"].get("classification", results["matching"].get("status", "UNKNOWN"))
        print(f"\nMatching Result: {match_status}")
        if results["matching"].get("match_score"):
            print(f"  Score: {results['matching']['match_score']}")
        if results["matching"].get("report_path"):
            print(f"  Report: {results['matching']['report_path']}")
    
    print(f"\n{'='*70}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="E2E Test for AgentCore Trade Matching")
    parser.add_argument("--bank", help="Path to bank PDF file")
    parser.add_argument("--counterparty", help="Path to counterparty PDF file")
    parser.add_argument("--both", action="store_true", help="Process both default PDFs")
    parser.add_argument("--match-only", help="Only run matching for given trade ID")
    
    args = parser.parse_args()
    
    if args.match_only:
        # Just run matching
        correlation_id = f"match_test_{uuid.uuid4().hex[:8]}"
        print_header("Trade Matching Test")
        run_matching(args.match_only, correlation_id)
        return
    
    bank_pdf = args.bank
    counterparty_pdf = args.counterparty
    
    if args.both:
        bank_pdf = "data/BANK/FAB_26933659.pdf"
        counterparty_pdf = "data/COUNTERPARTY/GCS381315_V1.pdf"
    
    if not bank_pdf and not counterparty_pdf:
        print("Please specify --bank, --counterparty, --both, or --match-only")
        parser.print_help()
        sys.exit(1)
    
    # Verify files exist
    if bank_pdf and not Path(bank_pdf).exists():
        print(f"Error: Bank PDF not found: {bank_pdf}")
        sys.exit(1)
    
    if counterparty_pdf and not Path(counterparty_pdf).exists():
        print(f"Error: Counterparty PDF not found: {counterparty_pdf}")
        sys.exit(1)
    
    run_e2e_test(bank_pdf, counterparty_pdf)


if __name__ == "__main__":
    main()
