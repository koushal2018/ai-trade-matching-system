#!/usr/bin/env python3
"""
Comprehensive Token Usage Testing Pipeline
Creates test PDFs, processes them through the system, and analyzes token consumption.
"""

import os
import sys
import time
import json
import boto3
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import argparse

# Add deployment path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'deployment', 's3_event_processor'))
sys.path.append(os.path.join(os.path.dirname(__file__)))

from create_test_pdf import create_batch_test_pdfs, create_bank_trade_pdf, create_counterparty_trade_pdf
from analyze_token_usage import TokenUsageAnalyzer


class TokenUsageTestPipeline:
    """Orchestrates end-to-end token usage testing."""
    
    def __init__(self, region: str = "us-east-1", bucket_name: str = "trade-matching-system-agentcore-production"):
        self.region = region
        self.bucket_name = bucket_name
        self.s3 = boto3.client('s3', region_name=region)
        self.analyzer = TokenUsageAnalyzer(region)
        
    def upload_test_pdfs(self, pdf_pairs: List[Tuple[str, str]]) -> Dict[str, List[str]]:
        """Upload test PDFs to S3 and return upload details."""
        uploaded = {"BANK": [], "COUNTERPARTY": []}
        
        for bank_pdf, counterparty_pdf in pdf_pairs:
            try:
                # Upload bank PDF
                bank_key = f"BANK/{bank_pdf}"
                self.s3.upload_file(bank_pdf, self.bucket_name, bank_key)
                uploaded["BANK"].append(bank_key)
                print(f"✅ Uploaded: s3://{self.bucket_name}/{bank_key}")
                
                # Upload counterparty PDF
                counterparty_key = f"COUNTERPARTY/{counterparty_pdf}"
                self.s3.upload_file(counterparty_pdf, self.bucket_name, counterparty_key)
                uploaded["COUNTERPARTY"].append(counterparty_key)
                print(f"✅ Uploaded: s3://{self.bucket_name}/{counterparty_key}")
                
            except Exception as e:
                print(f"❌ Failed to upload {bank_pdf}/{counterparty_pdf}: {e}")
                
        return uploaded
    
    def wait_for_processing(self, wait_minutes: int = 5) -> None:
        """Wait for agent processing to complete."""
        print(f"⏳ Waiting {wait_minutes} minutes for agent processing...")
        
        for minute in range(wait_minutes):
            remaining = wait_minutes - minute
            print(f"   {remaining} minutes remaining...")
            time.sleep(60)
            
        print("✅ Processing wait complete")
    
    def run_comprehensive_test(self, 
                             pdf_count: int = 3, 
                             complexity_mix: bool = True,
                             wait_minutes: int = 5) -> Dict[str, Any]:
        """Run comprehensive token usage test."""
        
        print("🚀 Starting Comprehensive Token Usage Test")
        print("=" * 60)
        
        # Step 1: Create test PDFs
        print(f"\n📄 Step 1: Creating {pdf_count} test PDF pairs...")
        pdf_pairs = create_batch_test_pdfs(pdf_count, complexity_mix)
        
        if not pdf_pairs:
            raise Exception("Failed to create test PDFs")
            
        print(f"✅ Created {len(pdf_pairs)} PDF pairs")
        
        # Step 2: Get baseline token usage
        print(f"\n📊 Step 2: Getting baseline token usage...")
        baseline_report = self.analyzer.generate_report(hours_back=1)
        baseline_tokens = baseline_report['summary']['total_tokens']
        print(f"✅ Baseline: {baseline_tokens:,} tokens")
        
        # Step 3: Upload PDFs to trigger processing
        print(f"\n☁️ Step 3: Uploading PDFs to S3...")
        uploaded = self.upload_test_pdfs(pdf_pairs)
        total_uploaded = len(uploaded["BANK"]) + len(uploaded["COUNTERPARTY"])
        print(f"✅ Uploaded {total_uploaded} files")
        
        # Step 4: Wait for processing
        print(f"\n⏳ Step 4: Waiting for agent processing...")
        self.wait_for_processing(wait_minutes)
        
        # Step 5: Analyze token usage
        print(f"\n📈 Step 5: Analyzing token usage...")
        final_report = self.analyzer.generate_report(hours_back=1)
        final_tokens = final_report['summary']['total_tokens']
        
        # Calculate test-specific usage
        test_tokens = final_tokens - baseline_tokens
        tokens_per_pdf = test_tokens / max(len(pdf_pairs) * 2, 1)  # 2 PDFs per pair
        
        # Compile comprehensive results
        results = {
            "test_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "pdf_count": len(pdf_pairs),
                "complexity_mix": complexity_mix,
                "wait_minutes": wait_minutes,
                "files_uploaded": total_uploaded
            },
            "token_analysis": {
                "baseline_tokens": baseline_tokens,
                "final_tokens": final_tokens,
                "test_tokens": test_tokens,
                "tokens_per_pdf": round(tokens_per_pdf, 2),
                "tokens_per_trade_pair": round(test_tokens / max(len(pdf_pairs), 1), 2)
            },
            "baseline_report": baseline_report,
            "final_report": final_report,
            "uploaded_files": uploaded,
            "pdf_files_created": pdf_pairs
        }
        
        # Print summary
        print(f"\n🎯 TEST RESULTS SUMMARY")
        print("=" * 40)
        print(f"PDFs Processed: {len(pdf_pairs)} pairs ({total_uploaded} files)")
        print(f"Baseline Tokens: {baseline_tokens:,}")
        print(f"Final Tokens: {final_tokens:,}")
        print(f"Test Usage: {test_tokens:,} tokens")
        print(f"Per PDF: {tokens_per_pdf:,.1f} tokens")
        print(f"Per Trade Pair: {results['token_analysis']['tokens_per_trade_pair']:,.1f} tokens")
        
        if final_report.get('cost_analysis'):
            test_cost = (test_tokens / (final_tokens or 1)) * final_report['cost_analysis']['total_estimated_cost']
            print(f"Estimated Test Cost: ${test_cost:.4f}")
        
        return results
    
    def cleanup_test_files(self, pdf_pairs: List[Tuple[str, str]]) -> None:
        """Clean up local test PDF files."""
        for bank_pdf, counterparty_pdf in pdf_pairs:
            try:
                if os.path.exists(bank_pdf):
                    os.remove(bank_pdf)
                if os.path.exists(counterparty_pdf):
                    os.remove(counterparty_pdf)
            except Exception as e:
                print(f"Warning: Failed to cleanup {bank_pdf}/{counterparty_pdf}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Comprehensive Token Usage Testing Pipeline')
    parser.add_argument('--pdf-count', type=int, default=3, help='Number of PDF pairs to test')
    parser.add_argument('--wait-minutes', type=int, default=5, help='Minutes to wait for processing')
    parser.add_argument('--no-complexity-mix', action='store_true', help='Use standard complexity only')
    parser.add_argument('--output', type=str, help='Output file for results (JSON)')
    parser.add_argument('--cleanup', action='store_true', help='Clean up test files after completion')
    parser.add_argument('--region', type=str, default='us-east-1', help='AWS region')
    parser.add_argument('--bucket', type=str, default='trade-matching-system-agentcore-production', help='S3 bucket name')
    
    args = parser.parse_args()
    
    pipeline = TokenUsageTestPipeline(region=args.region, bucket_name=args.bucket)
    
    try:
        results = pipeline.run_comprehensive_test(
            pdf_count=args.pdf_count,
            complexity_mix=not args.no_complexity_mix,
            wait_minutes=args.wait_minutes
        )
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {args.output}")
        
        # Cleanup if requested
        if args.cleanup:
            print(f"\n🧹 Cleaning up test files...")
            pipeline.cleanup_test_files(results['pdf_files_created'])
            print("✅ Cleanup complete")
            
        print(f"\n🎉 Token usage testing complete!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()