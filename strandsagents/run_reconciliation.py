#!/usr/bin/env python3
"""
Trade Reconciliation Workflow Runner

This script demonstrates how to run the trade reconciliation workflow
using the Strands Agents SDK with proper sequential workflow patterns.
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
        "--check-status-only",
        action="store_true",
        help="Only check and display current workflow state without starting it"
    )
    
    parser.add_argument(
        "--numeric-tolerance",
        type=float,
        default=0.001,
        help="Numeric tolerance for field comparisons (default: 0.001 = 0.1%)"
    )
    
    parser.add_argument(
        "--string-similarity-threshold",
        type=float,
        default=0.85,
        help="String similarity threshold for text field matching (default: 0.85)"
    )
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    logger.info("Starting Trade Reconciliation Workflow")
    logger.info(f"Configuration: threshold={args.matcher_threshold}, bucket={args.report_bucket}")
    
    # Create configuration objects with command line parameters
    matcher_config = MatcherConfig(threshold=args.matcher_threshold)
    
    reconciler_config = ReconcilerConfig(
        numeric_tolerance={
            "total_notional_quantity": args.numeric_tolerance,
            "fixed_price": args.numeric_tolerance / 10  # Tighter tolerance for prices
        },
        string_similarity_threshold=args.string_similarity_threshold
    )
    
    reporter_config = ReportConfig(report_bucket=args.report_bucket)
    
    # Create workflow with configurations
    workflow = ReconciliationWorkflow(
        matcher_config=matcher_config,
        reconciler_config=reconciler_config,
        reporter_config=reporter_config
    )
    
    if args.check_status_only:
        # Just check current workflow state
        logger.info("Checking workflow state...")
        state = workflow.get_workflow_state()
        print("\n" + "="*50)
        print("CURRENT WORKFLOW STATE")
        print("="*50)
        print(json.dumps(state, indent=2, default=str))
    else:
        # Execute the complete workflow
        logger.info("Executing complete trade reconciliation workflow...")
        
        try:
            results = workflow.execute_workflow()
            
            # Display results
            print("\n" + "="*60)
            print("TRADE RECONCILIATION WORKFLOW RESULTS")
            print("="*60)
            
            # Print summary
            print(f"Workflow ID: {results['workflow_id']}")
            print(f"Status: {results['status']}")
            print(f"Start Time: {results['start_time']}")
            
            if 'end_time' in results:
                print(f"End Time: {results['end_time']}")
                print(f"Duration: {results.get('total_duration', 'N/A')} seconds")
            
            if results['status'] == 'failed':
                print(f"Failed at phase: {results.get('failed_phase', 'Unknown')}")
            
            # Print phase results
            print("\nPhase Results:")
            for phase_name, phase_result in results['phases'].items():
                print(f"\n{phase_name.upper()}:")
                print(f"  Status: {phase_result['status']}")
                if phase_result['status'] == 'error':
                    print(f"  Error: {phase_result.get('error', 'Unknown error')}")
                else:
                    # Truncate long results for readability
                    result_str = str(phase_result.get('result', 'No result'))
                    if len(result_str) > 300:
                        result_str = result_str[:300] + "... (truncated)"
                    print(f"  Result: {result_str}")
            
            # Print workflow state
            print("\n" + "="*50)
            print("FINAL WORKFLOW STATE")
            print("="*50)
            state = workflow.get_workflow_state()
            print(json.dumps(state, indent=2, default=str))
            
            # Save detailed results to file
            results_filename = f"reconciliation_results_{results['workflow_id']}.json"
            with open(results_filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Detailed results saved to: {results_filename}")
            
            # Exit with appropriate code
            if results['status'] == 'completed':
                logger.info("Workflow completed successfully!")
                return 0
            else:
                logger.error("Workflow failed!")
                return 1
                
        except Exception as e:
            logger.error(f"Unexpected error during workflow execution: {str(e)}")
            print(f"\nERROR: {str(e)}")
            return 1

if __name__ == "__main__":
    exit(main())
