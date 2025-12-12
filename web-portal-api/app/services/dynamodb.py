import boto3
from typing import Optional, Any
from ..config import settings


class DynamoDBService:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self.client = boto3.client("dynamodb", region_name=settings.aws_region)
    
    def get_table(self, table_name: str):
        return self.dynamodb.Table(table_name)
    
    def scan_table(self, table_name: str, filter_expression: Optional[Any] = None, 
                   limit: int = 100) -> list[dict]:
        table = self.get_table(table_name)
        params = {"Limit": limit}
        if filter_expression:
            params["FilterExpression"] = filter_expression
        response = table.scan(**params)
        return response.get("Items", [])
    
    def get_item(self, table_name: str, key: dict) -> Optional[dict]:
        table = self.get_table(table_name)
        response = table.get_item(Key=key)
        return response.get("Item")
    
    def put_item(self, table_name: str, item: dict) -> dict:
        table = self.get_table(table_name)
        return table.put_item(Item=item)
    
    def update_item(self, table_name: str, key: dict, update_expression: str,
                    expression_values: dict) -> dict:
        table = self.get_table(table_name)
        return table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )
    
    def query_with_pagination(self, table_name: str, page: int, page_size: int,
                              filter_expression: Optional[Any] = None) -> tuple[list[dict], int]:
        table = self.get_table(table_name)
        
        # Get total count
        scan_params = {}
        if filter_expression:
            scan_params["FilterExpression"] = filter_expression
        count_response = table.scan(Select="COUNT", **scan_params)
        total = count_response.get("Count", 0)
        
        # Get paginated items
        items = []
        scan_params["Limit"] = page_size
        response = table.scan(**scan_params)
        
        # Skip to the right page
        for _ in range(page):
            if "LastEvaluatedKey" not in response:
                break
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"], **scan_params)
        
        items = response.get("Items", [])
        return items, total


db_service = DynamoDBService()
