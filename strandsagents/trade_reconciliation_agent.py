#!/usr/bin/env python3
"""
Trade Reconciliation Agent using Strands Framework

This implementation leverages custom Strands tools for orchestrating
a comprehensive trade reconciliation workflow using AWS services.
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from strands import Agent, tool
from agents import (
    fetch_unmatched_trades, find_potential_matches, compute_similarity,
    update_match_status, mark_as_unmatched, fetch_matched_trades,
    get_trade_pair, compare_fields, determine_overall_status,
    update_reconciliation_status, generate_reconciliation_report,
    store_report, fetch_reconciliation_results
)

# Import configuration models
from models import MatcherConfig, ReconcilerConfig, ReportConfig, TableConfig

@tool
def get_current_timestamp() -> str:
    """Get the current timestamp in ISO format."""
    return datetime.now().isoformat()

@tool
def create_workflow_log(workflow_id: str, message: str) -> Dict[str, Any]:
    """Create a workflow log entry."""
    return {
        "workflow_id": workflow_id,
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "status": "logged"
    }

@tool
def validate_aws_connectivity() -> Dict[str, Any]:
    """Validate connectivity to AWS services."""
    from agents import validate_table_exists, get_dynamodb_resource
    
    table_config = TableConfig.from_environment()
    results = {}
    
    try:
        # Test DynamoDB connectivity
        get_dynamodb_resource()
        results["dynamodb"] = "connected"
        
        # Test table access
        results["tables"] = {
            "bank_trades": validate_table_exists(table_config.bank_trades_table),
            "counterparty_trades": validate_table_exists(table_config.counterparty_trades_table),
            "trade_matches": validate_table_exists(table_config.trade_matches_table)
        }
        
    except Exception as e:
        results["error"] = str(e)
        results["status"] = "failed"
    
    return results

class TradeReconciliationAgent:
    """
    Main Trade Reconciliation Agent that orchestrates the entire reconciliation process
    using Strands framework with custom tools.
    """
    
    def __init__(self, 
                 matcher_config: MatcherConfig = None,
                 reconciler_config: ReconcilerConfig = None,
                 reporter_config: ReportConfig = None):
        """Initialize the Trade Reconciliation Agent with configurations."""
        
        self.matcher_config = matcher_config or MatcherConfig()
        self.reconciler_config = reconciler_config or ReconcilerConfig()
        self.reporter_config = reporter_config or ReportConfig()
        self.table_config = TableConfig.from_environment()
        
        # Create the orchestration agent with custom tools
        self.agent = Agent(
            system_prompt=self._get_system_prompt(),
            tools=[
                # Workflow management tools
                get_current_timestamp,
                create_workflow_log,
                validate_aws_connectivity,
                
                # Trade matching tools
                fetch_unmatched_trades,
                find_potential_matches,
                compute_similarity,
                update_match_status,
                mark_as_unmatched,
                
                # Reconciliation tools
                fetch_matched_trades,
                get_trade_pair,
                compare_fields,
                determine_overall_status,
                update_reconciliation_status,
                
                # Reporting tools
                generate_reconciliation_report,
                store_report,
                fetch_reconciliation_results
            ]
        )
        
        self.workflow_id = f"trade_reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def _get_system_prompt(self) -> str:
        """Generate the system prompt for the orchestration agent."""
        return f"""
You are the Trade Reconciliation Orchestrator, responsible for managing the complete 
trade reconciliation process using custom Strands tools.

## Your Mission:
Orchestrate a comprehensive trade reconciliation workflow that matches trades between 
bank and counterparty sources, performs detailed field comparisons, and generates 
actionable reports.

## Workflow Configuration:
- **Matching Threshold**: {self.matcher_config.threshold}
- **Field Weights**: {json.dumps(self.matcher_config.weights)}
- **Numeric Tolerances**: {json.dumps({k: float(v) for k, v in self.reconciler_config.numeric_tolerance.items()})}
- **Critical Fields**: {', '.join(self.reconciler_config.critical_fields)}
- **Report Bucket**: {self.reporter_config.report_bucket}

## AWS Configuration:
- **Bank Trades Table**: {self.table_config.bank_trades_table}
- **Counterparty Trades Table**: {self.table_config.counterparty_trades_table}
- **Trade Matches Table**: {self.table_config.trade_matches_table}
- **AWS Region**: {os.getenv('AWS_REGION', 'us-east-1')}

## Available Tools:
### Workflow Management:
- **get_current_timestamp**: Get timestamps for audit trails
- **create_workflow_log**: Track workflow progress and log events
- **validate_aws_connectivity**: Test AWS service connectivity

### Trade Matching:
- **fetch_unmatched_trades**: Get unmatched trades from BANK or COUNTERPARTY sources
- **find_potential_matches**: Find potential matches for a trade in the opposite source
- **compute_similarity**: Calculate similarity score between two trades
- **update_match_status**: Update match status and create match records
- **mark_as_unmatched**: Mark trades that couldn't be matched

### Reconciliation:
- **fetch_matched_trades**: Get matched trades that need reconciliation
- **get_trade_pair**: Retrieve bank and counterparty trade details for a match
- **compare_fields**: Compare fields between matched trades
- **determine_overall_status**: Determine overall reconciliation status
- **update_reconciliation_status**: Update reconciliation results in database

### Reporting:
- **generate_reconciliation_report**: Create comprehensive reconciliation reports
- **store_report**: Save reports to S3
- **fetch_reconciliation_results**: Retrieve reconciliation results

## Process Overview:
1. **Setup & Validation**: Initialize workflow, validate AWS connectivity
2. **Trade Matching**: Find and match trades between sources using similarity scoring
3. **Field Reconciliation**: Compare matched trades field-by-field
4. **Report Generation**: Create comprehensive reconciliation reports
5. **Cleanup & Logging**: Finalize workflow and save audit logs

Always maintain detailed logs of all operations for audit and troubleshooting purposes.
Execute the workflow systematically, using the appropriate tools for each phase.
"""

    def execute_reconciliation(self) -> str:
        """
        Execute the complete trade reconciliation workflow.
        
        Returns:
            str: The agent's response about the workflow execution
        """
        return self.agent(f"""
Execute the complete trade reconciliation workflow using the following systematic approach:

## Step 1: Initialize Workflow
1. Use 'get_current_timestamp' to record the workflow start time
2. Use 'create_workflow_log' to create initial log entry with workflow ID: {self.workflow_id}
3. Use 'validate_aws_connectivity' to ensure all required AWS services and tables are accessible

## Step 2: Trade Matching Phase
1. Use 'fetch_unmatched_trades' to get unmatched trades from BANK source (limit: 50)
2. Use 'fetch_unmatched_trades' to get unmatched trades from COUNTERPARTY source (limit: 50)
3. For each bank trade:
   - Use 'find_potential_matches' to find counterparty candidates
   - For each potential match:
     - Use 'compute_similarity' with weights: {json.dumps(self.matcher_config.weights)}
     - If similarity score >= {self.matcher_config.threshold}:
       - Use 'update_match_status' to create the match
   - If no matches found, use 'mark_as_unmatched'
4. Use 'create_workflow_log' to record matching phase completion

## Step 3: Field Reconciliation Phase
1. Use 'fetch_matched_trades' to get all pending reconciliation matches
2. For each match:
   - Use 'get_trade_pair' to retrieve full trade details
   - Use 'compare_fields' with tolerances: {json.dumps({k: float(v) for k, v in self.reconciler_config.numeric_tolerance.items()})}
   - Use 'determine_overall_status' with critical fields: {self.reconciler_config.critical_fields}
   - Use 'update_reconciliation_status' to save reconciliation results
3. Use 'create_workflow_log' to record reconciliation phase completion

## Step 4: Report Generation
1. Use 'fetch_reconciliation_results' to get all completed reconciliation results
2. Use 'generate_reconciliation_report' to create comprehensive summary
3. Use 'store_report' to save to S3 bucket: {self.reporter_config.report_bucket}
4. Use 'create_workflow_log' to record final completion

## Step 5: Final Summary
1. Use 'get_current_timestamp' to record completion time
2. Provide comprehensive summary including:
   - Total trades processed from each source
   - Number of matches found and their average confidence
   - Reconciliation status breakdown (fully matched, partially matched, critical mismatches)
   - Report location and key statistics
   - Any errors or warnings encountered
   - Performance metrics and workflow duration

Execute each step systematically and provide detailed progress updates.
""")

    def get_workflow_status(self) -> str:
        """Get the current status of the reconciliation workflow."""
        return self.agent(f"""
Check the current status of the trade reconciliation workflow with ID: {self.workflow_id}

1. Use 'get_current_timestamp' to get current time
2. Use 'fetch_reconciliation_results' to check recent results
3. Use 'validate_aws_connectivity' to verify system health

Provide a status summary including:
- Current workflow phase and progress
- Recent reconciliation activity
- System health status
- Any issues requiring attention
""")

    def generate_ad_hoc_report(self, report_type: str = "summary") -> str:
        """Generate an ad-hoc reconciliation report."""
        return self.agent(f"""
Generate an ad-hoc reconciliation report of type: {report_type}

1. Use 'fetch_reconciliation_results' to get current reconciliation data
2. Use 'generate_reconciliation_report' to compile the analysis
3. Use 'store_report' to save to S3 bucket: {self.reporter_config.report_bucket}

Include in the report:
- Current matching statistics and trends
- Reconciliation status breakdown with details
- Recent activity summary
- Data quality metrics and recommendations
- Any outstanding issues or exceptions
""")

def main():
    """Example usage of the Trade Reconciliation Agent."""
    
    # Create agent with custom configuration
    agent = TradeReconciliationAgent(
        matcher_config=MatcherConfig(threshold=0.85),
        reconciler_config=ReconcilerConfig(
            numeric_tolerance={"total_notional_quantity": 0.001, "fixed_price": 0.0001}
        ),
        reporter_config=ReportConfig(report_bucket="trade-reconciliation-reports")
    )
    
    print("Starting Trade Reconciliation Workflow...")
    
    # Execute the complete workflow
    results = agent.execute_reconciliation()
    print("Workflow Results:")
    print(results)
    
    # Check final status
    status = agent.get_workflow_status()
    print("\nFinal Status:")
    print(status)

if __name__ == "__main__":
    main()
