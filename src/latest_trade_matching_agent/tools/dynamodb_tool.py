"""
DynamoDB Operations Tool
Provides put_item and scan operations for DynamoDB tables
"""

import boto3
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DynamoDBTool:
    """
    DynamoDB operations tool for storing and retrieving trade data.
    Supports both BankTradeData and CounterpartyTradeData tables.
    """
    
    def __init__(self, region_name: str = "me-central-1"):
        self.region_name = region_name
        self.name = "DynamoDB Operations Tool"
        self.description = (
            "Performs DynamoDB operations including put_item and scan. "
            "Use this tool to store trade data in DynamoDB tables or retrieve all items from a table. "
            "Supports both BankTradeData and CounterpartyTradeData tables."
        )
        logger.info(f"DynamoDB client initialized for region: {region_name}")

    def _get_dynamodb_client(self):
        """Get or create DynamoDB client"""
        return boto3.client('dynamodb', region_name=self.region_name)

    def run(
        self,
        operation: str,
        table_name: str,
        item: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Execute a DynamoDB operation.

        Args:
            operation: The operation to perform ('put_item' or 'scan')
            table_name: The name of the DynamoDB table
            item: For put_item operation, the item to store (must be in DynamoDB typed format)

        Returns:
            JSON string with operation result
        """
        try:
            dynamodb = self._get_dynamodb_client()

            if operation == "put_item":
                if not item:
                    return json.dumps({"error": "item parameter required for put_item operation"})

                logger.info(f"Putting item in table {table_name}: {item.get('Trade_ID', {}).get('S', 'unknown')}")
                response = dynamodb.put_item(
                    TableName=table_name,
                    Item=item
                )
                return json.dumps({
                    "success": True,
                    "message": f"Item successfully stored in {table_name}",
                    "trade_id": item.get("Trade_ID", {}).get("S", "unknown")
                })

            elif operation == "scan":
                logger.info(f"Scanning table {table_name}")
                response = dynamodb.scan(TableName=table_name)

                # Convert DynamoDB typed format to simplified format
                items = response.get('Items', [])
                simplified_items = []

                for item in items:
                    simplified = {}
                    for key, value_dict in item.items():
                        # Extract the actual value from DynamoDB typed format
                        if 'S' in value_dict:
                            simplified[key] = value_dict['S']
                        elif 'N' in value_dict:
                            simplified[key] = value_dict['N']
                        elif 'M' in value_dict:
                            simplified[key] = value_dict['M']
                        elif 'L' in value_dict:
                            simplified[key] = value_dict['L']
                        else:
                            simplified[key] = value_dict
                    simplified_items.append(simplified)

                return json.dumps({
                    "success": True,
                    "count": len(simplified_items),
                    "items": simplified_items
                }, indent=2)

            else:
                return json.dumps({"error": f"Unsupported operation: {operation}. Use 'put_item' or 'scan'."})

        except Exception as e:
            logger.error(f"DynamoDB operation failed: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
