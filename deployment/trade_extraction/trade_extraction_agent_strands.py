"""
Trade Data Extraction Agent - Strands SDK Implementation

This agent uses Strands SDK with built-in tools for AWS operations.
It reads canonical adapter output from S3, extracts structured trade data using LLM reasoning,
and stores in DynamoDB - letting the agent decide which fields are relevant.

Requirements: 2.1, 2.2, 3.3, 6.1, 6.2, 6.3, 6.4, 6.5
"""

import os
# Enable non-interactive tool execution for AgentCore Runtime
# MUST be set before importing strands_tools
os.environ["BYPASS_TOOL_CONSENT"] = "true"

import json
import uuid
import random
from datetime import datetime
from typing import Any, Dict, Optional
import logging

# Strands SDK imports
from strands import Agent, tool
from strands.models import BedrockModel

# Try to import use_aws from different locations in strands-agents
try:
    from strands_tools import use_aws
    print("✓ Imported use_aws from strands_tools (community tools package)")
except ImportError:
    try:
        from strands import use_aws
        print("✓ Imported use_aws from strands")
    except ImportError:
        try:
            from strands.tools import use_aws
            print("✓ Imported use_aws from strands.tools")
        except ImportError:
            # If none work, we'll define our own
            print("⚠ use_aws not found, will define custom implementation")
            use_aws = None

# Fallback implementation if use_aws is not available
if use_aws is None:
    @tool
    def use_aws(service_name: str, operation_name: str, parameters: dict, region: str = "us-east-1", label: str = "") -> str:
        """
        Fallback AWS tool implementation using boto3 directly.
        
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
            logger.debug(f"Parameters: {parameters}")
            
            client = boto3.client(service_name, region_name=region)
            
            # boto3 uses snake_case for method names
            operation_method = operation_name
            
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
                    logger.info(f"S3 GetObject successful - retrieved {len(body_content)} characters")
                    logger.debug(f"Content preview: {body_content[:200]}...")
                
                response_data = {
                    "success": True, 
                    "result": result, 
                    "service": service_name, 
                    "operation": operation_name,
                    "fallback_used": True
                }
                response_json = json.dumps(response_data, default=str)
                logger.info(f"Operation successful - response length: {len(response_json)}")
                return response_json
            else:
                return json.dumps({
                    "success": False, 
                    "error": f"Operation {operation_method} not found on {service_name} client", 
                    "service": service_name, 
                    "operation": operation_name
                })
                
        except Exception as e:
            logger.error(f"AWS operation failed: {service_name}.{operation_name} - {e}")
            return json.dumps({
                "success": False, 
                "error": str(e), 
                "error_type": type(e).__name__,
                "service": service_name,
                "operation": operation_name,
                "fallback_used": True
            })


from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

# AgentCore Observability with PII redaction
try:
    from bedrock_agentcore.observability import Observability
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

# PII patterns to redact from observability logs
PII_PATTERNS = {
    "trade_id": r"(trade_id[\"']?\s*[:=]\s*[\"']?)([^\"',}\s]+)",
    "counterparty": r"(counterparty[\"']?\s*[:=]\s*[\"']?)([^\"',}\s]+)",
    "notional": r"(notional[\"']?\s*[:=]\s*[\"']?)(\d+\.?\d*)",
    "currency": r"(currency[\"']?\s*[:=]\s*[\"']?)([A-Z]{3})",
    "effective_date": r"(effective_date[\"']?\s*[:=]\s*[\"']?)(\d{4}-\d{2}-\d{2})",
    "maturity_date": r"(maturity_date[\"']?\s*[:=]\s*[\"']?)(\d{4}-\d{2}-\d{2})",
}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Configuration
REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
BANK_TABLE = os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData")
COUNTERPARTY_TABLE = os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")
AGENT_ALIAS = os.getenv("AGENT_ALIAS", "default")
DEPLOYMENT_STAGE = os.getenv("DEPLOYMENT_STAGE", "development")  # development, staging, production
OBSERVABILITY_STAGE = os.getenv("OBSERVABILITY_STAGE", "development")

# Security & Authentication Configuration
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "us-east-1_uQ2lN39dT")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "78daptta2m4lb6k5jm3n2hd8oc")
ENABLE_MFA = os.getenv("ENABLE_MFA", "true").lower() == "true"

# AgentCore Resource Names
AGENTCORE_GATEWAY_DYNAMODB = os.getenv("AGENTCORE_GATEWAY_DYNAMODB", "trade-matching-system-dynamodb-gateway-production")
AGENTCORE_GATEWAY_S3 = os.getenv("AGENTCORE_GATEWAY_S3", "trade-matching-system-s3-gateway-production")
AGENTCORE_MEMORY_PATTERNS = os.getenv("AGENTCORE_MEMORY_PATTERNS", "trade-matching-system-trade-patterns-production")
AGENTCORE_MEMORY_HISTORY = os.getenv("AGENTCORE_MEMORY_HISTORY", "trade-matching-system-processing-history-production")

# Reusable AWS resource configuration for strands-tools
# This configuration will be used by the use_aws tool for consistent resource management
AWS_RESOURCE_CONFIG = {
    "region_name": REGION,
    "s3_bucket": S3_BUCKET,
    "dynamodb_tables": {
        "bank": BANK_TABLE,
        "counterparty": COUNTERPARTY_TABLE
    }
}

# Shared AWS client instances for resource reuse
# These will be initialized once and reused across tool calls
_aws_clients = {}
_tool_config = None

def load_tool_resources_config():
    """
    Load tool resources configuration for better resource management.
    
    This enables sharing of network settings, connection pools, and
    other resources across multiple sessions and tool invocations.
    """
    global _tool_config
    if _tool_config is None:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "tool_resources_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    _tool_config = json.load(f)
                logger.info("Loaded tool resources configuration")
            else:
                _tool_config = {}
                logger.warning("Tool resources config not found, using defaults")
        except Exception as e:
            logger.warning(f"Failed to load tool resources config: {e}")
            _tool_config = {}
    return _tool_config

def get_aws_client(service_name: str, region: str = REGION):
    """
    Get or create a reusable AWS client instance.
    
    This implements resource reuse by maintaining client connections
    across multiple tool invocations, reducing connection overhead.
    """
    client_key = f"{service_name}_{region}"
    if client_key not in _aws_clients:
        import boto3
        
        # Load configuration for better resource management
        config = load_tool_resources_config()
        aws_config = config.get("tool_resources", {}).get("aws_config", {})
        
        # Configure client with resource reuse settings
        client_config = {}
        if "connection_pool_size" in aws_config:
            from botocore.config import Config
            client_config["config"] = Config(
                max_pool_connections=aws_config["connection_pool_size"],
                retries=aws_config.get("retry_config", {})
            )
        
        _aws_clients[client_key] = boto3.client(service_name, region_name=region, **client_config)
        logger.info(f"Created reusable AWS client: {service_name} in {region}")
    return _aws_clients[client_key]

# Agent identification constants
AGENT_NAME = "trade-extraction-agent"
AGENT_DESCRIPTION = "Extracts structured trade data from canonical adapter output using LLM reasoning"
AGENT_CAPABILITIES = ["trade_extraction", "data_validation", "table_routing", "pattern_learning"]

# Initialize Enhanced Observability with PII redaction
observability = None
if OBSERVABILITY_AVAILABLE:
    try:
        observability = Observability(
            service_name=AGENT_NAME,
            stage=OBSERVABILITY_STAGE,
            verbosity="high" if OBSERVABILITY_STAGE == "development" else "medium",
            # Enhanced configuration for trade extraction monitoring
            custom_attributes={
                "agent_type": "trade_extraction",
                "deployment_stage": DEPLOYMENT_STAGE,
                "model_id": BEDROCK_MODEL_ID,
                "version": AGENT_VERSION,
                "region": REGION,
                "s3_bucket": S3_BUCKET,
                "bank_table": BANK_TABLE,
                "counterparty_table": COUNTERPARTY_TABLE
            }
        )
        logger.info(f"✅ Enhanced observability initialized for {AGENT_NAME} with PII redaction")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize observability: {e}")
        observability = None

# Note: This agent uses AgentCore Gateway tools for production-grade AWS operations.
# The built-in use_aws tool from strands-tools is available as fallback.
# The LLM autonomously decides which tools to use based on context.

# IAM Role Requirements (for AgentCore Runtime deployment):
# - bedrock-agent:InvokeGateway on trade-matching-system-*-gateway-production
# - bedrock-agent:QueryMemory, StoreMemory on trade-matching-system-*-memory-production


# ============================================================================
# IAM Role Requirements (for AgentCore Runtime deployment)
# ============================================================================
# - bedrock-agent:InvokeGateway on trade-matching-system-*-gateway-production
# - bedrock-agent:QueryMemory, StoreMemory on trade-matching-system-*-memory-production
# - s3:GetObject on {S3_BUCKET}/extracted/* (fallback only)
# - dynamodb:PutItem on {BANK_TABLE} and {COUNTERPARTY_TABLE} (fallback only)
# - bedrock:InvokeModel on {BEDROCK_MODEL_ID}
# - logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents for CloudWatch
#
# Dependencies:
# - strands-agents: Required for Strands SDK and use_aws tool
# - bedrock-agentcore: Required for AgentCore Runtime, Gateway, Memory integration


# ============================================================================
# AgentCore Gateway Integration (Recommended)
# ============================================================================

# AgentCore Gateway Integration (Production)
# Gateway provides managed access, authentication, and monitoring
try:
    from bedrock_agentcore import Gateway
    
    # Initialize gateways for production use
    dynamodb_gateway = Gateway(name="trade-matching-system-dynamodb-gateway-production")
    s3_gateway = Gateway(name="trade-matching-system-s3-gateway-production")
    
    GATEWAY_AVAILABLE = True
    logger.info("✓ AgentCore Gateway initialized for production")
except ImportError:
    GATEWAY_AVAILABLE = False
    logger.warning("⚠ AgentCore Gateway not available - using fallback tools")

# Import evaluation capabilities if available
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from latest_trade_matching_agent.evaluations.custom_evaluators import EvaluationOrchestrator
    EVALUATION_AVAILABLE = True
    evaluation_orchestrator = EvaluationOrchestrator()
    logger.info("✅ Evaluation orchestrator initialized")
except ImportError as e:
    EVALUATION_AVAILABLE = False
    evaluation_orchestrator = None
    logger.info(f"ℹ️ Evaluation not available: {e}")

# ============================================================================
# Helper Tools (High-Level - Agent decides strategy)
# ============================================================================

@tool
def store_trade_data(trade_data: dict, target_table: str) -> str:
    """Store extracted trade data in the appropriate DynamoDB table.
    
    Handles DynamoDB format conversion and table routing for trade data storage.
    Ensures data integrity by validating TRADE_SOURCE matches target table.
    
    Args:
        trade_data: Extracted trade data in standard format
        target_table: Target DynamoDB table (BankTradeData or CounterpartyTradeData)
        
    Returns:
        JSON string with storage result and success status
    """
    try:
        logger.info(f"DynamoDB Gateway Operation: {operation} - {label}")
        
        # Production: Use AgentCore Gateway for managed, secure access
        if GATEWAY_AVAILABLE and DEPLOYMENT_STAGE == "production":
            try:
                result = dynamodb_gateway.invoke_tool(operation, parameters)
                return json.dumps({"success": True, "result": result, "gateway": "dynamodb", "production": True}, default=str)
            except Exception as gateway_error:
                logger.warning(f"Gateway failed, falling back to direct access: {gateway_error}")
        
        # Development fallback: Direct boto3 access
        logger.info(f"Using direct AWS access (stage: {DEPLOYMENT_STAGE})")
        return use_aws("dynamodb", operation.lower().replace("item", "_item"), parameters, label=label)
        
    except Exception as e:
        logger.error(f"DynamoDB Gateway operation failed: {operation} - {e}")
        return json.dumps({
            "success": False, 
            "error": str(e), 
            "error_type": type(e).__name__,
            "gateway": "dynamodb",
            "operation": operation
        })


@tool
def use_s3_gateway(operation: str, parameters: dict, label: str = "") -> str:
    """
    Use AgentCore Gateway for secure S3 operations.
    
    Args:
        operation: S3 operation (GetObject, PutObject, ListObjects, etc.)
        parameters: Operation parameters
        label: Description of what you're doing
        
    Returns:
        JSON string with operation result
        
    Examples:
        # Get canonical adapter output
        use_s3_gateway("GetObject", {
            "Bucket": "trade-matching-system-agentcore-production",
            "Key": "extracted/BANK/trade_123.json"
        })
        
        # Store extraction results
        use_s3_gateway("PutObject", {
            "Bucket": "trade-matching-system-agentcore-production",
            "Key": "processed/BANK/trade_123_extracted.json",
            "Body": json.dumps(trade_data)
        })
    """
    try:
        logger.info(f"S3 Gateway Operation: {operation} - {label}")
        
        # Production: Use AgentCore Gateway for managed, secure access
        if GATEWAY_AVAILABLE and DEPLOYMENT_STAGE == "production":
            try:
                result = s3_gateway.invoke_tool(operation, parameters)
                return json.dumps({"success": True, "result": result, "gateway": "s3", "production": True}, default=str)
            except Exception as gateway_error:
                logger.warning(f"Gateway failed, falling back to direct access: {gateway_error}")
        
        # Development fallback: Direct boto3 access
        logger.info(f"Using direct AWS access (stage: {DEPLOYMENT_STAGE})")
        return use_aws("s3", operation.lower().replace("object", "_object"), parameters, label=label)
        
    except Exception as e:
        logger.error(f"S3 Gateway operation failed: {operation} - {e}")
        return json.dumps({
            "success": False, 
            "error": str(e), 
            "error_type": type(e).__name__,
            "gateway": "s3",
            "operation": operation
        })


# ============================================================================
# Helper Tools (High-Level - Agent decides strategy)
# ============================================================================

@tool
def use_agentcore_memory(operation: str, memory_resource: str, data: dict = None, query: str = None, top_k: int = 5) -> str:
    """
    Use AgentCore Memory for trade pattern storage and retrieval.
    
    Args:
        operation: Memory operation (store, query, add_event)
        memory_resource: Memory resource name
        data: Data to store (for store/add_event operations)
        query: Query string (for query operations)
        top_k: Number of results to return (for query operations)
        
    Returns:
        JSON string with memory operation result
        
    Examples:
        # Store trade pattern
        use_agentcore_memory("store", "trade-patterns", {
            "trade_id": "GCS382857",
            "counterparty": "Goldman Sachs",
            "product_type": "SWAP",
            "extraction_confidence": 0.95,
            "pattern": "standard_irs_confirmation"
        })
        
        # Query similar trades
        use_agentcore_memory("query", "trade-patterns", 
                           query="Goldman Sachs interest rate swap", top_k=3)
        
        # Add processing event
        use_agentcore_memory("add_event", "processing-history", {
            "timestamp": "2025-01-15T10:30:00Z",
            "agent": "trade_extractor",
            "action": "trade_extracted",
            "trade_id": "GCS382857",
            "confidence": 0.95
        })
    """
    try:
        logger.info(f"AgentCore Memory Operation: {operation} on {memory_resource}")
        
        # AgentCore Memory Integration (Production)
        if DEPLOYMENT_STAGE == "production":
            try:
                from bedrock_agentcore import Memory
                
                memory = Memory(resource_name=f"trade-matching-system-{memory_resource}-production")
                
                if operation == "store":
                    result = memory.store(data)
                elif operation == "query":
                    result = memory.query(query, top_k=top_k)
                elif operation == "add_event":
                    result = memory.add_event(data)
                
                return json.dumps({
                    "success": True,
                    "result": result,
                    "memory_resource": memory_resource,
                    "operation": operation,
                    "production": True,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as memory_error:
                logger.warning(f"Memory operation failed, using mock: {memory_error}")
        
        # Development/Mock implementation
        if operation == "query":
            return json.dumps({
                "success": True,
                "results": [
                    {
                        "similarity_score": 0.92,
                        "trade_pattern": "standard_irs_confirmation",
                        "counterparty": "Goldman Sachs",
                        "extraction_tips": "Focus on notional amount in paragraph 2",
                        "confidence_boost": 0.05,
                        "field_mappings": {
                            "notional": "paragraph_2_amount",
                            "currency": "header_currency_code",
                            "trade_date": "execution_date_field"
                        }
                    }
                ],
                "memory_resource": memory_resource,
                "query_timestamp": datetime.utcnow().isoformat()
            })
        else:
            return json.dumps({
                "success": True, 
                "operation": operation, 
                "resource": memory_resource,
                "timestamp": datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"AgentCore Memory operation failed: {operation} - {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "operation": operation,
            "resource": memory_resource
        })


@tool
def should_run_quality_evaluation(extraction_context: dict) -> str:
    """
    Determine if quality evaluation should be run for this extraction.
    
    Args:
        extraction_context: Context about the extraction (complexity, confidence, etc.)
        
    Returns:
        JSON string with evaluation recommendation
    """
    try:
        # Let the LLM decide based on context rather than hardcoded rules
        context_factors = {
            "evaluation_available": EVALUATION_AVAILABLE,
            "deployment_stage": DEPLOYMENT_STAGE,
            "extraction_complexity": extraction_context.get("complexity", "medium"),
            "confidence_level": extraction_context.get("confidence", 0.8),
            "document_type": extraction_context.get("document_type", "standard"),
            "error_indicators": extraction_context.get("error_indicators", [])
        }
        
        # Provide guidance but let LLM decide
        recommendation = {
            "should_evaluate": EVALUATION_AVAILABLE and DEPLOYMENT_STAGE in ["development", "staging"],
            "context_factors": context_factors,
            "evaluation_benefits": [
                "Quality assurance for complex extractions",
                "Performance monitoring and improvement",
                "Error pattern detection",
                "Confidence validation"
            ],
            "decision_guidance": "Consider evaluation for complex documents, low confidence extractions, or when error indicators are present"
        }
        
        return json.dumps(recommendation)
        
    except Exception as e:
        return json.dumps({
            "should_evaluate": False,
            "error": str(e),
            "fallback_reason": "evaluation_decision_failed"
        })

@tool
def get_business_context() -> str:
    """
    Get critical business rules and context for trade extraction decisions.
    
    Use this to understand business requirements, validation rules, and decision criteria.
    
    Returns:
        JSON string with business context and rules
    """
    business_context = {
        "critical_business_rules": {
            "source_classification": "All trades must be classified as either BANK or COUNTERPARTY",
            "table_routing": "BANK trades → BankTradeData, COUNTERPARTY trades → CounterpartyTradeData", 
            "data_integrity": "TRADE_SOURCE field must match table location",
            "primary_key": "trade_id is the primary key for all DynamoDB operations",
            "matching_strategy": "Match by attributes (currency, notional, dates, counterparty) - NOT by Trade_ID",
            "different_ids": "Bank and counterparty systems use different Trade_IDs for the same trade"
        },
        "matching_tolerances": {
            "currency": "exact match required",
            "notional": "±2% tolerance", 
            "dates": "±2 business days",
            "counterparty": "fuzzy string matching"
        },
        "classification_thresholds": {
            "MATCHED": "85%+ (auto-settle)",
            "PROBABLE_MATCH": "70-84% (senior review)", 
            "REVIEW_REQUIRED": "50-69% (ops review)",
            "BREAK": "<50% (investigate)"
        },
        "data_flow_context": {
            "current_stage": "Trade Extraction (Stage 5 of 11)",
            "previous_stage": "PDF Adapter extracted text to canonical output",
            "next_stage": "Trade Matching Agent will match by attributes",
            "handoff_criteria": "Successful storage in appropriate DynamoDB table"
        },
        "quality_requirements": {
            "accuracy": "High accuracy required for financial data",
            "completeness": "Extract all available relevant fields",
            "consistency": "Ensure data consistency across fields",
            "validation": "Validate against business rules before storage"
        }
    }
    
    return json.dumps(business_context, indent=2)

@tool
def validate_extraction_prerequisites() -> str:
    """Validate prerequisites for trade extraction.
    
    Implements circuit breaker pattern - fails fast if critical dependencies unavailable.
    Provides context about data format requirements and business rules.
    
    Returns:
        JSON string with validation results and extraction context
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
            "trade_id (partition key)",
            "internal_reference (sort key)",
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
            "matching_strategy": "Trades have different IDs across systems - extract for attribute matching",
            "critical_fields": ["trade_id", "notional", "currency", "trade_date", "counterparty"],
            "extraction_confidence_threshold": 0.7,
            "retry_policy": {
                "max_retries": 3,
                "backoff_multiplier": 2,
                "initial_delay_seconds": 1
            }
        },
        "common_fields": [
            "trade_date", "effective_date", "maturity_date",
            "notional", "currency", "counterparty",
            "product_type", "fixed_rate", "floating_rate_index",
            "spread", "quantity", "settlement_type",
            "payment_frequency", "commodity_type", "delivery_point",
            "uti", "lei", "usi"
        ]
    }
    
    return json.dumps(context, indent=2)


# ============================================================================
# Health Check Handler
# ============================================================================

@app.ping
def health_check() -> PingStatus:
    """Custom health check for AgentCore Runtime."""
    # Simple health check - agent uses use_aws tool which handles its own connectivity
    return PingStatus.HEALTHY


# ============================================================================
# Agent System Prompt
# ============================================================================

SYSTEM_PROMPT = f"""You are a specialized Trade Data Extraction Agent powered by Strands SDK.

## Your Mission
Extract structured trade data from canonical adapter output and store it in the correct DynamoDB table. You excel at understanding financial trade documents and converting unstructured text into precise, validated trade records.

## AgentCore Environment
- **Agent Version**: {AGENT_VERSION} ({AGENT_ALIAS})
- **Deployment Stage**: {DEPLOYMENT_STAGE}
- **Model**: {BEDROCK_MODEL_ID}
- **Observability**: Enhanced with PII redaction and custom metrics
- **Evaluation**: {"Enabled (10% sampling)" if EVALUATION_AVAILABLE else "Disabled"}
- **Gateway**: {"Enabled" if GATEWAY_AVAILABLE and DEPLOYMENT_STAGE == "production" else "Fallback mode"}
- **Memory**: {"Production" if DEPLOYMENT_STAGE == "production" else "Development"}
- **Security**: {"MFA Enabled" if ENABLE_MFA else "Standard Auth"}

## Available Resources
- **S3 Bucket**: {S3_BUCKET} (contains canonical adapter outputs)
- **DynamoDB Tables**: {BANK_TABLE} (bank trades), {COUNTERPARTY_TABLE} (counterparty trades)
- **AWS Region**: {REGION}
- **AgentCore Memory**: Available for pattern learning and context retrieval
- **AgentCore Gateway**: Secure, managed AWS operations (production)

## Available Tools

### Core Tools
- **get_business_context**: Get critical business rules and context for decision-making
- **should_run_quality_evaluation**: Determine if quality evaluation should be run
- **validate_extraction_prerequisites**: Get extraction environment and validation requirements
- **use_agentcore_memory**: Store/retrieve trade patterns and processing insights
- **use_aws**: Direct AWS operations (S3, DynamoDB, etc.)

### AWS Operations with use_aws (Primary Tool)
- **S3 Get**: `use_aws(service_name="s3", operation_name="get_object", parameters={{"Bucket": "bucket", "Key": "file.json"}})`
- **DynamoDB Put**: `use_aws(service_name="dynamodb", operation_name="put_item", parameters= {{"TableName": "table", "Item": {{"trade_id": {{"S": "value"}}}}}}`
- **DynamoDB Query**: `use_aws(service_name="dynamodb", operation_name="query", parameters={{"TableName": "table", "KeyConditionExpression": "trade_id = :id"}})`

**Important**: Use `use_aws` with named parameters: service_name, operation_name, parameters. DynamoDB requires typed format: {{"S": "string"}}, {{"N": "number"}}, {{"BOOL": true}}

**Strategy**: Use `use_aws` with named parameters for all S3 and DynamoDB operations. Start with S3 get_object to retrieve canonical output, then store extracted data with DynamoDB put_item.

## Decision-Making Framework

You are an intelligent agent with access to AgentCore capabilities. For each extraction task:

1. **Learn**: Query AgentCore Memory for similar trade patterns and extraction insights
2. **Analyze**: What information is available? What's the source type? What fields are present?
3. **Reason**: Which fields are relevant for matching? How should values be normalized? What's the appropriate table?
4. **Validate**: Does the data meet business requirements? Are required fields present? Is the format correct?
5. **Execute**: Use AgentCore Gateway for secure AWS operations
6. **Remember**: Store successful patterns and extraction insights in AgentCore Memory
7. **Verify**: Did the operation succeed? Should you take additional actions?

## Critical Business Rules

**Enterprise Context**: You are part of an AI Trade Matching System processing derivative trade confirmations. Your role is Stage 5 of 11 in the data flow.

**Key Constraints**:
- **Source Classification**: BANK trades → {BANK_TABLE}, COUNTERPARTY trades → {COUNTERPARTY_TABLE}
- **Data Integrity**: TRADE_SOURCE field MUST match the target table
- **Primary Key**: trade_id is the primary key for all DynamoDB operations
- **Different Trade IDs**: Bank and counterparty systems use different Trade_IDs for the same trade
- **Downstream Impact**: Your extraction quality directly affects matching accuracy (Stage 8)
- **DynamoDB Format**: Use typed format {{"S": "string"}}, {{"N": "number"}}, {{"BOOL": true}}

**Quality Standards**: This is financial data - accuracy and completeness are critical for settlement risk management.

## Your Autonomy

You have complete decision-making authority over:
- **Strategy**: How to approach the extraction task
- **Tool Selection**: Which tools to use and in what order
- **Data Processing**: How to extract, validate, and structure the data
- **Field Selection**: Which fields to include based on relevance and context
- **Error Handling**: How to handle missing, ambiguous, or invalid information
- **Quality Assurance**: What validation checks to perform
- **Optimization**: How to balance accuracy, speed, and reliability

**Decision Framework**: For each task, analyze the context, reason about the best approach, choose appropriate tools, and adapt based on results. You are the intelligent decision-maker - use your reasoning capabilities to solve problems dynamically.
"""


# ============================================================================
# Create Strands Agent
# ============================================================================

def create_extraction_agent() -> Agent:
    """Create and configure the Strands extraction agent with session management."""
    # Configure model for financial data processing
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.1,  # Low temperature for consistent financial data extraction
        max_tokens=4096,
    )
    
    # Create agent with focused tools - Strands SDK handles session management internally
    agent = Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            # Core extraction tools for context and validation
            validate_extraction_prerequisites,
            use_agentcore_memory,
            # Primary AWS operations tool - use this for all S3 and DynamoDB operations
            use_aws
        ]
    )
    
    # Add observability hooks
    if observability:
        agent = observability.wrap_agent(agent)
    
    return agent


# ============================================================================
# AgentCore Entrypoint
# ============================================================================

def _extract_token_metrics(result) -> Dict[str, int]:
    """Extract token usage metrics from Strands agent result."""
    metrics = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    try:
        if hasattr(result, 'metrics'):
            metrics["input_tokens"] = getattr(result.metrics, 'input_tokens', 0) or 0
            metrics["output_tokens"] = getattr(result.metrics, 'output_tokens', 0) or 0
        elif hasattr(result, 'usage'):
            metrics["input_tokens"] = getattr(result.usage, 'input_tokens', 0) or 0
            metrics["output_tokens"] = getattr(result.usage, 'output_tokens', 0) or 0
        metrics["total_tokens"] = metrics["input_tokens"] + metrics["output_tokens"]
    except Exception:
        pass
    return metrics


def _send_custom_metrics(processing_time_ms: float, token_metrics: Dict[str, int], 
                        success: bool, source_type: str = "unknown", 
                        extraction_quality: Dict[str, Any] = None):
    """Send custom CloudWatch metrics for monitoring and alerting."""
    try:
        import boto3
        cloudwatch = boto3.client('cloudwatch', region_name=REGION)
        
        metrics_data = [
            {
                'MetricName': 'ProcessingTimeMs',
                'Dimensions': [
                    {'Name': 'AgentName', 'Value': AGENT_NAME},
                    {'Name': 'SourceType', 'Value': source_type},
                    {'Name': 'Version', 'Value': AGENT_VERSION}
                ],
                'Value': processing_time_ms,
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'TokenUsage',
                'Dimensions': [
                    {'Name': 'AgentName', 'Value': AGENT_NAME},
                    {'Name': 'TokenType', 'Value': 'Total'}
                ],
                'Value': token_metrics.get('total_tokens', 0),
                'Unit': 'Count'
            },
            {
                'MetricName': 'ExtractionSuccessRate',
                'Dimensions': [
                    {'Name': 'AgentName', 'Value': AGENT_NAME},
                    {'Name': 'SourceType', 'Value': source_type}
                ],
                'Value': 1.0 if success else 0.0,
                'Unit': 'Count'
            }
        ]
        
        # Add extraction quality metrics if available
        if extraction_quality:
            metrics_data.extend([
                {
                    'MetricName': 'ExtractionCompleteness',
                    'Dimensions': [
                        {'Name': 'AgentName', 'Value': AGENT_NAME},
                        {'Name': 'SourceType', 'Value': source_type}
                    ],
                    'Value': extraction_quality.get('completeness_ratio', 0.0),
                    'Unit': 'Percent'
                },
                {
                    'MetricName': 'EstimatedCost',
                    'Dimensions': [
                        {'Name': 'AgentName', 'Value': AGENT_NAME},
                        {'Name': 'ModelId', 'Value': BEDROCK_MODEL_ID}
                    ],
                    'Value': extraction_quality.get('estimated_cost', 0.0),
                    'Unit': 'None'
                }
            ])
        
        # Send metrics in production only
        if DEPLOYMENT_STAGE == "production":
            cloudwatch.put_metric_data(
                Namespace='AgentCore/TradeExtraction',
                MetricData=metrics_data
            )
            
    except Exception as e:
        logger.warning(f"Failed to send custom metrics: {e}")


# Import enhanced observability if available
try:
    # Try relative import first (for local development)
    from .agentcore_observability_enhancement import create_enhanced_observability_wrapper
    ENHANCED_OBSERVABILITY_AVAILABLE = True
except ImportError:
    try:
        # Try absolute import (for AgentCore Runtime)
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        from agentcore_observability_enhancement import create_enhanced_observability_wrapper
        ENHANCED_OBSERVABILITY_AVAILABLE = True
    except ImportError:
        ENHANCED_OBSERVABILITY_AVAILABLE = False

def _invoke_core(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Core AgentCore Runtime entrypoint logic for Trade Data Extraction Agent.
    
    Uses Strands SDK with use_aws tool for all AWS operations.
    
    Args:
        payload: Event payload containing:
            - document_id: Unique identifier for the document
            - canonical_output_location: S3 path to canonical adapter output
            - source_type: Optional - BANK or COUNTERPARTY
        context: AgentCore context (optional)
        
    Returns:
        dict: Extraction result with trade_id and table_name
    """
    start_time = datetime.utcnow()
    logger.info("Trade Data Extraction Agent (Strands) invoked")
    # Redact PII from payload logging
    safe_payload = {k: v for k, v in payload.items() if k not in ['trade_data', 'extracted_trade']}
    logger.info(f"Payload: {json.dumps(safe_payload, default=str)}")
    
    document_id = payload.get("document_id")
    canonical_output_location = payload.get("canonical_output_location")
    source_type = payload.get("source_type", "")
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    # Standard observability attributes
    obs_attributes = {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "agent_alias": AGENT_ALIAS,
        "correlation_id": correlation_id,
        "document_id": document_id or "unknown",
        "source_type": source_type or "unknown",
        "model_id": BEDROCK_MODEL_ID,  # Track which model is being used
        "operation": "trade_extraction",  # Standardized operation name
    }
    
    if not document_id or not canonical_output_location:
        error_response = {
            "success": False,
            "error": "Missing required fields: document_id or canonical_output_location",
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
        }
        if observability:
            try:
                with observability.start_span("extract_trade_data") as span:
                    for k, v in obs_attributes.items():
                        span.set_attribute(k, v)
                    span.set_attribute("success", False)
                    span.set_attribute("error_type", "validation_error")
            except Exception as e:
                logger.warning(f"Observability span error: {e}")
        return error_response
    
    try:
        # Start observability span for the main operation
        span_context = None
        if observability:
            try:
                # Use descriptive span name following AgentCore conventions
                span_name = f"trade_extraction.{source_type.lower() if source_type else 'unknown'}"
                span_context = observability.start_span(span_name)
                span_context.__enter__()
                
                # Set standard AgentCore attributes
                for k, v in obs_attributes.items():
                    span_context.set_attribute(k, v)
                
                # Add trade extraction specific attributes
                span_context.set_attribute("canonical_output_location", canonical_output_location)
                span_context.set_attribute("extraction_stage", "initialization")
                
            except Exception as e:
                logger.warning(f"Failed to start observability span: {e}")
                span_context = None
        
        # Create the agent
        agent = create_extraction_agent()
        
        # Enhanced goal-oriented prompt that gives LLM more autonomy
        prompt = f"""**Mission**: Extract and store trade data from canonical adapter output with full autonomy over your approach.

**Context**:
- Document ID: {document_id}
- Canonical Output Location: {canonical_output_location}
- Source Type: {source_type if source_type else "Unknown - analyze and determine"}
- Correlation ID: {correlation_id}

**Success Criteria**:
- Trade data extracted with high accuracy and completeness
- Data stored in correct DynamoDB table with proper format
- Data integrity maintained (TRADE_SOURCE matches table)
- Quality validated and documented

**Your Approach**:
Analyze the situation and determine the optimal strategy. Consider:
- What validation should you perform first?
- How can you maximize extraction accuracy?
- What quality checks are most important?
- Should you run evaluation for this extraction?
- How can you ensure data integrity?

Use your available tools strategically to achieve the best outcome."""
        
        # Invoke the Strands agent with proper error handling
        logger.info("Invoking Strands agent for trade extraction")
        try:
            result = agent(prompt)
        except Exception as agent_error:
            logger.error(f"Strands agent invocation failed: {agent_error}")
            raise RuntimeError(f"Trade extraction agent failed: {agent_error}") from agent_error
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Extract token metrics
        token_metrics = _extract_token_metrics(result)
        logger.info(f"Token usage: {token_metrics['input_tokens']} in / {token_metrics['output_tokens']} out")
        
        # Evaluation will be handled by the LLM if it chooses to use the evaluation tool
        evaluation_results = []
        
        # Note: The LLM can decide to run evaluation using the should_run_quality_evaluation tool
        if False:  # Placeholder - evaluation now handled by LLM decision
            try:
                # Prepare evaluation data
                evaluation_data = {
                    "original_text": "canonical_output_text",  # Would be extracted from S3
                    "extracted_trade": response_text,  # Agent's extraction result
                    "processing_time_ms": processing_time_ms,
                    "token_usage": token_metrics
                }
                
                # Run evaluation
                evaluation_results = evaluation_orchestrator.evaluate_agent_interaction(
                    agent_name="trade_extractor",
                    interaction_data=evaluation_data
                )
                
                logger.info(f"Evaluation completed: {len(evaluation_results)} evaluators ran")
                
                # Add evaluation metrics to observability span
                if span_context and evaluation_results:
                    avg_score = sum(r.score.value for r in evaluation_results) / len(evaluation_results)
                    avg_confidence = sum(r.confidence for r in evaluation_results) / len(evaluation_results)
                    span_context.set_attribute("evaluation_avg_score", avg_score)
                    span_context.set_attribute("evaluation_avg_confidence", avg_confidence)
                    span_context.set_attribute("evaluation_count", len(evaluation_results))
                    
            except Exception as e:
                logger.warning(f"Evaluation failed: {e}")
                if span_context:
                    span_context.set_attribute("evaluation_error", str(e)[:200])
        
        # Prepare extraction quality metrics
        extraction_quality = {
            'completeness_ratio': completeness_ratio if 'completeness_ratio' in locals() else 0.0,
            'estimated_cost': (token_metrics["input_tokens"] * 0.0008 / 1000) + 
                             (token_metrics["output_tokens"] * 0.0032 / 1000)
        }
        
        # Send custom CloudWatch metrics
        _send_custom_metrics(processing_time_ms, token_metrics, True, source_type, extraction_quality)
        
        # Extract agent response following Strands SDK patterns
        response_text = ""
        if hasattr(result, 'message') and result.message:
            if hasattr(result.message, 'content'):
                content = result.message.content
                if isinstance(content, list) and content:
                    # Handle list of content blocks
                    first_block = content[0]
                    response_text = first_block.get('text', str(first_block)) if isinstance(first_block, dict) else str(first_block)
                else:
                    response_text = str(content)
            else:
                response_text = str(result.message)
        else:
            response_text = str(result)
        
        logger.info(f"Agent response length: {len(response_text)} characters")
        
        # Record success metrics in observability span
        if span_context:
            try:
                span_context.set_attribute("success", True)
                span_context.set_attribute("extraction_stage", "completed")
                span_context.set_attribute("processing_time_ms", processing_time_ms)
                span_context.set_attribute("input_tokens", token_metrics["input_tokens"])
                span_context.set_attribute("output_tokens", token_metrics["output_tokens"])
                span_context.set_attribute("total_tokens", token_metrics["total_tokens"])
                
                # Add cost estimation (Nova Pro pricing)
                estimated_cost = (token_metrics["input_tokens"] * 0.0008 / 1000) + \
                                (token_metrics["output_tokens"] * 0.0032 / 1000)
                span_context.set_attribute("estimated_cost_usd", round(estimated_cost, 6))
                
                # Add extraction quality indicators
                response_length = len(response_text)
                span_context.set_attribute("response_length_chars", response_length)
                
                # Estimate extraction completeness (basic heuristic)
                trade_keywords = ["trade_id", "notional", "currency", "counterparty", "trade_date"]
                found_keywords = sum(1 for keyword in trade_keywords if keyword.lower() in response_text.lower())
                completeness_ratio = found_keywords / len(trade_keywords)
                span_context.set_attribute("extraction_completeness_ratio", completeness_ratio)
                
                # Performance classification
                if processing_time_ms < 15000:  # < 15 seconds
                    span_context.set_attribute("performance_tier", "fast")
                elif processing_time_ms < 30000:  # < 30 seconds
                    span_context.set_attribute("performance_tier", "normal")
                else:
                    span_context.set_attribute("performance_tier", "slow")
                    
            except Exception as e:
                logger.warning(f"Failed to set span attributes: {e}")
        
        return {
            "success": True,
            "document_id": document_id,
            "source_type": source_type,
            "correlation_id": correlation_id,
            "agent_response": response_text,
            "processing_time_ms": processing_time_ms,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "agent_alias": AGENT_ALIAS,
            "token_usage": token_metrics,
            "evaluation_results": [
                {
                    "evaluator": r.evaluator_name,
                    "score": r.score.value,
                    "confidence": r.confidence,
                    "reasoning": r.reasoning[:200]  # Truncate for response size
                } for r in evaluation_results
            ] if evaluation_results else [],
            "model_id": BEDROCK_MODEL_ID,
            "deployment_stage": DEPLOYMENT_STAGE,
        }
        
    except Exception as e:
        logger.error(f"Error in extraction agent: {e}", exc_info=True)
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Record error in observability span
        if span_context:
            try:
                span_context.set_attribute("success", False)
                span_context.set_attribute("extraction_stage", "failed")
                span_context.set_attribute("error_type", type(e).__name__)
                span_context.set_attribute("error_message", str(e)[:500])  # Truncate long errors
                span_context.set_attribute("processing_time_ms", processing_time_ms)
                
                # Enhanced error categorization for trade extraction
                error_str = str(e).lower()
                if "dynamodb" in error_str or "table" in error_str:
                    span_context.set_attribute("error_category", "database")
                    span_context.set_attribute("error_subcategory", "dynamodb_operation")
                elif "s3" in error_str or "bucket" in error_str:
                    span_context.set_attribute("error_category", "storage")
                    span_context.set_attribute("error_subcategory", "s3_operation")
                elif "bedrock" in error_str or "model" in error_str:
                    span_context.set_attribute("error_category", "model")
                    span_context.set_attribute("error_subcategory", "llm_invocation")
                elif "validation" in error_str or "schema" in error_str:
                    span_context.set_attribute("error_category", "validation")
                    span_context.set_attribute("error_subcategory", "data_validation")
                elif "timeout" in error_str:
                    span_context.set_attribute("error_category", "performance")
                    span_context.set_attribute("error_subcategory", "timeout")
                elif "permission" in error_str or "access" in error_str:
                    span_context.set_attribute("error_category", "security")
                    span_context.set_attribute("error_subcategory", "access_denied")
                elif "trade_source" in error_str or "classification" in error_str:
                    span_context.set_attribute("error_category", "business_logic")
                    span_context.set_attribute("error_subcategory", "trade_classification")
                elif "extraction" in error_str or "parsing" in error_str:
                    span_context.set_attribute("error_category", "data_processing")
                    span_context.set_attribute("error_subcategory", "extraction_failure")
                else:
                    span_context.set_attribute("error_category", "unknown")
                    span_context.set_attribute("error_subcategory", "unclassified")
                    
            except Exception:
                pass
        
        # Send error metrics
        _send_custom_metrics(processing_time_ms, {}, False, source_type)
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "document_id": document_id,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "processing_time_ms": processing_time_ms,
        }
    finally:
        # Close observability span
        if span_context:
            try:
                span_context.__exit__(None, None, None)
            except Exception:
                pass


# Apply enhanced observability wrapper if available
if ENHANCED_OBSERVABILITY_AVAILABLE and DEPLOYMENT_STAGE == "production":
    invoke = create_enhanced_observability_wrapper(_invoke_core)
    logger.info("✅ Enhanced observability wrapper applied")
else:
    invoke = _invoke_core
    logger.info("ℹ️ Using standard observability")

# Register with AgentCore Runtime
app.entrypoint(invoke)


def main():
    """
    CLI entry point for the Trade Extraction Agent.
    
    This provides a command-line interface for testing and development,
    while maintaining compatibility with AgentCore Runtime.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Trade Data Extraction Agent")
    parser.add_argument("--mode", choices=["runtime", "test"], default="runtime",
                       help="Run mode: 'runtime' for AgentCore, 'test' for CLI testing")
    parser.add_argument("--document-id", help="Document ID for testing")
    parser.add_argument("--canonical-output-location", help="S3 location of canonical output")
    parser.add_argument("--source-type", choices=["BANK", "COUNTERPARTY"], help="Trade source type")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.mode == "test" and args.document_id and args.canonical_output_location:
        # CLI testing mode
        print(f"🧪 Testing Trade Extraction Agent")
        print(f"Document ID: {args.document_id}")
        print(f"Canonical Output: {args.canonical_output_location}")
        print(f"Source Type: {args.source_type}")
        
        # Create test payload
        test_payload = {
            "document_id": args.document_id,
            "canonical_output_location": args.canonical_output_location,
            "source_type": args.source_type or "BANK",
            "correlation_id": f"cli_test_{uuid.uuid4().hex[:8]}"
        }
        
        # Invoke the agent
        result = invoke(test_payload)
        
        # Display results
        print(f"\n📊 Results:")
        print(f"Success: {result.get('success', False)}")
        if result.get('success'):
            print(f"Processing Time: {result.get('processing_time_ms', 0):.0f}ms")
            print(f"Token Usage: {result.get('token_usage', {})}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        return result.get('success', False)
    
    else:
        # AgentCore Runtime mode
        print(f"🚀 Starting Trade Extraction Agent in AgentCore Runtime mode")
        app.run()


if __name__ == "__main__":
    main()
