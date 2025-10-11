import sys
import warnings

from datetime import datetime

from latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent

warnings.filterwarnings("ignore", category=DeprecationWarning)


def run():
    # Define your inputs
    inputs = {
        'document_path': 's3://otc-menat-2025/COUNTERPARTY/GCS382857_V2.pdf',
        'unique_identifier': 'GCS382857',
        'source_type': 'COUNTERPARTY',
        's3_bucket': 'otc-menat-2025',
        's3_key': 'COUNTERPARTY/GCS382857_V2',
        'dynamodb_bank_table': 'BankTradeData',
        'dynamodb_counterparty_table': 'CounterpartyTradeData',
        'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S')
    }

    # Create crew instance - MCP lifecycle managed automatically by @CrewBase
    crew_instance = LatestTradeMatchingAgent()

    # Run the crew - MCP server will auto-start on first get_mcp_tools() call
    # and auto-cleanup after kickoff completes
    result = crew_instance.crew().kickoff(inputs=inputs)

    print("\nCrew execution completed successfully!")
    print(f"Usage metrics: {crew_instance.crew().usage_metrics}")

    return result

if __name__ == "__main__":
    run()