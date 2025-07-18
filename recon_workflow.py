from strands import Agent
from strands_tools import workflow
import json
import logging
import boto3
from decimal import Decimal
from datetime import datetime
from models import MatcherConfig, ReconcilerConfig, ReportConfig

# Import all tools from agents.py
from agents import (
    fetch_unmatched_trades, find_potential_matches, compute_similarity,
    update_match_status, mark_as_unmatched, fetch_matched_trades,
    get_trade_pair, compare_fields, determine_overall_status,
    update_reconciliation_status, generate_reconciliation_report,
    store_report, fetch_reconciliation_results
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create an agent with workflow capability
agent = Agent(tools=[workflow])

def create_trade_reconciliation_workflow():
    """Create the trade reconciliation workflow with the three agents."""
    
    # Create a multi-agent workflow
    agent.tool.workflow(
        action="create",
        workflow_id="trade_reconciliation",
        tasks=[
            {
                "task_id": "trade_matcher",
                "description": "Match trades between bank and counterparty data sources using fuzzy matching",
                "system_prompt": """
                You are a trade matching agent responsible for pairing trades between bank and counterparty sources.
                
                Your tasks:
                1. Fetch unmatched trades from both sources using the fetch_unmatched_trades tool
                2. For each bank trade, find potential matches in counterparty data using find_potential_matches
                3. Compute similarity scores using compute_similarity tool
                4. Create match records for trades above threshold (0.90) using update_match_status
                5. Mark trades with no good matches as unmatched using mark_as_unmatched
                
                Use the following weights for similarity scoring:
                - trade_date: 0.30
                - counterparty_name: 0.20
                - notional: 0.25
                - currency: 0.15
                - product_type: 0.10
                
                Process trades in batches to avoid timeouts.
                """,
                "priority": 5
            },
            {
                "task_id": "trade_reconciler",
                "description": "Perform field-level reconciliation on matched trades",
                "dependencies": ["trade_matcher"],
                "system_prompt": """
                You are a trade reconciliation agent responsible for comparing fields between matched trades.
                
                Your tasks:
                1. Fetch matched trades pending reconciliation using fetch_matched_trades
                2. For each match, get the bank and counterparty trade details using get_trade_pair
                3. Compare fields with appropriate tolerances using compare_fields
                4. Determine overall reconciliation status using determine_overall_status
                5. Update reconciliation results using update_reconciliation_status
                
                Use the following configuration:
                - Numeric tolerances: 
                  - notional: 0.001 (0.1%)
                  - fixed_price: 0.0001 (0.01%)
                - Critical fields: trade_date, notional, currency
                - String similarity threshold: 0.85
                
                Process trades in batches to avoid timeouts.
                """,
                "priority": 3
            },
            {
                "task_id": "report_generator",
                "description": "Generate reconciliation reports for completed reconciliations",
                "dependencies": ["trade_reconciler"],
                "system_prompt": """
                You are a report generation agent responsible for creating reconciliation reports.
                
                Your tasks:
                1. Fetch completed reconciliation results using fetch_reconciliation_results
                2. Generate summary statistics and detailed report using generate_reconciliation_report
                3. Store the report in S3 using store_report
                
                Include the following in your reports:
                - Summary statistics (total matches, match status counts, average confidence)
                - Detailed results with field-level information
                - Timestamps and metadata
                
                Use 'trade-reconciliation-reports' as the S3 bucket name.
                """,
                "priority": 2
            }
        ]
    )
    
    logger.info("Created trade reconciliation workflow")


def execute_workflow():
    """Execute the trade reconciliation workflow."""
    # Start the workflow
    agent.tool.workflow(action="start", workflow_id="trade_reconciliation")
    logger.info("Started trade reconciliation workflow")
    
    # Check status
    status = agent.tool.workflow(action="status", workflow_id="trade_reconciliation")
    logger.info(f"Workflow status: {json.dumps(status, indent=2)}")
    
    return status


def check_workflow_status():
    """Check the status of the trade reconciliation workflow."""
    status = agent.tool.workflow(action="status", workflow_id="trade_reconciliation")
    logger.info(f"Workflow status: {json.dumps(status, indent=2)}")
    return status


class ReconciliationWorkflow:
    """Class to manage the trade reconciliation workflow."""
    
    def __init__(
        self,
        matcher_config: MatcherConfig = None,
        reconciler_config: ReconcilerConfig = None,
        reporter_config: ReportConfig = None
    ):
        """Initialize the workflow with optional configurations."""
        self.matcher_config = matcher_config or MatcherConfig()
        self.reconciler_config = reconciler_config or ReconcilerConfig()
        self.reporter_config = reporter_config or ReportConfig()
        self.workflow_id = "trade_reconciliation"
        
        # Create an agent with workflow capability and all the tools
        self.agent = Agent(tools=[
            workflow,
            fetch_unmatched_trades,
            find_potential_matches,
            compute_similarity,
            update_match_status,
            mark_as_unmatched,
            fetch_matched_trades,
            get_trade_pair,
            compare_fields,
            determine_overall_status,
            update_reconciliation_status,
            generate_reconciliation_report,
            store_report,
            fetch_reconciliation_results
        ])
    
    def define_workflow(self):
        """Define the workflow with the three agents."""
        self.agent.tool.workflow(
            action="create",
            workflow_id=self.workflow_id,
            tasks=[
                {
                    "task_id": "trade_matcher",
                    "description": "Match trades between bank and counterparty data sources using fuzzy matching",
                    "system_prompt": f"""
                    You are a trade matching agent responsible for pairing trades between bank and counterparty sources.
                    
                    Your tasks:
                    1. Fetch unmatched trades from both sources using the fetch_unmatched_trades tool
                    2. For each bank trade, find potential matches in counterparty data using find_potential_matches
                    3. Compute similarity scores using compute_similarity tool with the weights provided
                    4. Create match records for trades above threshold ({self.matcher_config.threshold}) using update_match_status
                    5. Mark trades with no good matches as unmatched using mark_as_unmatched
                    
                    Configuration:
                    - Weights: {json.dumps(self.matcher_config.weights)}
                    - Threshold: {self.matcher_config.threshold}
                    - Conflict band: {self.matcher_config.conflict_band}
                    
                    Process trades in batches to avoid timeouts.
                    """,
                    "priority": 5
                },
                {
                    "task_id": "trade_reconciler",
                    "description": "Perform field-level reconciliation on matched trades",
                    "dependencies": ["trade_matcher"],
                    "system_prompt": f"""
                    You are a trade reconciliation agent responsible for comparing fields between matched trades.
                    
                    Your tasks:
                    1. Fetch matched trades pending reconciliation using fetch_matched_trades
                    2. For each match, get the bank and counterparty trade details using get_trade_pair
                    3. Compare fields with appropriate tolerances using compare_fields
                    4. Determine overall reconciliation status using determine_overall_status
                    5. Update reconciliation results using update_reconciliation_status
                    
                    Configuration:
                    - Numeric tolerances: {json.dumps({k: float(v) for k, v in self.reconciler_config.numeric_tolerance.items()})}
                    - Critical fields: {json.dumps(self.reconciler_config.critical_fields)}
                    - String similarity threshold: {self.reconciler_config.string_similarity_threshold}
                    
                    Process trades in batches to avoid timeouts.
                    """,
                    "priority": 3
                },
                {
                    "task_id": "report_generator",
                    "description": "Generate reconciliation reports for completed reconciliations",
                    "dependencies": ["trade_reconciler"],
                    "system_prompt": f"""
                    You are a report generation agent responsible for creating reconciliation reports.
                    
                    Your tasks:
                    1. Fetch completed reconciliation results using fetch_reconciliation_results
                    2. Generate summary statistics and detailed report using generate_reconciliation_report
                    3. Store the report in S3 using store_report with the bucket name provided
                    
                    Configuration:
                    - Report bucket: {self.reporter_config.report_bucket}
                    - Include summary stats: {self.reporter_config.include_summary_stats}
                    - Include field details: {self.reporter_config.include_field_details}
                    
                    Include the following in your reports:
                    - Summary statistics (total matches, match status counts, average confidence)
                    - Detailed results with field-level information
                    - Timestamps and metadata
                    """,
                    "priority": 2
                }
            ]
        )
        
        logger.info(f"Defined trade reconciliation workflow with ID {self.workflow_id}")
    
    def execute_workflow(self):
        """Execute the workflow."""
        # Start the workflow
        self.agent.tool.workflow(action="start", workflow_id=self.workflow_id)
        logger.info(f"Started trade reconciliation workflow with ID {self.workflow_id}")
        
        # Return initial status
        return self.check_status()
    
    def check_status(self):
        """Check the status of the workflow."""
        status = self.agent.tool.workflow(action="status", workflow_id=self.workflow_id)
        logger.info(f"Workflow status: {json.dumps(status, indent=2)}")
        return status


if __name__ == "__main__":
    # Example usage
    workflow = ReconciliationWorkflow()
    workflow.define_workflow()
    workflow.execute_workflow()