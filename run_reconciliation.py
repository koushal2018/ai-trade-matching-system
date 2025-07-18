#!/usr/bin/env python3
"""
Trade Reconciliation Workflow Runner

This script demonstrates how to run the trade reconciliation workflow
using the Strands Agents SDK.
"""

import logging
import json
import argparse
from recon_workflow import ReconciliationWorkflow
from models import MatcherConfig, ReconcilerConfig, ReportConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("trade-reconciliation")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run trade reconciliation workflow")
    
    parser.add_argument(
        "--matcher-threshold",
        type=float,
        default=0.90,
        help="Threshold for trade matching (default: 0.90)"
    )
    
    parser.add_argument(
        "--report-bucket",
        type=str,
        default="trade-reconciliation-reports",
        help="S3 bucket for storing reports"
    )
    
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check workflow status without starting it"
    )
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Create configuration objects
    matcher_config = MatcherConfig(threshold=args.matcher_threshold)
    reconciler_config = ReconcilerConfig()
    reporter_config = ReportConfig(report_bucket=args.report_bucket)
    
    # Create workflow
    workflow = ReconciliationWorkflow(
        matcher_config=matcher_config,
        reconciler_config=reconciler_config,
        reporter_config=reporter_config
    )
    
    # Define workflow
    workflow.define_workflow()
    
    if args.check_only:
        # Just check status
        status = workflow.check_status()
        print(json.dumps(status, indent=2))
    else:
        # Execute workflow
        logger.info("Starting trade reconciliation workflow")
        status = workflow.execute_workflow()
        print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()