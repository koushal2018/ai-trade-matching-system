#!/usr/bin/env python3
"""
End-to-end test with comprehensive token usage tracking.
"""

import json
import time
import boto3
from datetime import datetime
from typing import Dict, Any, List
from analyze_token_usage import TokenUsageAnalyzer


class E2ETokenTest:
    """End-to-end test with token usage tracking."""
    
    def __init__(self, region: str = "us-east-1", bucket_name: str = None):
        self.region = region
        self.bucket_name = bucket_name or "trade-matching-system-agentcore-production"
        self.s3 = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.analyzer = TokenUsageAnalyzer(region)
        
    def upload_test_pdfs(self, test_files: List[str]) -> List[str]:
        """Upload test PDFs and return S3 keys."""
        uploaded_keys = []
        
        for file_path in test_files:
            # Determine if it's a bank or counterparty file based on naming
            prefix = "BANK/" if "bank" in file_path.lower() else "COUNTERPARTY/"
            key = f"{prefix}test_{int(time.time())}_{file_path.split('/')[-1]}"
            
            try:
                self.s3.upload_file(file_path, self.bucket_name, key)
                uploaded_keys.append(key)
                print(f"📤 Uploaded: {key}")
            except Exception as e:
                print(f"❌ Failed to upload {file_path}: {e}")
                
        return uploaded_keys
    
    def wait_for_processing(self, correlation_ids: List[str], timeout: int = 300) -> Dict[str, Any]:
        """Wait for all trades to be processed and collect results."""
        start_time = time.time()
        results = {}
        
        while time.time() - start_time < timeout:
            all_complete = True
            
            for corr_id in correlation_ids:
                if corr_id not in results:
                    # Check if processing is complete by looking for final status
                    # This would depend on your specific implementation
                    # For now, we'll simulate by waiting and checking logs
                    all_complete = False
                    
            if all_complete:
                break
                
            time.sleep(10)  # Check every 10 seconds
            
        return results
    
    def run_e2e_test(self, test_files: List[str]) -> Dict[str, Any]:
        """Run complete end-to-end test with token tracking."""
        print("🚀 Starting E2E Test with Token Tracking")
        print("=" * 50)
        
        # Record start time for token analysis
        test_start = datetime.utcnow()
        
        # Upload test files
        print("\n1️⃣ Uploading test PDFs...")
        uploaded_keys = self.upload_test_pdfs(test_files)
        
        if not uploaded_keys:
            return {"error": "No files uploaded successfully"}
        
        # Wait for processing to complete
        print(f"\n2️⃣ Waiting for processing of {len(uploaded_keys)} files...")
        correlation_ids = [key.replace('/', '_').replace('.', '_') for key in uploaded_keys]
        
        # Give some time for processing
        time.sleep(60)  # Wait 1 minute for processing to start
        
        # Analyze token usage
        print("\n3️⃣ Analyzing token usage...")
        hours_elapsed = max(1, int((datetime.utcnow() - test_start).total_seconds() / 3600))
        token_report = self.analyzer.generate_report(hours_back=hours_elapsed)
        
        # Get final processing results
        print("\n4️⃣ Collecting final results...")
        processing_results = self.get_processing_results(uploaded_keys)
        
        # Compile comprehensive report
        report = {
            "test_metadata": {
                "start_time": test_start.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "test_files": test_files,
                "uploaded_keys": uploaded_keys,
                "correlation_ids": correlation_ids
            },
            "token_usage": token_report,
            "processing_results": processing_results,
            "cost_estimate": self.estimate_costs(token_report)
        }
        
        return report
    
    def get_processing_results(self, s3_keys: List[str]) -> Dict[str, Any]:
        """Get processing results for uploaded files."""
        results = {}
        
        # Check for output files in S3
        for key in s3_keys:
            try:
                # Look for corresponding output files
                output_prefix = key.replace('.pdf', '_output.json')
                
                response = self.s3.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=output_prefix
                )
                
                if 'Contents' in response:
                    results[key] = {
                        "status": "processed",
                        "output_files": [obj['Key'] for obj in response['Contents']]
                    }
                else:
                    results[key] = {"status": "pending"}
                    
            except Exception as e:
                results[key] = {"status": "error", "error": str(e)}
                
        return results
    
    def estimate_costs(self, token_report: Dict[str, Any]) -> Dict[str, float]:
        """Estimate costs based on token usage."""
        # Bedrock pricing (approximate, check current pricing)
        pricing = {
            "claude_sonnet_input": 0.003 / 1000,    # $0.003 per 1K input tokens
            "claude_sonnet_output": 0.015 / 1000,   # $0.015 per 1K output tokens
            "nova_pro_input": 0.0008 / 1000,        # $0.0008 per 1K input tokens
            "nova_pro_output": 0.0032 / 1000        # $0.0032 per 1K output tokens
        }
        
        summary = token_report.get('summary', {})
        input_tokens = summary.get('total_input_tokens', 0)
        output_tokens = summary.get('total_output_tokens', 0)
        
        # Estimate assuming mix of models (adjust based on your usage)
        estimated_cost = (
            (input_tokens * pricing['claude_sonnet_input'] * 0.7) +  # 70% Claude
            (output_tokens * pricing['claude_sonnet_output'] * 0.7) +
            (input_tokens * pricing['nova_pro_input'] * 0.3) +       # 30% Nova
            (output_tokens * pricing['nova_pro_output'] * 0.3)
        )
        
        return {
            "estimated_total_cost": round(estimated_cost, 4),
            "cost_per_token": round(estimated_cost / max(input_tokens + output_tokens, 1), 6),
            "pricing_assumptions": pricing
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Run E2E test with token tracking')
    parser.add_argument('--files', nargs='+', required=True, help='Test PDF files to process')
    parser.add_argument('--bucket', type=str, help='S3 bucket name')
    parser.add_argument('--region', type=str, default='us-east-1', help='AWS region')
    parser.add_argument('--output', type=str, help='Output report file')
    
    args = parser.parse_args()
    
    tester = E2ETokenTest(region=args.region, bucket_name=args.bucket)
    report = tester.run_e2e_test(args.files)
    
    # Print summary
    print("\n📊 E2E TEST RESULTS")
    print("=" * 50)
    
    token_summary = report.get('token_usage', {}).get('summary', {})
    print(f"Total Tokens Used: {token_summary.get('total_tokens', 0):,}")
    print(f"Estimated Cost: ${report.get('cost_estimate', {}).get('estimated_total_cost', 0):.4f}")
    
    processing_results = report.get('processing_results', {})
    processed_count = sum(1 for r in processing_results.values() if r.get('status') == 'processed')
    print(f"Files Processed: {processed_count}/{len(processing_results)}")
    
    # Save full report
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n💾 Full report saved to: {args.output}")


if __name__ == "__main__":
    main()