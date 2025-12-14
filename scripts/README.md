# Operational Scripts

This directory contains useful scripts for operating and testing the AI Trade Matching System.

## Setup Scripts

### `populate_agent_registry.py`
Populates the Agent Registry DynamoDB table with realistic mock data for testing the web portal.

```bash
python scripts/populate_agent_registry.py
```

**Purpose**: Creates sample agent metrics data to test the dashboard functionality.

### `enhanced_populate_agent_registry.py`
Enhanced version with more detailed agent metrics and performance data.

```bash
python scripts/enhanced_populate_agent_registry.py
```

**Purpose**: Creates comprehensive test data with realistic performance patterns.

## Monitoring Scripts

### `collect_real_agent_metrics.py`
Collects real-time metrics from deployed agents for monitoring and analysis.

```bash
python scripts/collect_real_agent_metrics.py
```

**Purpose**: Gathers actual performance data from running agents for dashboard display.

## Processing Scripts

### `batch_process_trades.sh`
Batch processes multiple trade confirmations through the system.

```bash
./scripts/batch_process_trades.sh /path/to/trade/pdfs/
```

**Purpose**: Processes multiple PDF files in batch mode for bulk operations.

## Testing Scripts

### `run_property_test.sh`
Runs property-based tests using Hypothesis for comprehensive testing.

```bash
./scripts/run_property_test.sh
```

**Purpose**: Executes property-based tests to validate system behavior across various inputs.

### `performance/load_test.py`
Load testing script for performance validation.

```bash
python scripts/performance/load_test.py
```

**Purpose**: Tests system performance under various load conditions.

## Prerequisites

- AWS credentials configured
- Python dependencies installed (`pip install -r requirements.txt`)
- DynamoDB tables created (via Terraform)
- Agents deployed (for monitoring scripts)

## Usage Notes

- **Setup scripts** should be run after infrastructure deployment to populate test data
- **Monitoring scripts** require deployed agents to collect real metrics
- **Processing scripts** need sample PDF files and proper S3 bucket configuration
- **Testing scripts** can be run independently for validation

## Configuration

Most scripts use environment variables for configuration:

```bash
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=your-bucket-name
export DYNAMODB_AGENT_REGISTRY_TABLE=your-table-name
```

See individual script files for specific configuration requirements.