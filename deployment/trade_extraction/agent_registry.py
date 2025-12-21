"""
Agent Registry Integration for Trade Extraction Agent.

This module implements DynamoDB AgentRegistry table integration
for registering and managing agent metadata.
"""

import os
import boto3
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from botocore.exceptions import ClientError

try:
    from data_models import AgentRegistryEntry
except ImportError:
    # For testing, create a minimal AgentRegistryEntry class
    from dataclasses import dataclass
    from typing import List, Optional
    
    @dataclass
    class AgentRegistryEntry:
        agent_id: str
        agent_name: str
        agent_type: str
        runtime_arn: str
        status: str
        version: str
        capabilities: List[str]
        created_at: str
        updated_at: str
        sop_enabled: bool
        sop_version: Optional[str]
        
        def to_dict(self):
            return {
                'agent_id': self.agent_id,
                'agent_name': self.agent_name,
                'agent_type': self.agent_type,
                'runtime_arn': self.runtime_arn,
                'status': self.status,
                'version': self.version,
                'capabilities': self.capabilities,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'sop_enabled': self.sop_enabled,
                'sop_version': self.sop_version
            }
        
        @classmethod
        def from_dict(cls, data):
            return cls(**data)

logger = logging.getLogger(__name__)


class AgentRegistryManager:
    """
    Manages agent registration in DynamoDB AgentRegistry table.
    
    This class handles registration, updates, and queries for agent
    metadata in the centralized agent registry.
    """
    
    def __init__(self, region_name: str = None, table_name: str = None):
        """
        Initialize the AgentRegistryManager.
        
        Args:
            region_name: AWS region name (defaults to environment or us-east-1)
            table_name: DynamoDB table name (defaults to environment or AgentRegistry)
        """
        self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-1')
        self.table_name = table_name or os.getenv('AGENT_REGISTRY_TABLE', 'AgentRegistry')
        
        # Initialize DynamoDB client
        self.dynamodb = boto3.client('dynamodb', region_name=self.region_name)
        
        logger.info(f"AgentRegistryManager initialized for table {self.table_name} in {self.region_name}")
    
    def register_trade_extraction_agent(
        self,
        runtime_arn: str,
        version: str = "1.0.0",
        status: str = "active"
    ) -> Tuple[bool, Optional[str]]:
        """
        Register the Trade Extraction Agent in the registry.
        
        Args:
            runtime_arn: AgentCore runtime ARN
            version: Agent version (semantic versioning)
            status: Agent status (active, inactive, maintenance)
            
        Returns:
            Tuple of (success, error_message)
        """
        agent_id = "trade-extraction-agent"
        current_time = datetime.now(timezone.utc).isoformat()
        
        agent_entry = AgentRegistryEntry(
            agent_id=agent_id,
            agent_name="Trade Extraction Agent",
            agent_type="extraction",
            runtime_arn=runtime_arn,
            status=status,
            version=version,
            capabilities=[
                "pdf_processing",
                "trade_data_extraction",
                "data_validation",
                "table_routing",
                "sop_workflow"
            ],
            created_at=current_time,
            updated_at=current_time,
            sop_enabled=True,
            sop_version="1.0.0"
        )
        
        try:
            # Convert to DynamoDB format
            item = self._to_dynamodb_item(agent_entry.to_dict())
            
            # Use put_item with condition to prevent overwrites of existing active agents
            response = self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item,
                ConditionExpression='attribute_not_exists(agent_id) OR #status <> :active_status',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':active_status': {'S': 'active'}
                }
            )
            
            logger.info(f"Successfully registered agent {agent_id} with version {version}")
            return True, None
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                # Agent already exists and is active, update instead
                return self._update_existing_agent(agent_entry)
            else:
                error_msg = f"Failed to register agent: {e.response['Error']['Message']}"
                logger.error(error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during agent registration: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def update_agent_status(
        self,
        agent_id: str,
        status: str,
        version: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Update agent status and optionally version.
        
        Args:
            agent_id: Agent identifier
            status: New status (active, inactive, maintenance)
            version: Optional new version
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            update_expression = "SET #status = :status, updated_at = :updated_at"
            expression_attribute_names = {'#status': 'status'}
            expression_attribute_values = {
                ':status': {'S': status},
                ':updated_at': {'S': datetime.now(timezone.utc).isoformat()}
            }
            
            if version:
                update_expression += ", version = :version"
                expression_attribute_values[':version'] = {'S': version}
            
            response = self.dynamodb.update_item(
                TableName=self.table_name,
                Key={'agent_id': {'S': agent_id}},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ConditionExpression='attribute_exists(agent_id)'
            )
            
            logger.info(f"Successfully updated agent {agent_id} status to {status}")
            return True, None
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                error_msg = f"Agent {agent_id} not found in registry"
            else:
                error_msg = f"Failed to update agent status: {e.response['Error']['Message']}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during status update: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_agent_info(self, agent_id: str) -> Tuple[bool, Optional[AgentRegistryEntry], Optional[str]]:
        """
        Retrieve agent information from registry.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Tuple of (success, agent_entry, error_message)
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={'agent_id': {'S': agent_id}}
            )
            
            if 'Item' not in response:
                return False, None, f"Agent {agent_id} not found in registry"
            
            # Convert from DynamoDB format
            item_dict = self._from_dynamodb_item(response['Item'])
            agent_entry = AgentRegistryEntry.from_dict(item_dict)
            
            logger.info(f"Successfully retrieved agent {agent_id} from registry")
            return True, agent_entry, None
            
        except Exception as e:
            error_msg = f"Failed to retrieve agent info: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def list_agents_by_type(self, agent_type: str) -> Tuple[bool, List[AgentRegistryEntry], Optional[str]]:
        """
        List all agents of a specific type.
        
        Args:
            agent_type: Agent type to filter by
            
        Returns:
            Tuple of (success, agent_list, error_message)
        """
        try:
            # Use scan with filter (could be optimized with GSI in production)
            response = self.dynamodb.scan(
                TableName=self.table_name,
                FilterExpression='agent_type = :agent_type',
                ExpressionAttributeValues={
                    ':agent_type': {'S': agent_type}
                }
            )
            
            agents = []
            for item in response.get('Items', []):
                item_dict = self._from_dynamodb_item(item)
                agents.append(AgentRegistryEntry.from_dict(item_dict))
            
            logger.info(f"Found {len(agents)} agents of type {agent_type}")
            return True, agents, None
            
        except Exception as e:
            error_msg = f"Failed to list agents by type: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg
    
    def _update_existing_agent(self, agent_entry: AgentRegistryEntry) -> Tuple[bool, Optional[str]]:
        """Update an existing agent entry."""
        try:
            # Update with new version and timestamp
            agent_entry.updated_at = datetime.now(timezone.utc).isoformat()
            
            update_expression = """
                SET agent_name = :agent_name,
                    agent_type = :agent_type,
                    runtime_arn = :runtime_arn,
                    #status = :status,
                    version = :version,
                    capabilities = :capabilities,
                    updated_at = :updated_at,
                    sop_enabled = :sop_enabled,
                    sop_version = :sop_version
            """
            
            item_dict = agent_entry.to_dict()
            expression_attribute_values = {
                ':agent_name': {'S': item_dict['agent_name']},
                ':agent_type': {'S': item_dict['agent_type']},
                ':runtime_arn': {'S': item_dict['runtime_arn']},
                ':status': {'S': item_dict['status']},
                ':version': {'S': item_dict['version']},
                ':capabilities': {'SS': item_dict['capabilities']},
                ':updated_at': {'S': item_dict['updated_at']},
                ':sop_enabled': {'BOOL': item_dict['sop_enabled']},
                ':sop_version': {'S': item_dict['sop_version']} if item_dict['sop_version'] else {'NULL': True}
            }
            
            response = self.dynamodb.update_item(
                TableName=self.table_name,
                Key={'agent_id': {'S': agent_entry.agent_id}},
                UpdateExpression=update_expression,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues=expression_attribute_values
            )
            
            logger.info(f"Successfully updated existing agent {agent_entry.agent_id}")
            return True, None
            
        except Exception as e:
            error_msg = f"Failed to update existing agent: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _to_dynamodb_item(self, item_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Convert dictionary to DynamoDB item format."""
        dynamodb_item = {}
        
        for key, value in item_dict.items():
            if value is None:
                dynamodb_item[key] = {'NULL': True}
            elif isinstance(value, str):
                dynamodb_item[key] = {'S': value}
            elif isinstance(value, bool):
                dynamodb_item[key] = {'BOOL': value}
            elif isinstance(value, (int, float)):
                dynamodb_item[key] = {'N': str(value)}
            elif isinstance(value, list):
                if all(isinstance(item, str) for item in value):
                    dynamodb_item[key] = {'SS': value}
                else:
                    # Convert to string list
                    dynamodb_item[key] = {'SS': [str(item) for item in value]}
            else:
                dynamodb_item[key] = {'S': str(value)}
        
        return dynamodb_item
    
    def _from_dynamodb_item(self, dynamodb_item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DynamoDB item to regular dictionary."""
        item_dict = {}
        
        for key, value in dynamodb_item.items():
            if 'NULL' in value:
                item_dict[key] = None
            elif 'S' in value:
                item_dict[key] = value['S']
            elif 'BOOL' in value:
                item_dict[key] = value['BOOL']
            elif 'N' in value:
                # Try to convert to int first, then float
                try:
                    item_dict[key] = int(value['N'])
                except ValueError:
                    item_dict[key] = float(value['N'])
            elif 'SS' in value:
                item_dict[key] = value['SS']
            else:
                # Fallback for other types
                item_dict[key] = str(value)
        
        return item_dict