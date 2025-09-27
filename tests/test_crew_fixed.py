"""
Unit tests for crew_fixed.py with request context support.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from typing import Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock external dependencies
sys.modules['openlit'] = MagicMock()
sys.modules['mcp'] = MagicMock()
sys.modules['crewai_tools'] = MagicMock()


class TestLatestTradeMatchingAgent:
    """Test LatestTradeMatchingAgent with request context"""

    @pytest.fixture
    def mock_dynamodb_tools(self):
        """Mock DynamoDB tools"""
        tool1 = Mock()
        tool1.name = "dynamodb_read"
        tool2 = Mock()
        tool2.name = "dynamodb_write"
        return [tool1, tool2]

    @pytest.fixture
    def request_context(self):
        """Sample request context"""
        return {
            's3_bucket': 'test-bucket',
            's3_key': 'BANK/test.pdf',
            'source_type': 'BANK',
            'unique_identifier': 'TEST123'
        }

    @patch('src.latest_trade_matching_agent.crew_fixed.PDFToImageTool')
    @patch('src.latest_trade_matching_agent.crew_fixed.FileWriterTool')
    @patch('src.latest_trade_matching_agent.crew_fixed.FileReadTool')
    @patch('src.latest_trade_matching_agent.crew_fixed.OCRTool')
    def test_initialization_with_context(self, mock_ocr, mock_file_read, mock_file_write, mock_pdf, mock_dynamodb_tools, request_context):
        """Test agent initialization with request context"""
        from src.latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent

        agent = LatestTradeMatchingAgent(
            dynamodb_tools=mock_dynamodb_tools,
            request_context=request_context
        )

        assert agent.dynamodb_tools == mock_dynamodb_tools
        assert agent.request_context == request_context
        assert agent.config['s3_bucket'] == 'test-bucket'

    @patch('src.latest_trade_matching_agent.crew_fixed.PDFToImageTool')
    @patch('src.latest_trade_matching_agent.crew_fixed.FileWriterTool')
    def test_configuration_defaults(self, mock_file_write, mock_pdf):
        """Test configuration uses defaults when no context provided"""
        from src.latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent

        agent = LatestTradeMatchingAgent()

        assert agent.config['s3_bucket'] == 'trade-documents-production'
        assert agent.config['dynamodb_bank_table'] == 'BankTradeData'
        assert agent.config['dynamodb_counterparty_table'] == 'CounterpartyTradeData'
        assert agent.config['max_rpm'] == 10
        assert agent.config['max_execution_time'] == 1200

    @patch.dict(os.environ, {'MAX_RPM': '20', 'MAX_EXECUTION_TIME': '3600'})
    @patch('src.latest_trade_matching_agent.crew_fixed.PDFToImageTool')
    def test_configuration_from_environment(self, mock_pdf):
        """Test configuration reads from environment variables"""
        from src.latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent

        agent = LatestTradeMatchingAgent()

        assert agent.config['max_rpm'] == 20
        assert agent.config['max_execution_time'] == 3600

    def test_set_request_context(self):
        """Test setting request context after initialization"""
        from src.latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent

        agent = LatestTradeMatchingAgent()
        new_context = {'source_type': 'COUNTERPARTY'}

        agent.set_request_context(new_context)
        assert agent.request_context == new_context

    @patch('src.latest_trade_matching_agent.crew_fixed.Agent')
    def test_document_processor_agent(self, mock_agent_class):
        """Test document processor agent creation"""
        from src.latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent

        agent = LatestTradeMatchingAgent()
        agent.agents_config = {'document_processor': {'role': 'processor'}}

        doc_processor = agent.document_processor()

        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args.kwargs
        assert call_kwargs['max_rpm'] == agent.config['max_rpm']
        assert call_kwargs['max_execution_time'] == agent.config['max_execution_time']
        assert call_kwargs['multimodal'] == True

    @patch('src.latest_trade_matching_agent.crew_fixed.Agent')
    def test_reporting_analyst_with_dynamodb(self, mock_agent_class, mock_dynamodb_tools):
        """Test reporting analyst gets DynamoDB tools"""
        from src.latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent

        agent = LatestTradeMatchingAgent(dynamodb_tools=mock_dynamodb_tools)
        agent.agents_config = {'reporting_analyst': {'role': 'analyst'}}

        reporting_analyst = agent.reporting_analyst()

        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args.kwargs
        # Check that DynamoDB tools were included
        assert len(call_kwargs['tools']) > 2  # file tools + dynamodb tools

    @patch('src.latest_trade_matching_agent.crew_fixed.Crew')
    def test_crew_creation_with_callbacks(self, mock_crew_class):
        """Test crew creation includes monitoring callbacks"""
        from src.latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent

        agent = LatestTradeMatchingAgent()
        agent.agents = []
        agent.tasks = []

        crew = agent.crew()

        mock_crew_class.assert_called_once()
        call_kwargs = mock_crew_class.call_args.kwargs
        assert call_kwargs['max_rpm'] == agent.config['max_rpm']
        assert 'step_callback' in call_kwargs
        assert 'task_callback' in call_kwargs

    def test_step_callback(self, caplog):
        """Test step callback logging"""
        from src.latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent

        agent = LatestTradeMatchingAgent()
        with caplog.at_level('INFO'):
            agent._step_callback("test_step")
            assert "Crew step executed: test_step" in caplog.text

    def test_task_callback(self, caplog):
        """Test task callback logging"""
        from src.latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent

        agent = LatestTradeMatchingAgent()

        # Test with task that has description
        task_with_desc = Mock()
        task_with_desc.description = "This is a very long task description that should be truncated"

        with caplog.at_level('INFO'):
            agent._task_callback(task_with_desc)
            assert "Task completed:" in caplog.text

        # Test with task without description
        task_without_desc = "simple_task"
        with caplog.at_level('INFO'):
            agent._task_callback(task_without_desc)
            assert "Task completed: simple_task" in caplog.text


class TestAgentIntegration:
    """Integration tests for agent with request context"""

    @patch('src.latest_trade_matching_agent.crew_fixed.Task')
    @patch('src.latest_trade_matching_agent.crew_fixed.Agent')
    def test_full_agent_initialization(self, mock_agent, mock_task):
        """Test full agent initialization with all components"""
        from src.latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent

        request_context = {
            's3_bucket': 'production-bucket',
            'source_type': 'BANK',
            'unique_identifier': 'PROD123'
        }

        agent = LatestTradeMatchingAgent(request_context=request_context)

        # Verify configuration includes request context
        assert agent.config['s3_bucket'] == 'production-bucket'

        # Create agents
        agent.agents_config = {
            'document_processor': {},
            'trade_entity_extractor': {},
            'reporting_analyst': {},
            'matching_analyst': {}
        }

        doc_proc = agent.document_processor()
        trade_ext = agent.trade_entity_extractor()
        report_analyst = agent.reporting_analyst()
        match_analyst = agent.matching_analyst()

        # Verify all agents were created
        assert mock_agent.call_count == 4

    @patch('src.latest_trade_matching_agent.crew_fixed.Crew')
    def test_crew_with_dynamic_configuration(self, mock_crew):
        """Test crew uses dynamic configuration from request context"""
        from src.latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent

        request_context = {
            's3_bucket': 'dynamic-bucket',
            'source_type': 'COUNTERPARTY'
        }

        with patch.dict(os.environ, {'MAX_RPM': '15'}):
            agent = LatestTradeMatchingAgent(request_context=request_context)
            agent.agents = []
            agent.tasks = []

            crew = agent.crew()

            # Verify crew was created with dynamic config
            call_kwargs = mock_crew.call_args.kwargs
            assert call_kwargs['max_rpm'] == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])