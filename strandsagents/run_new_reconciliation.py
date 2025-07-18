#!/usr/bin/env python3
"""
New Trade Reconciliation Runner using Strands Built-in Tools

This script demonstrates the proper way to run trade reconciliation using
the new Strands-based agent implementation with out-of-the-box tools.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trade_reconciliation_agent import TradeReconciliationAgent
from models import MatcherConfig, ReconcilerConfig, ReportConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("trade-reconciliation-runner")

def setup_environment_variables():
    """Set up required environment variables if not already set."""
    
    # Set default AWS region if not specified
    if not os.getenv('AWS_REGION') and not os.getenv('AWS_DEFAULT_REGION'):
        os.environ['AWS_REGION'] = 'us-east-1'
        logger.info("Set default AWS_REGION to us-east-1")
    
    # Set table names if not specified (using defaults from models.py)
    table_vars = {
        'BANK_TRADES_TABLE': 'BankTrades',
        'COUNTERPARTY_TRADES_TABLE': 'CounterpartyTrades', 
        'TRADE_MATCHES_TABLE': 'TradeMatches'
    }
    
    for var, default in table_vars.items():
        if not os.getenv(var):
            os.environ[var] = default
            logger.info(f"Set default {var} to {default}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run trade reconciliation using Strands built-in tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python run_new_reconciliation.py
  
  # Run with custom matching threshold
  python run_new_reconciliation.py --threshold 0.95
  
  # Run with custom S3 bucket
  python run_new_reconciliation.py --report-bucket my-custom-bucket
  
  # Check status only
  python run_new_reconciliation.py --status-only
  
  # Generate ad-hoc report
  python run_new_reconciliation.py --generate-report summary
        """
    )
    
    # Matching configuration
    parser.add_argument(
        '--threshold', 
        type=float, 
        default=0.90,
        help='Similarity threshold for trade matching (default: 0.90)'
    )
    
    parser.add_argument(
        '--conflict-band',
        type=float,
        default=0.05,
        help='Conflict band for ambiguous matches (default: 0.05)'
    )
    
    # Reconciliation configuration
    parser.add_argument(
        '--numeric-tolerance',
        type=float,
        default=0.001,
        help='Numeric tolerance for field comparisons (default: 0.001)'
    )
    
    parser.add_argument(
        '--string-similarity',
        type=float,
        default=0.85,
        help='String similarity threshold (default: 0.85)'
    )
    
    # Reporting configuration
    parser.add_argument(
        '--report-bucket',
        type=str,
        default='trade-reconciliation-reports',
        help='S3 bucket for storing reports (default: trade-reconciliation-reports)'
    )
    
    # Execution modes
    parser.add_argument(
        '--status-only',
        action='store_true',
        help='Only check workflow status without running reconciliation'
    )
    
    parser.add_argument(
        '--generate-report',
        type=str,
        choices=['summary', 'detailed', 'errors'],
        help='Generate an ad-hoc report of the specified type'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without making any changes'
    )
    
    return parser.parse_args()

def create_agent_with_config(args) -> TradeReconciliationAgent:
    """Create the trade reconciliation agent with the provided configuration."""
    
    # Create matcher configuration
    matcher_config = MatcherConfig(
        threshold=args.threshold,
        conflict_band=args.conflict_band,
        weights={
            "trade_date": 0.30,
            "counterparty_name": 0.20,
            "notional": 0.25,
            "currency": 0.15,
            "product_type": 0.10
        }
    )
    
    # Create reconciler configuration
    reconciler_config = ReconcilerConfig(
        numeric_tolerance={
            "total_notional_quantity": args.numeric_tolerance,
            "fixed_price": args.numeric_tolerance / 10  # Tighter tolerance for prices
        },
        string_similarity_threshold=args.string_similarity,
        critical_fields=["trade_date", "total_notional_quantity", "currency"]
    )
    
    # Create reporter configuration
    reporter_config = ReportConfig(
        report_bucket=args.report_bucket,
        include_summary_stats=True,
        include_field_details=True
    )
    
    # Create and return the agent
    agent = TradeReconciliationAgent(
        matcher_config=matcher_config,
        reconciler_config=reconciler_config,
        reporter_config=reporter_config
    )
    
    logger.info("Created Trade Reconciliation Agent with configuration:")
    logger.info(f"  - Matching threshold: {args.threshold}")
    logger.info(f"  - Numeric tolerance: {args.numeric_tolerance}")
    logger.info(f"  - String similarity: {args.string_similarity}")
    logger.info(f"  - Report bucket: {args.report_bucket}")
    
    return agent

def main():
    """Main execution function."""
    try:
        # Parse arguments and setup environment
        args = parse_arguments()
        setup_environment_variables()
        
        logger.info("="*60)
        logger.info("STRANDS TRADE RECONCILIATION AGENT")
        logger.info("="*60)
        
        # Create the agent with configuration
        agent = create_agent_with_config(args)
        
        # Execute based on the mode
        if args.status_only:
            logger.info("Checking workflow status...")
            status = agent.get_workflow_status()
            print("\n" + "="*50)
            print("WORKFLOW STATUS")
            print("="*50)
            print(json.dumps(status, indent=2, default=str))
            
        elif args.generate_report:
            logger.info(f"Generating {args.generate_report} report...")
            report = agent.generate_ad_hoc_report(args.generate_report)
            print("\n" + "="*50)
            print(f"{args.generate_report.upper()} REPORT")
            print("="*50)
            print(json.dumps(report, indent=2, default=str))
            
        else:
            # Run the full reconciliation workflow
            if args.dry_run:
                logger.info("DRY RUN MODE - No changes will be made")
                # TODO: Implement dry run mode in the agent
            
            logger.info("Starting trade reconciliation workflow...")
            start_time = datetime.now()
            
            results = agent.execute_reconciliation()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "="*60)
            print("RECONCILIATION RESULTS")
            print("="*60)
            print(json.dumps(results, indent=2, default=str))
            print(f"\nWorkflow completed in {duration:.2f} seconds")
            
            # Get final status
            logger.info("Retrieving final workflow status...")
            final_status = agent.get_workflow_status()
            print("\n" + "="*50)
            print("FINAL STATUS")
            print("="*50)
            print(json.dumps(final_status, indent=2, default=str))
            
        logger.info("Trade reconciliation workflow completed successfully")
        
    except KeyboardInterrupt:
        logger.warning("Workflow interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error running trade reconciliation: {str(e)}")
        logger.exception("Full traceback:")
        sys.exit(1)

if __name__ == "__main__":
    main()
