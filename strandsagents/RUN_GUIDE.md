# How to Run the Trade Reconciliation Strands Agent

This guide provides step-by-step instructions for running your trade reconciliation agent implementation.

## Prerequisites

### 1. Install Required Dependencies
```bash
# Install Strands framework
pip install strands

# Install AWS SDK
pip install boto3

# Install other required dependencies
pip install python-dotenv
```

### 2. AWS Configuration
Ensure you have AWS credentials configured:

```bash
# Option 1: AWS CLI configuration
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

### 3. Set Environment Variables
```bash
# Required DynamoDB table names
export BANK_TRADES_TABLE=BankTrades
export COUNTERPARTY_TRADES_TABLE=CounterpartyTrades
export TRADE_MATCHES_TABLE=TradeMatches

# S3 bucket for reports
export REPORT_BUCKET=trade-reconciliation-reports

# AWS Region
export AWS_REGION=us-east-1
```

## Running Methods

### Method 1: Direct Script Execution

Navigate to the strandsagents directory and run:

```bash
cd strandsagents
python trade_reconciliation_agent.py
```

This will execute the `main()` function with default configuration.

### Method 2: Interactive Python Session

```python
# Start Python in the strandsagents directory
cd strandsagents
python

# Then in Python:
from trade_reconciliation_agent import TradeReconciliationAgent
from models import MatcherConfig, ReconcilerConfig, ReportConfig

# Create agent with custom configuration
agent = TradeReconciliationAgent(
    matcher_config=MatcherConfig(threshold=0.85),
    reconciler_config=ReconcilerConfig(
        numeric_tolerance={"total_notional_quantity": 0.001, "fixed_price": 0.0001}
    ),
    reporter_config=ReportConfig(report_bucket="your-bucket-name")
)

# Execute the complete workflow
print("Starting Trade Reconciliation Workflow...")
results = agent.execute_reconciliation()
print("Results:", results)
```

### Method 3: Custom Python Script

Create a new file `run_reconciliation.py`:

```python
#!/usr/bin/env python3
import os
from trade_reconciliation_agent import TradeReconciliationAgent
from models import MatcherConfig, ReconcilerConfig, ReportConfig

def main():
    # Configure the agent
    agent = TradeReconciliationAgent(
        matcher_config=MatcherConfig(
            threshold=0.8,  # Adjust matching threshold
            weights={
                "trade_date": 0.3,
                "counterparty_name": 0.2,
                "notional": 0.25,
                "currency": 0.15,
                "product_type": 0.1
            }
        ),
        reconciler_config=ReconcilerConfig(
            numeric_tolerance={
                "total_notional_quantity": 0.001,  # 0.1% tolerance
                "fixed_price": 0.0001               # 0.01% tolerance
            },
            critical_fields=["trade_date", "total_notional_quantity", "currency"]
        ),
        reporter_config=ReportConfig(
            report_bucket=os.getenv("REPORT_BUCKET", "trade-reconciliation-reports")
        )
    )
    
    print("=== Trade Reconciliation Workflow Started ===")
    
    # Execute the complete workflow
    try:
        results = agent.execute_reconciliation()
        print("\n=== Workflow Results ===")
        print(results)
        
        # Check final status
        print("\n=== Final Status Check ===")
        status = agent.get_workflow_status()
        print(status)
        
        # Generate summary report
        print("\n=== Generating Summary Report ===")
        report = agent.generate_ad_hoc_report("summary")
        print(report)
        
    except Exception as e:
        print(f"Error during workflow execution: {e}")
        return 1
    
    print("\n=== Workflow Completed Successfully ===")
    return 0

if __name__ == "__main__":
    exit(main())
```

Then run:
```bash
python run_reconciliation.py
```

## Individual Tool Testing

You can also test individual tools directly:

```python
from agents import fetch_unmatched_trades, validate_table_exists

# Test connectivity
print("Testing table connectivity...")
print("Bank trades table:", validate_table_exists("BankTrades"))

# Test fetching trades
print("Fetching unmatched bank trades...")
trades = fetch_unmatched_trades("BANK", limit=5)
print(f"Found {len(trades)} unmatched trades")
```

## Environment Setup Script

Create a setup script `setup_environment.sh`:

```bash
#!/bin/bash
echo "Setting up Trade Reconciliation Environment..."

# Set environment variables
export AWS_REGION=us-east-1
export BANK_TRADES_TABLE=BankTrades
export COUNTERPARTY_TRADES_TABLE=CounterpartyTrades
export TRADE_MATCHES_TABLE=TradeMatches
export REPORT_BUCKET=trade-reconciliation-reports

echo "Environment variables set:"
echo "AWS_REGION: $AWS_REGION"
echo "BANK_TRADES_TABLE: $BANK_TRADES_TABLE"
echo "COUNTERPARTY_TRADES_TABLE: $COUNTERPARTY_TRADES_TABLE"
echo "TRADE_MATCHES_TABLE: $TRADE_MATCHES_TABLE"
echo "REPORT_BUCKET: $REPORT_BUCKET"

echo "Ready to run trade reconciliation agent!"
```

Run the setup:
```bash
chmod +x setup_environment.sh
source setup_environment.sh
```

## Troubleshooting

### Common Issues and Solutions

1. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'strands'
   ```
   **Solution**: Install the strands framework: `pip install strands`

2. **AWS Connectivity Issues**
   ```
   NoCredentialsError: Unable to locate credentials
   ```
   **Solution**: Configure AWS credentials using `aws configure` or environment variables

3. **Table Not Found Errors**
   ```
   ResourceNotFoundException: Table 'BankTrades' does not exist
   ```
   **Solution**: Create the required DynamoDB tables or verify table names in environment variables

4. **Permission Errors**
   ```
   AccessDenied: User is not authorized to perform...
   ```
   **Solution**: Ensure your AWS user/role has proper DynamoDB and S3 permissions

### Validation Commands

Test your setup with these validation commands:

```python
# Test AWS connectivity
from agents import get_dynamodb_resource, validate_table_exists

try:
    dynamodb = get_dynamodb_resource()
    print("✓ DynamoDB connection successful")
    
    # Test table access
    tables = ["BankTrades", "CounterpartyTrades", "TradeMatches"]
    for table in tables:
        if validate_table_exists(table):
            print(f"✓ Table {table} is accessible")
        else:
            print(f"✗ Table {table} not found or not accessible")
            
except Exception as e:
    print(f"✗ AWS setup issue: {e}")
```

## Expected Output

When running successfully, you should see output similar to:

```
=== Trade Reconciliation Workflow Started ===
Starting workflow initialization...
✓ Timestamp recorded: 2024-01-15T10:30:00
✓ Workflow log created for ID: trade_reconciliation_20240115_103000
✓ AWS connectivity validated

Trade Matching Phase:
✓ Fetched 25 unmatched bank trades
✓ Fetched 30 unmatched counterparty trades
✓ Found 18 potential matches with scores above 0.85
✓ Created 15 successful matches
✓ Marked 10 trades as unmatched

Field Reconciliation Phase:
✓ Processing 15 matched trade pairs
✓ 12 trades fully matched
✓ 2 trades partially matched
✓ 1 trade with critical mismatch

Report Generation:
✓ Report generated: recon-report-20240115-103045
✓ Report stored at: s3://trade-reconciliation-reports/reports/recon-report-20240115-103045.json

=== Workflow Completed Successfully ===
```

This guide should help you run your Strands-based trade reconciliation agent successfully!
