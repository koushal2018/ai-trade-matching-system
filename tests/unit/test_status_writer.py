"""
Unit tests for StatusWriter class.

Tests status initialization, agent status updates, and finalize operations.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Mock boto3 before importing status_writer with proper structure
mock_boto3 = MagicMock()
mock_dynamodb_resource = MagicMock()
mock_table = MagicMock()
mock_dynamodb_resource.Table.return_value = mock_table
mock_boto3.resource.return_value = mock_dynamodb_resource
sys.modules['boto3'] = mock_boto3

# Add deployment directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../deployment/swarm_agentcore'))

from status_writer import StatusWriter


class TestStatusWriterInitialization:
    """Test StatusWriter initialization and configuration."""
    
    def test_init_with_defaults(self):
        """Test StatusWriter initializes with default table name and region."""
        with patch('deployment.swarm_agentcore.status_writer.USE_STRANDS_TOOLS_AWS', False):
            writer = StatusWriter()
            
            assert writer.table_name == "trade-matching-system-processing-status"
            assert writer.region_name == "us-east-1"
            assert writer.use_strands_tool is False
    
    def test_init_with_custom_params(self):
        """Test StatusWriter initializes with custom table name and region."""
        with patch('deployment.swarm_agentcore.status_writer.USE_STRANDS_TOOLS_AWS', False):
            writer = StatusWriter(
                table_name="custom-table",
                region_name="us-west-2"
            )
            
            assert writer.table_name == "custom-table"
            assert writer.region_name == "us-west-2"
    
    def test_init_with_strands_tool(self):
        """Test StatusWriter initializes with strands_tools when available."""
        with patch('deployment.swarm_agentcore.status_writer.USE_STRANDS_TOOLS_AWS', True):
            writer = StatusWriter()
            
            assert writer.use_strands_tool is True


class TestStatusInitialization:
    """Test initialize_status method."""
    
    def test_initialize_status_creates_correct_item(self):
        """Test initialize_status creates DynamoDB item with all required fields."""
        with patch('deployment.swarm_agentcore.status_writer.USE_STRANDS_TOOLS_AWS', False):
            mock_table = Mock()
            writer = StatusWriter()
            writer.table = mock_table
        writer.initialize_status(
            session_id="session-123",
            correlation_id="corr-456",
            document_id="doc-789",
            source_type="BANK"
        )
        
        # Verify put_item was called
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]
        item = call_args['Item']
        
        # Verify required fields
        assert item['sessionId'] == "session-123"
        assert item['correlationId'] == "corr-456"
        assert item['documentId'] == "doc-789"
        assert item['sourceType'] == "BANK"
        assert item['overallStatus'] == "initializing"
        
        # Verify agent status objects
        for agent_key in ['pdfAdapter', 'tradeExtraction', 'tradeMatching', 'exceptionManagement']:
            assert agent_key in item
            assert item[agent_key]['status'] == "pending"
            assert item[agent_key]['activity'] == "Waiting to start"
        
        # Verify token usage
        assert item['totalTokenUsage'] == {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}
        assert item['totalDuration'] == 0.0
        
        # Verify timestamps
        assert 'createdAt' in item
        assert 'lastUpdated' in item
        assert 'expiresAt' in item
    
    def test_initialize_status_sets_ttl_90_days(self):
        """Test initialize_status sets TTL to 90 days from creation."""
        with patch('deployment.swarm_agentcore.status_writer.USE_STRANDS_TOOLS_AWS', False):
            mock_table = Mock()
            writer = StatusWriter()
            writer.table = mock_table
        now = datetime.now(timezone.utc)
        
        writer.initialize_status(
            session_id="session-123",
            correlation_id="corr-456",
            document_id="doc-789",
            source_type="BANK"
        )
        
        call_args = mock_table.put_item.call_args[1]
        item = call_args['Item']
        
        # Verify TTL is approximately 90 days from now
        expected_ttl = int((now + timedelta(days=90)).timestamp())
        actual_ttl = item['expiresAt']
        
        # Allow 5 second tolerance for test execution time
        assert abs(actual_ttl - expected_ttl) < 5
    
    def test_initialize_status_handles_errors_gracefully(self):
        """Test initialize_status doesn't raise exceptions on DynamoDB errors."""
        with patch('deployment.swarm_agentcore.status_writer.USE_STRANDS_TOOLS_AWS', False):
            mock_table = Mock()
            mock_table.put_item.side_effect = Exception("DynamoDB error")
            writer = StatusWriter()
            writer.table = mock_table
        
        # Should not raise exception
        writer.initialize_status(
            session_id="session-123",
            correlation_id="corr-456",
            document_id="doc-789",
            source_type="BANK"
        )


class TestAgentStatusUpdate:
    """Test update_agent_status method."""
    
    def test_update_agent_status_in_progress(self):
        """Test update_agent_status sets agent to in-progress with startedAt."""
        with patch('deployment.swarm_agentcore.status_writer.USE_STRANDS_TOOLS_AWS', False):
            mock_table = Mock()
            writer = StatusWriter()
            writer.table = mock_table
        writer.update_agent_status(
            session_id="session-123",
            correlation_id="corr-456",
            agent_key="pdfAdapter",
            status="in-progress"
        )
        
        # Verify update_item was called
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]
        
        # Verify update expression
        assert "SET #agent = :status" in call_args['UpdateExpression']
        assert call_args['ExpressionAttributeNames']['#agent'] == "pdfAdapter"
        
        # Verify agent status object
        agent_status = call_args['ExpressionAttributeValues'][':status']
        assert agent_status['status'] == "in-progress"
        assert agent_status['activity'] == "Extracting text from PDF document"
        assert 'startedAt' in agent_status
    
    def test_update_agent_status_success_with_tokens(self):
        """Test update_agent_status extracts token usage on success."""
        with patch('deployment.swarm_agentcore.status_writer.USE_STRANDS_TOOLS_AWS', False):
            mock_table = Mock()
            writer = StatusWriter()
            writer.table = mock_table
        agent_response = {
            "success": True,
            "processing_time_ms": 15000,
            "token_usage": {
                "input_tokens": 1000,
                "output_tokens": 500,
                "total_tokens": 1500
            }
        }
        
        writer.update_agent_status(
            session_id="session-123",
            correlation_id="corr-456",
            agent_key="tradeExtraction",
            status="success",
            agent_response=agent_response
        )
        
        call_args = mock_table.update_item.call_args[1]
        agent_status = call_args['ExpressionAttributeValues'][':status']
        
        # Verify token usage
        assert agent_status['tokenUsage']['inputTokens'] == 1000
        assert agent_status['tokenUsage']['outputTokens'] == 500
        assert agent_status['tokenUsage']['totalTokens'] == 1500
        
        # Verify duration
        assert agent_status['duration'] == 15.0  # 15000ms = 15s
        
        # Verify timestamps
        assert 'completedAt' in agent_status
    
    def test_update_agent_status_error_with_message(self):
        """Test update_agent_status includes error message on failure."""
        with patch('deployment.swarm_agentcore.status_writer.USE_STRANDS_TOOLS_AWS', False):
            mock_table = Mock()
            writer = StatusWriter()
            writer.table = mock_table
        agent_response = {
            "success": False,
            "error": "Failed to extract trade data",
            "processing_time_ms": 5000
        }
        
        writer.update_agent_status(
            session_id="session-123",
            correlation_id="corr-456",
            agent_key="tradeMatching",
            status="error",
            agent_response=agent_response
        )
        
        call_args = mock_table.update_item.call_args[1]
        agent_status = call_args['ExpressionAttributeValues'][':status']
        
        # Verify error message
        assert agent_status['error'] == "Failed to extract trade data"
        assert agent_status['status'] == "error"
        
        # Verify overallStatus set to failed
        assert call_args['ExpressionAttributeValues'][':overall'] == "failed"
    
    def test_update_agent_status_handles_missing_token_usage(self):
        """Test update_agent_status handles missing token usage gracefully."""
        with patch('deployment.swarm_agentcore.status_writer.USE_STRANDS_TOOLS_AWS', False):
            mock_table = Mock()
            writer = StatusWriter()
            writer.table = mock_table
        agent_response = {
            "success": True,
            "processing_time_ms": 10000
            # No token_usage field
        }
        
        writer.update_agent_status(
            session_id="session-123",
            correlation_id="corr-456",
            agent_key="pdfAdapter",
            status="success",
            agent_response=agent_response
        )
        
        call_args = mock_table.update_item.call_args[1]
        agent_status = call_args['ExpressionAttributeValues'][':status']
        
        # Should not have tokenUsage field if not provided
        assert 'tokenUsage' not in agent_status


class TestFinalizeStatus:
    """Test finalize_status method."""
    
    def test_finalize_status_completed(self):
        """Test finalize_status sets overallStatus to completed."""
        with patch('deployment.swarm_agentcore.status_writer.USE_STRANDS_TOOLS_AWS', False):
            mock_table = Mock()
            writer = StatusWriter()
            writer.table = mock_table
        writer.finalize_status(
            session_id="session-123",
            correlation_id="corr-456",
            overall_status="completed"
        )
        
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]
        
        assert call_args['ExpressionAttributeValues'][':status'] == "completed"
        assert 'lastUpdated' in call_args['UpdateExpression']
    
    def test_finalize_status_failed(self):
        """Test finalize_status sets overallStatus to failed."""
        with patch('deployment.swarm_agentcore.status_writer.USE_STRANDS_TOOLS_AWS', False):
            mock_table = Mock()
            writer = StatusWriter()
            writer.table = mock_table
        writer.finalize_status(
            session_id="session-123",
            correlation_id="corr-456",
            overall_status="failed"
        )
        
        call_args = mock_table.update_item.call_args[1]
        assert call_args['ExpressionAttributeValues'][':status'] == "failed"


class TestHelperMethods:
    """Test helper methods."""
    
    def test_pending_status_structure(self):
        """Test _pending_status returns correct structure."""
        pending = StatusWriter._pending_status()
        
        assert pending['status'] == "pending"
        assert pending['activity'] == "Waiting to start"
        assert pending['tokenUsage'] == {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}
    
    def test_get_activity_message_all_agents(self):
        """Test _get_activity_message returns correct messages for all agents."""
        test_cases = [
            ("pdfAdapter", "in-progress", "Extracting text from PDF document"),
            ("pdfAdapter", "success", "Text extraction complete"),
            ("pdfAdapter", "error", "Text extraction failed"),
            ("tradeExtraction", "in-progress", "Extracting structured trade data"),
            ("tradeMatching", "success", "Trade matching complete"),
            ("exceptionManagement", "error", "Exception handling failed"),
        ]
        
        for agent_key, status, expected_message in test_cases:
            message = StatusWriter._get_activity_message(agent_key, status)
            assert message == expected_message
    
    def test_get_activity_message_unknown_agent(self):
        """Test _get_activity_message returns default for unknown agent."""
        message = StatusWriter._get_activity_message("unknownAgent", "in-progress")
        assert message == "Processing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
