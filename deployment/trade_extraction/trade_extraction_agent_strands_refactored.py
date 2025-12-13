"""
Trade Data Extraction Agent - LLM-Centric Strands SDK Implementation

This agent follows LLM-centric design principles:
1. LLM drives all decision-making
2. Tools handle external operations
3. Minimal hardcoded logic
4. Agent autonomously chooses tools based on context

Requirements: 2.1, 2.2, 3.3, 6.1, 6.2, 6.3, 6.4, 6.5
"""

import os
# Enable non-interactive tool execution for AgentCore Runtime
os.environ["BYPASS_TOOL_CONSENT"] = "true"

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging

# Strands SDK imports
from strands import Agent, tool
from strands.models import BedrockModel

# Try to import use_aws from different locations
try:
    from strands_tools import use_aws
    print("✓ Imported use_aws from strands_tools")
except ImportError:
    try:
        from strands import use_aws
        print("✓ Imported use_aws from strands")
    except ImportError:
        try:
            from strands.tools import use_aws
            print("✓ Imported use_aws from strands.tools")
        except ImportError:
            print("⚠ use_aws not found, will define custom implementation")
            use_aws = None

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Configuration
REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
BANK_TABLE = os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData")
COUNTERPARTY_TABLE = os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
AGENT_NAME = "trade-extraction-agent"
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")
DEPLOYMENT_STAGE = os.getenv("DEPLOYMENT_STAGE", "development")

# Fallback use_aws implementation if not available
if use_aws is None:
    @tool
    def use_aws(service_name: str, operation_name: str, parameters: dict, region: str = REGION, label: str = "") -> str:
        """
        AWS operations tool using boto3.
        
        Args:
            service_name: AWS service (e.g., "s3", "dynamodb")
            operation_name: Operation in snake_case (e.g., "get_object", "put_item")
            parameters: Operation-specific parameters
            region: AWS region
            label: Description of what you're doing
            
        Returns:
            JSON string with operation result
        """
        try:
            import boto3
            logger.info(f"AWS Operation: {service_name}.{operation_name} - {label}")
            
            client = boto3.client(service_name, region_name=region)
            
            # Convert snake_case to camelCase for boto3
            parts = operation_name.split('_')
            operation_method = parts[0] + ''.join(word.capitalize() for word in parts[1:])
            
            if hasattr(client, operation_method):
                result = getattr(client, operation_method)(**parameters)
                
                # Handle streaming responses for S3 GetObject
                if service_name == "s3" and operation_name == "get_object" and "Body" in result:
                    body_content = result["Body"].read()
                    if isinstance(body_content, bytes):
                        try:
                            body_content = body_content.decode('utf-8')
                        except UnicodeDecodeError:
                            body_content = body_content.decode('utf-8', errors='ignore')
                    result["Body"] = body_content
                
                return json.dumps({
                    "success": True, 
                    "result": result, 
                    "service": service_name, 
                    "operation": operation_name
                }, default=str)
            else:
                return json.dumps({
                    "success": False, 
                    "error": f"Operation {operation_method} not found on {service_name} client"
                })
                
        except Exception as e:
            logger.error(f"AWS operation failed: {service_name}.{operation_name} - {e}")
            return json.dumps({
                "success": False, 
                "error": str(e), 
                "error_type": type(e).__name__
            })

@tool
def get_extraction_context() -> str:
    """
    Get context about the extraction environment and business rules.
    
    Use this to understand:
    - Available DynamoDB tables and their purposes
    - Required data format and validation rules
    - Business constraints and data integrity requirements
    
    Returns:
        JSON string with extraction context and guidelines
    """
    context = {
        "tables": {
            "bank_trades": {
                "name": BANK_TABLE,
                "purpose": "Stores trades from bank systems",
                "source_type": "BANK",
                "region": REGION
            },
            "counterparty_trades": {
                "name": COUNTERPARTY_TABLE,
                "purpose": "Stores trades from counterparty systems",
                "source_type": "COUNTERPARTY",
                "region": REGION
            }
        },
        "data_format": {
            "storage": "DynamoDB typed format",
            "examples": {
                "string": {"S": "value"},
                "number": {"N": "123.45"},
                "boolean": {"BOOL": True}
            }
        },
        "required_fields": [
            "Trade_ID (partition key)",
            "TRADE_SOURCE (must match table: BANK or COUNTERPARTY)"
        ],
        "validation_rules": {
            "trade_id": "Must be unique and non-empty",
            "TRADE_SOURCE": "Must be exactly 'BANK' or 'COUNTERPARTY'",
            "dates": "Recommended format: YYYY-MM-DD",
            "numbers": "Must use DynamoDB N type with string representation"
        },
        "business_rules": {
            "table_routing": "BANK trades → BankTradeData, COUNTERPARTY trades → CounterpartyTradeData",
            "data_integrity": "TRADE_SOURCE field must match target table",
            "critical_fields": ["Trade_ID", "notional", "currency", "trade_date", "counterparty"]
        }
    }
    
    return json.dumps(context, indent=2)

@tool
def validate_extraction_result(trade_data: dict, target_table: str) -> str:
    """
    Validate extracted trade data against business rules.
    
    Args:
        trade_data: Extracted trade data
        target_table: Target DynamoDB table name
        
    Returns:
        JSON string with validation results
    """
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check required fields
    required_fields = ["Trade_ID", "TRADE_SOURCE"]
    for field in required_fields:
        if not trade_data.get(field):
            validation_results["valid"] = False
            validation_results["errors"].append(f"Missing required field: {field}")
    
    # Check TRADE_SOURCE matches table
    trade_source = trade_data.get("TRADE_SOURCE", "")
    if target_table == BANK_TABLE and trade_source != "BANK":
        validation_results["valid"] = False
        validation_results["errors"].append(f"TRADE_SOURCE '{trade_source}' doesn't match table '{target_table}'")
    elif target_table == COUNTERPARTY_TABLE and trade_source != "COUNTERPARTY":
        validation_results["valid"] = False
        validation_results["errors"].append(f"TRADE_SOURCE '{trade_source}' doesn't match table '{target_table}'")
    
    # Check data types for DynamoDB
    for key, value in trade_data.items():
        if value is not None and not isinstance(value, (str, int, float, bool)):
            validation_results["warnings"].append(f"Field '{key}' may need type conversion for DynamoDB")
    
    return json.dumps(validation_results)

@tool
def send_metrics(metric_name: str, value: float, dimensions: dict = None, unit: str = "Count") -> str:
    """
    Send custom metrics to CloudWatch.
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        dimensions: Optional dimensions for the metric
        unit: Metric unit (Count, Milliseconds, etc.)
        
    Returns:
        JSON string with operation result
    """
    try:
        if DEPLOYMENT_STAGE != "production":
            return json.dumps({"success": True, "message": "Metrics disabled in non-production"})
        
        import boto3
        cloudwatch = boto3.client('cloudwatch', region_name=REGION)
        
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': str(v)} for k, v in dimensions.items()
            ]
        
        cloudwatch.put_metric_data(
            Namespace='AgentCore/TradeExtraction',
            MetricData=[metric_data]
        )
        
        return json.dumps({"success": True, "metric_sent": metric_name})
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@tool
def log_processing_event(event_type: str, details: dict) -> str:
    """
    Log processing events for audit and monitoring.
    
    Args:
        event_type: Type of event (extraction_started, extraction_completed, error_occurred)
        details: Event details
        
    Returns:
        JSON string with logging result
    """
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "event_type": event_type,
            "details": details
        }
        
        logger.info(f"Processing Event: {json.dumps(log_entry)}")
        
        return json.dumps({"success": True, "logged": event_type})
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

# Health Check Handler
@app.ping
def health_check() -> PingStatus:
    """Health check for AgentCore Runtime."""
    return PingStatus.HEALTHY

# LLM-Centric System Prompt
SYSTEM_PROMPT = f"""You are an expert Trade Data Extraction Agent running on Amazon Bedrock AgentCore.

## Your Mission
Extract structured trade data from canonical adapter output and store it in the appropriate DynamoDB table. You have complete autonomy over your approach - analyze the situation, reason about the data, and determine the optimal extraction strategy.

## Environment
- **Agent**: {AGENT_NAME} v{AGENT_VERSION}
- **Model**: {BEDROCK_MODEL_ID}
- **Region**: {REGION}
- **S3 Bucket**: {S3_BUCKET}
- **Bank Table**: {BANK_TABLE}
- **Counterparty Table**: {COUNTERPARTY_TABLE}

## Available Tools

### AWS Operations
- **use_aws**: Direct AWS service operations (S3, DynamoDB, etc.)
  - Parameters: service_name, operation_name, parameters, region, label
  - Examples: Get S3 object, store DynamoDB item, scan table

### Context & Validation
- **get_extraction_context**: Get business rules, data formats, and validation requirements
- **validate_extraction_result**: Validate extracted data against business rules
- **log_processing_event**: Log important events for audit trail
- **send_metrics**: Send performance metrics to CloudWatch

## Decision-Making Framework

You are an intelligent agent. For each extraction task:

1. **Understand**: What information is available? What's the source type? What are the requirements?
2. **Plan**: Which tools do you need? What's the optimal sequence? How will you validate?
3. **Execute**: Use tools to achieve your goals. Adapt based on results.
4. **Validate**: Does the data meet requirements? Are there any issues?
5. **Store**: Save to the correct table with proper format.
6. **Monitor**: Log events and send metrics for observability.

## Key Constraints

- BANK trades must go to {BANK_TABLE}
- COUNTERPARTY trades must go to {COUNTERPARTY_TABLE}
- TRADE_SOURCE field must match the table (data integrity requirement)
- DynamoDB requires typed format: {{"S": "string"}}, {{"N": "number"}}, {{"BOOL": true}}
- Primary key is Trade_ID

## Your Autonomy

You decide:
- How to extract and structure the data
- Which fields to include based on relevance
- How to handle missing or ambiguous information
- What validation checks to perform
- The order of operations
- When to log events or send metrics

Think critically. Reason about edge cases. Optimize for accuracy and reliability.
"""

def create_extraction_agent() -> Agent:
    """Create and configure the Strands extraction agent."""
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.1,  # Low temperature for consistent financial data processing
        max_tokens=4096,
    )
    
    return Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            use_aws,
            get_extraction_context,
            validate_extraction_result,
            send_metrics,
            log_processing_event
        ]
    )

def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    LLM-Centric AgentCore Runtime entrypoint.
    
    This function provides minimal scaffolding and lets the LLM agent
    drive all decision-making through tool usage.
    """
    start_time = datetime.utcnow()
    
    # Extract basic information
    document_id = payload.get("document_id")
    canonical_output_location = payload.get("canonical_output_location")
    source_type = payload.get("source_type", "")
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    # Basic validation (minimal hardcoded logic)
    if not document_id or not canonical_output_location:
        return {
            "success": False,
            "error": "Missing required fields: document_id or canonical_output_location",
            "agent_name": AGENT_NAME
        }
    
    try:
        # Create the agent
        agent = create_extraction_agent()
        
        # Construct goal-oriented prompt - let LLM decide the approach
        prompt = f"""**Goal**: Extract and store trade data from canonical adapter output.

**Context**:
- Document: {document_id}
- Canonical Output Location: {canonical_output_location}
- Source Type: {source_type if source_type else "Unknown - determine from data"}
- Correlation ID: {correlation_id}

**Success Criteria**:
- Trade data extracted with all relevant fields
- Data stored in the correct DynamoDB table
- Data integrity maintained
- Processing events logged
- Metrics sent for monitoring

Analyze the situation and determine the best approach to achieve this goal. Use the available tools as needed.
"""
        
        # Let the LLM agent drive the entire process
        logger.info("Invoking LLM-centric trade extraction agent")
        result = agent(prompt)
        
        # Calculate processing time
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Extract response text
        if hasattr(result, 'message') and result.message:
            if hasattr(result.message, 'content') and result.message.content:
                content = result.message.content
                if isinstance(content, list) and len(content) > 0:
                    first_block = content[0]
                    response_text = first_block.get('text', str(result.message)) if isinstance(first_block, dict) else str(first_block)
                else:
                    response_text = str(content)
            else:
                response_text = str(result.message)
        else:
            response_text = str(result)
        
        # Extract token metrics if available
        token_metrics = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        try:
            if hasattr(result, 'metrics'):
                token_metrics["input_tokens"] = getattr(result.metrics, 'input_tokens', 0) or 0
                token_metrics["output_tokens"] = getattr(result.metrics, 'output_tokens', 0) or 0
            elif hasattr(result, 'usage'):
                token_metrics["input_tokens"] = getattr(result.usage, 'input_tokens', 0) or 0
                token_metrics["output_tokens"] = getattr(result.usage, 'output_tokens', 0) or 0
            token_metrics["total_tokens"] = token_metrics["input_tokens"] + token_metrics["output_tokens"]
        except Exception:
            pass
        
        return {
            "success": True,
            "document_id": document_id,
            "source_type": source_type,
            "correlation_id": correlation_id,
            "agent_response": response_text,
            "processing_time_ms": processing_time_ms,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "token_usage": token_metrics,
            "model_id": BEDROCK_MODEL_ID,
            "deployment_stage": DEPLOYMENT_STAGE
        }
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "document_id": document_id,
            "agent_name": AGENT_NAME,
            "processing_time_ms": processing_time_ms
        }

# Register with AgentCore Runtime
app.entrypoint(invoke)

def main():
    """CLI entry point for testing and AgentCore Runtime."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM-Centric Trade Data Extraction Agent")
    parser.add_argument("--mode", choices=["runtime", "test"], default="runtime")
    parser.add_argument("--document-id", help="Document ID for testing")
    parser.add_argument("--canonical-output-location", help="S3 location of canonical output")
    parser.add_argument("--source-type", choices=["BANK", "COUNTERPARTY"], help="Trade source type")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.mode == "test" and args.document_id and args.canonical_output_location:
        # CLI testing mode
        print(f"🧪 Testing LLM-Centric Trade Extraction Agent")
        print(f"Document ID: {args.document_id}")
        print(f"Canonical Output: {args.canonical_output_location}")
        print(f"Source Type: {args.source_type}")
        
        test_payload = {
            "document_id": args.document_id,
            "canonical_output_location": args.canonical_output_location,
            "source_type": args.source_type or "BANK",
            "correlation_id": f"cli_test_{uuid.uuid4().hex[:8]}"
        }
        
        result = invoke(test_payload)
        
        print(f"\n📊 Results:")
        print(f"Success: {result.get('success', False)}")
        if result.get('success'):
            print(f"Processing Time: {result.get('processing_time_ms', 0):.0f}ms")
            print(f"Token Usage: {result.get('token_usage', {})}")
            print(f"Agent Response: {result.get('agent_response', '')[:200]}...")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        return result.get('success', False)
    
    else:
        # AgentCore Runtime mode
        print(f"🚀 Starting LLM-Centric Trade Extraction Agent")
        app.run()

if __name__ == "__main__":
    main()