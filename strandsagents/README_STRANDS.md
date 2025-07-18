# Trade Reconciliation Agents - Strands Framework Implementation

This directory contains a comprehensive trade reconciliation system built using the **Strands Framework**, leveraging both custom tools and proper orchestration patterns.

## Implementation Overview

### Architecture
The implementation follows Strands best practices with:
- **Custom Tools**: Domain-specific tools for trade operations using `@tool` decorator
- **Orchestration Agent**: High-level agent that coordinates the entire workflow
- **Configuration-Driven**: Flexible configuration through model classes
- **AWS Integration**: Native integration with DynamoDB, S3, and other AWS services

### Key Components

#### 1. Core Tools (`agents.py`)
Contains all the custom Strands tools for trade reconciliation:

```python
from strands import Agent, tool

@tool
def fetch_unmatched_trades(source: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch unmatched trades from the specified source (BANK or COUNTERPARTY)."""
    # Implementation details...

@tool
def compute_similarity(bank_trade: Dict, counterparty_trade: Dict, weights: Dict) -> float:
    """Compute similarity score between two trades."""
    # Implementation details...
```

**Available Tools:**
- `fetch_unmatched_trades`: Retrieve unmatched trades from DynamoDB
- `find_potential_matches`: Find candidate matches using composite keys
- `compute_similarity`: Calculate similarity scores with configurable weights
- `update_match_status`: Create match records and update trade status
- `mark_as_unmatched`: Mark trades that couldn't be matched
- `fetch_matched_trades`: Get trades ready for reconciliation
- `get_trade_pair`: Retrieve full trade details for matched pairs
- `compare_fields`: Perform field-by-field comparison with tolerances
- `determine_overall_status`: Assess overall reconciliation status
- `update_reconciliation_status`: Save reconciliation results
- `generate_reconciliation_report`: Create comprehensive reports
- `store_report`: Save reports to S3
- `fetch_reconciliation_results`: Retrieve reconciliation data

#### 2. Orchestration Agent (`trade_reconciliation_agent.py`)
The main orchestration class that uses Strands framework:

```python
from strands import Agent, tool
from agents import (
    fetch_unmatched_trades, find_potential_matches, compute_similarity,
    # ... all other tools
)

class TradeReconciliationAgent:
    def __init__(self, matcher_config=None, reconciler_config=None, reporter_config=None):
        self.agent = Agent(
            system_prompt=self._get_system_prompt(),
            tools=[
                # Workflow management tools
                get_current_timestamp,
                create_workflow_log,
                validate_aws_connectivity,
                
                # Import all custom tools
                fetch_unmatched_trades,
                find_potential_matches,
                # ... etc
            ]
        )
```

#### 3. Configuration Models (`models.py`)
Proper data models for configuration and data structures:
- `MatcherConfig`: Similarity thresholds and field weights
- `ReconcilerConfig`: Field comparison tolerances and critical fields
- `ReportConfig`: Reporting configuration and S3 settings
- `TableConfig`: DynamoDB table names and configuration

## Strands Framework Features Used

### 1. Custom Tool Creation
Following Strands patterns for tool creation:

```python
@tool
def my_trade_tool(param1: str, param2: int) -> Dict[str, Any]:
    """
    Well-documented tool description for the language model.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2
    
    Returns:
        Dict containing the tool results
    """
    # Tool implementation
    return {"status": "success", "data": "..."}
```

### 2. Agent Orchestration
Using Strands `Agent` class for orchestration:

```python
agent = Agent(
    system_prompt="Detailed system prompt explaining the agent's role...",
    tools=[list_of_custom_tools]
)

# Execute workflow through natural language
result = agent("Execute the complete trade reconciliation workflow...")
```

### 3. Systematic Workflow Execution
The agent receives detailed step-by-step instructions:

```python
return self.agent(f"""
Execute the complete trade reconciliation workflow using the following systematic approach:

## Step 1: Initialize Workflow
1. Use 'get_current_timestamp' to record the workflow start time
2. Use 'create_workflow_log' to create initial log entry
3. Use 'validate_aws_connectivity' to ensure AWS services are accessible

## Step 2: Trade Matching Phase
1. Use 'fetch_unmatched_trades' to get trades from both sources
2. For each bank trade, find potential counterparty matches
3. Calculate similarity scores and create matches above threshold

...continue with detailed steps...
""")
```

## AWS Integration

### Required AWS Services
- **DynamoDB**: Trade storage and matching
  - `BankTrades` table
  - `CounterpartyTrades` table
  - `TradeMatches` table
- **S3**: Report storage
- **IAM**: Proper permissions for service access

### Environment Configuration
```bash
export AWS_REGION=us-east-1
export BANK_TRADES_TABLE=BankTrades
export COUNTERPARTY_TRADES_TABLE=CounterpartyTrades
export TRADE_MATCHES_TABLE=TradeMatches
export REPORT_BUCKET=trade-reconciliation-reports
```

## Usage Examples

### Basic Usage
```python
from trade_reconciliation_agent import TradeReconciliationAgent
from models import MatcherConfig, ReconcilerConfig, ReportConfig

# Create agent with custom configuration
agent = TradeReconciliationAgent(
    matcher_config=MatcherConfig(threshold=0.85),
    reconciler_config=ReconcilerConfig(
        numeric_tolerance={"total_notional_quantity": 0.001}
    ),
    reporter_config=ReportConfig(report_bucket="my-reports-bucket")
)

# Execute complete workflow
results = agent.execute_reconciliation()
print(results)
```

### Status Monitoring
```python
# Check workflow status
status = agent.get_workflow_status()
print(status)

# Generate ad-hoc reports
report = agent.generate_ad_hoc_report("detailed")
print(report)
```

### Direct Tool Usage
```python
# Access tools directly through the agent
trades = agent.agent.tool.fetch_unmatched_trades(source="BANK", limit=10)
print(f"Found {len(trades)} unmatched bank trades")
```

## Key Strands Framework Benefits

### 1. **Natural Language Orchestration**
The agent understands complex workflow instructions in natural language, making it easy to modify and extend workflows without changing code structure.

### 2. **Tool Composition**
Custom tools can be easily combined and reused across different agents and workflows.

### 3. **Robust Error Handling**
The framework provides built-in error handling and retry mechanisms for tool execution.

### 4. **Audit Trail**
All tool executions are logged and traceable for compliance and debugging.

### 5. **Flexible Configuration**
Workflow behavior can be modified through configuration without code changes.

## Implementation Best Practices Applied

### 1. **Comprehensive Tool Documentation**
Each tool has detailed docstrings explaining:
- Purpose and functionality
- Parameter types and descriptions
- Return value format
- Usage examples and limitations

### 2. **Error Handling and Logging**
- Proper exception handling in all tools
- Detailed logging for audit trails
- Graceful degradation when services are unavailable

### 3. **Configuration Management**
- Environment-based configuration
- Validation of required settings
- Default values for optional parameters

### 4. **AWS Best Practices**
- Proper credential management
- Region configuration
- Resource validation before use
- Efficient querying strategies

### 5. **Scalable Architecture**
- Modular tool design for reusability
- Configurable limits and thresholds
- Batch processing capabilities
- Comprehensive reporting and monitoring

## Testing and Validation

The implementation includes built-in validation tools:
- `validate_aws_connectivity`: Tests all AWS service connections
- Configuration validation on startup
- Table existence verification
- Credential and permission checks

## Future Enhancements

The Strands framework makes it easy to extend functionality:
- Add new matching algorithms as tools
- Implement real-time monitoring tools
- Create additional report formats
- Add integration with external systems
- Implement workflow scheduling and automation

This implementation demonstrates proper use of the Strands framework for complex, multi-step business processes with robust error handling, comprehensive logging, and flexible configuration management.
