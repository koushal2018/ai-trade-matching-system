"""
AgentCore Gateway Integration Example for Trade Extraction Agent

This shows how to replace direct boto3 calls with AgentCore Gateway for:
- Enhanced security and authentication
- Built-in monitoring and observability
- Managed connection pooling
- Automatic retry logic
"""

from bedrock_agentcore import Gateway
import json
from typing import Dict, Any

class AgentCoreGatewayIntegration:
    """Integration layer for AgentCore Gateway services."""
    
    def __init__(self):
        # Initialize gateways for different services
        self.dynamodb_gateway = Gateway(
            name="trade-matching-system-dynamodb-gateway-production"
        )
        self.s3_gateway = Gateway(
            name="trade-matching-system-s3-gateway-production"
        )
    
    def store_trade_data(self, table_name: str, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store trade data using AgentCore Gateway instead of direct boto3.
        
        Benefits:
        - Managed authentication and authorization
        - Built-in retry logic and error handling
        - Centralized monitoring and logging
        - Policy enforcement at the gateway level
        """
        try:
            # Use gateway instead of direct boto3 call
            result = self.dynamodb_gateway.invoke_tool(
                tool_name="PutItem",
                parameters={
                    "TableName": table_name,
                    "Item": trade_data
                }
            )
            
            return {
                "success": True,
                "result": result,
                "gateway_used": "dynamodb"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "gateway_used": "dynamodb"
            }
    
    def get_canonical_output(self, s3_key: str) -> Dict[str, Any]:
        """
        Retrieve canonical output using AgentCore Gateway.
        
        Benefits:
        - Secure access with managed credentials
        - Built-in caching and optimization
        - Automatic error handling and retries
        """
        try:
            result = self.s3_gateway.invoke_tool(
                tool_name="GetObject",
                parameters={
                    "Bucket": "trade-matching-system-agentcore-production",
                    "Key": s3_key
                }
            )
            
            return {
                "success": True,
                "content": result.get("Body", ""),
                "gateway_used": "s3"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "gateway_used": "s3"
            }

# Integration with your existing agent tools
@tool
def use_dynamodb_gateway_enhanced(operation: str, parameters: dict, label: str = "") -> str:
    """
    Enhanced DynamoDB operations using AgentCore Gateway.
    
    This replaces your current use_dynamodb_gateway tool with full AgentCore integration.
    """
    gateway_integration = AgentCoreGatewayIntegration()
    
    if operation == "PutItem":
        result = gateway_integration.store_trade_data(
            table_name=parameters.get("TableName"),
            trade_data=parameters.get("Item", {})
        )
    else:
        # Handle other operations
        result = gateway_integration.dynamodb_gateway.invoke_tool(
            tool_name=operation,
            parameters=parameters
        )
    
    return json.dumps(result, default=str)