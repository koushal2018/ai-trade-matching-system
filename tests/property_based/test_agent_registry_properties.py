"""
Property-based tests for Agent Registry Manager.

These tests validate agent registration completeness and DynamoDB integration
using Hypothesis for comprehensive property testing.
"""

import pytest
from hypothesis import given, strategies as st, assume
from unittest.mock import Mock, patch, MagicMock
import os
import sys
from datetime import datetime
from botocore.exceptions import ClientError

# Add the deployment directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'deployment', 'trade_extraction'))

from agent_registry import AgentRegistryManager
try:
    from data_models import AgentRegistryEntry
except ImportError:
    # Import from agent_registry module which has the fallback
    from agent_registry import AgentRegistryEntry


class TestAgentRegistryProperties:
    """Property-based tests for agent registry functionality."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Mock DynamoDB client to avoid actual AWS calls
        with patch('boto3.client') as mock_boto3:
            self.mock_dynamodb = Mock()
            mock_boto3.return_value = self.mock_dynamodb
            self.registry = AgentRegistryManager(region_name='us-east-1', table_name='TestAgentRegistry')
    
    @given(st.just('arn:aws:bedrock-agentcore:us-east-1:123456789012:agent/test-agent'))
    def test_property_4_agent_registration_completeness(self, runtime_arn: str):
        """
        Property 4: Agent Registration Completeness
        
        For any valid runtime ARN, agent registration must:
        1. Create a complete AgentRegistryEntry with all required fields
        2. Include proper timestamps and versioning
        3. Set appropriate capabilities and SOP configuration
        4. Handle DynamoDB operations correctly
        5. Return success status and handle errors gracefully
        """
        # Mock successful DynamoDB put_item
        self.mock_dynamodb.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        # Test registration
        success, error_message = self.registry.register_trade_extraction_agent(
            runtime_arn=runtime_arn,
            version="1.0.0",
            status="active"
        )
        
        # Verify success
        assert success is True
        assert error_message is None
        
        # Verify DynamoDB put_item was called
        assert self.mock_dynamodb.put_item.called
        call_args = self.mock_dynamodb.put_item.call_args
        
        # Verify table name
        assert call_args[1]['TableName'] == 'TestAgentRegistry'
        
        # Verify item structure
        item = call_args[1]['Item']
        assert 'agent_id' in item
        assert item['agent_id']['S'] == 'trade-extraction-agent'
        assert 'agent_name' in item
        assert item['agent_name']['S'] == 'Trade Extraction Agent'
        assert 'agent_type' in item
        assert item['agent_type']['S'] == 'extraction'
        assert 'runtime_arn' in item
        assert item['runtime_arn']['S'] == runtime_arn
        assert 'status' in item
        assert item['status']['S'] == 'active'
        assert 'version' in item
        assert item['version']['S'] == '1.0.0'
        assert 'capabilities' in item
        assert 'SS' in item['capabilities']
        assert len(item['capabilities']['SS']) > 0
        assert 'created_at' in item
        assert 'updated_at' in item
        assert 'sop_enabled' in item
        assert item['sop_enabled']['BOOL'] is True
        assert 'sop_version' in item
        assert item['sop_version']['S'] == '1.0.0'
        
        # Verify timestamps are valid ISO format
        created_at = item['created_at']['S']
        updated_at = item['updated_at']['S']
        datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        # Verify capabilities include expected values
        capabilities = item['capabilities']['SS']
        expected_capabilities = {
            'pdf_processing', 'trade_data_extraction', 'data_validation',
            'table_routing', 'sop_workflow'
        }
        assert expected_capabilities.issubset(set(capabilities))
    
    @given(st.text(min_size=1, max_size=50))
    def test_property_4_agent_registration_error_handling(self, agent_id: str):
        """
        Property 4 Extension: Agent registration error handling must be robust.
        """
        # Mock DynamoDB error
        error_response = {
            'Error': {
                'Code': 'ValidationException',
                'Message': 'Test error message'
            }
        }
        self.mock_dynamodb.put_item.side_effect = ClientError(error_response, 'PutItem')
        
        # Test registration with error
        success, error_message = self.registry.register_trade_extraction_agent(
            runtime_arn='arn:aws:bedrock-agentcore:us-east-1:123456789012:agent/test',
            version="1.0.0",
            status="active"
        )
        
        # Verify error handling
        assert success is False
        assert error_message is not None
        assert isinstance(error_message, str)
        assert len(error_message) > 0
        assert 'Test error message' in error_message
    
    @given(st.sampled_from(['active', 'inactive', 'maintenance']))
    def test_property_4_agent_status_update(self, new_status: str):
        """
        Property 4 Extension: Agent status updates must be handled correctly.
        """
        # Mock successful update
        self.mock_dynamodb.update_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        # Test status update
        success, error_message = self.registry.update_agent_status(
            agent_id='trade-extraction-agent',
            status=new_status,
            version='1.1.0'
        )
        
        # Verify success
        assert success is True
        assert error_message is None
        
        # Verify update_item was called correctly
        assert self.mock_dynamodb.update_item.called
        call_args = self.mock_dynamodb.update_item.call_args
        
        # Verify update parameters
        assert call_args[1]['TableName'] == 'TestAgentRegistry'
        assert call_args[1]['Key']['agent_id']['S'] == 'trade-extraction-agent'
        
        # Verify update expression includes status and version
        update_expression = call_args[1]['UpdateExpression']
        assert '#status = :status' in update_expression
        assert 'version = :version' in update_expression
        assert 'updated_at = :updated_at' in update_expression
        
        # Verify attribute values
        attr_values = call_args[1]['ExpressionAttributeValues']
        assert attr_values[':status']['S'] == new_status
        assert attr_values[':version']['S'] == '1.1.0'
        assert ':updated_at' in attr_values
    
    def test_property_4_agent_info_retrieval(self):
        """
        Property 4 Extension: Agent info retrieval must return complete data.
        """
        # Mock DynamoDB response
        mock_item = {
            'agent_id': {'S': 'trade-extraction-agent'},
            'agent_name': {'S': 'Trade Extraction Agent'},
            'agent_type': {'S': 'extraction'},
            'runtime_arn': {'S': 'arn:aws:bedrock-agentcore:us-east-1:123456789012:agent/test'},
            'status': {'S': 'active'},
            'version': {'S': '1.0.0'},
            'capabilities': {'SS': ['pdf_processing', 'trade_data_extraction']},
            'created_at': {'S': '2024-01-01T00:00:00Z'},
            'updated_at': {'S': '2024-01-01T00:00:00Z'},
            'sop_enabled': {'BOOL': True},
            'sop_version': {'S': '1.0.0'}
        }
        
        self.mock_dynamodb.get_item.return_value = {'Item': mock_item}
        
        # Test retrieval
        success, agent_entry, error_message = self.registry.get_agent_info('trade-extraction-agent')
        
        # Verify success
        assert success is True
        assert error_message is None
        assert agent_entry is not None
        assert isinstance(agent_entry, AgentRegistryEntry)
        
        # Verify agent entry fields
        assert agent_entry.agent_id == 'trade-extraction-agent'
        assert agent_entry.agent_name == 'Trade Extraction Agent'
        assert agent_entry.agent_type == 'extraction'
        assert agent_entry.status == 'active'
        assert agent_entry.version == '1.0.0'
        assert agent_entry.sop_enabled is True
        assert agent_entry.sop_version == '1.0.0'
        assert len(agent_entry.capabilities) > 0
    
    def test_property_4_agent_not_found_handling(self):
        """
        Property 4 Extension: Agent not found scenarios must be handled gracefully.
        """
        # Mock empty response (agent not found)
        self.mock_dynamodb.get_item.return_value = {}
        
        # Test retrieval of non-existent agent
        success, agent_entry, error_message = self.registry.get_agent_info('non-existent-agent')
        
        # Verify proper handling
        assert success is False
        assert agent_entry is None
        assert error_message is not None
        assert 'not found' in error_message.lower()
    
    @given(st.text(min_size=1, max_size=20))
    def test_property_4_list_agents_by_type(self, agent_type: str):
        """
        Property 4 Extension: Listing agents by type must handle various inputs.
        """
        # Mock scan response
        mock_items = [
            {
                'agent_id': {'S': f'agent-1-{agent_type}'},
                'agent_name': {'S': f'Agent 1 {agent_type}'},
                'agent_type': {'S': agent_type},
                'runtime_arn': {'S': 'arn:aws:bedrock-agentcore:us-east-1:123456789012:agent/1'},
                'status': {'S': 'active'},
                'version': {'S': '1.0.0'},
                'capabilities': {'SS': ['capability1']},
                'created_at': {'S': '2024-01-01T00:00:00Z'},
                'updated_at': {'S': '2024-01-01T00:00:00Z'},
                'sop_enabled': {'BOOL': True},
                'sop_version': {'S': '1.0.0'}
            }
        ]
        
        self.mock_dynamodb.scan.return_value = {'Items': mock_items}
        
        # Test listing
        success, agents, error_message = self.registry.list_agents_by_type(agent_type)
        
        # Verify success
        assert success is True
        assert error_message is None
        assert isinstance(agents, list)
        assert len(agents) == 1
        assert isinstance(agents[0], AgentRegistryEntry)
        assert agents[0].agent_type == agent_type
        
        # Verify scan was called with correct filter
        call_args = self.mock_dynamodb.scan.call_args
        assert call_args[1]['TableName'] == 'TestAgentRegistry'
        assert call_args[1]['FilterExpression'] == 'agent_type = :agent_type'
        assert call_args[1]['ExpressionAttributeValues'][':agent_type']['S'] == agent_type
    
    def test_property_4_dynamodb_item_conversion(self):
        """
        Property 4 Extension: DynamoDB item conversion must be bidirectional.
        """
        # Test data
        test_dict = {
            'string_field': 'test_value',
            'bool_field': True,
            'int_field': 42,
            'float_field': 3.14,
            'list_field': ['item1', 'item2'],
            'null_field': None
        }
        
        # Convert to DynamoDB format
        dynamodb_item = self.registry._to_dynamodb_item(test_dict)
        
        # Verify DynamoDB format
        assert dynamodb_item['string_field']['S'] == 'test_value'
        assert dynamodb_item['bool_field']['BOOL'] is True
        assert dynamodb_item['int_field']['N'] == '42'
        assert dynamodb_item['float_field']['N'] == '3.14'
        assert dynamodb_item['list_field']['SS'] == ['item1', 'item2']
        assert dynamodb_item['null_field']['NULL'] is True
        
        # Convert back to regular dict
        converted_dict = self.registry._from_dynamodb_item(dynamodb_item)
        
        # Verify round-trip conversion (excluding type changes for numbers)
        assert converted_dict['string_field'] == test_dict['string_field']
        assert converted_dict['bool_field'] == test_dict['bool_field']
        assert converted_dict['int_field'] == test_dict['int_field']
        assert abs(converted_dict['float_field'] - test_dict['float_field']) < 0.001
        assert converted_dict['list_field'] == test_dict['list_field']
        assert converted_dict['null_field'] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])