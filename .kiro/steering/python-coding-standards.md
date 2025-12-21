---
inclusion: fileMatch
fileMatchPattern: "**/*.py"
---

# Python Coding Standards

## Style & Formatting
- Follow PEP 8 with max line length of 100 characters
- Use type hints for all function parameters and return values
- Use Google-style docstrings for classes and functions
- Organize imports: standard library → third-party → local

## Type Hints Example
```python
from typing import Dict, List, Optional, Any, Tuple

def process_trade(
    trade_id: str,
    source_type: str,
    payload: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Process a trade confirmation.
    
    Args:
        trade_id: Unique trade identifier
        source_type: Either 'BANK' or 'COUNTERPARTY'
        payload: Trade data payload
        
    Returns:
        Processed trade data or None if processing fails
        
    Raises:
        ValueError: If source_type is invalid
    """
    pass
```

## Strands SDK Agent Pattern
```python
import os
os.environ["BYPASS_TOOL_CONSENT"] = "true"  # MUST be before strands imports

from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import use_aws

# Create agent with explicit model configuration
agent = Agent(
    model=BedrockModel(
        model_id="amazon.nova-pro-v1:0",
        region_name="us-east-1",
        temperature=0.1,
        max_tokens=4096,
    ),
    system_prompt=SYSTEM_PROMPT,
    tools=[use_aws]
)
```

## Error Handling
- Use structured logging with `structlog` or standard `logging`
- Include correlation_id in all log messages for tracing
- Return structured error responses, don't raise exceptions in agent handlers

## DynamoDB Typed Format
- Items use typed format: `{"S": "value"}`, `{"N": "123.45"}`
- Parse "N" type values as numbers for calculations
