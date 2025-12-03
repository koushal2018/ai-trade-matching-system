"""
Test Trade Data Extraction Agent

Basic tests to verify the Trade Data Extraction Agent functionality.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.latest_trade_matching_agent.agents.trade_extraction_agent import TradeDataExtractionAgent
from src.latest_trade_matching_agent.models.events import StandardEventMessage, EventTaxonomy
from src.latest_trade_matching_agent.models.adapter import CanonicalAdapterOutput
from src.latest_trade_matching_agent.models.trade import CanonicalTradeModel


class TestTradeDataExtractionAgent:
    """Test suite for Trade Data Extraction Agent."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        with patch('boto3.client'):
            agent = TradeDataExtractionAgent(
                agent_id="test_extraction_agent",
                region_name="us-east-1"
            )
            return agent
    
    @pytest.fixture
    def sample_canonical_output(self):
        """Create sample canonical adapter output."""
        return CanonicalAdapterOutput(
            adapter_type="PDF",
            document_id="test_doc_001",
            source_type="COUNTERPARTY",
            extracted_text="""
            Trade Confirmation
            Trade ID: GCS382857
            Trade Date: 2024-10-15
            Notional: 1000000
            Currency: USD
            Counterparty: Goldman Sachs
            Product Type: SWAP
            Effective Date: 2024-10-17
            Maturity Date: 2025-10-17
            Commodity Type: CRUDE_OIL
            Settlement Type: CASH
            """,
            metadata={
                "page_count": 5,
                "dpi": 300,
                "ocr_confidence": 0.95
            },
            s3_location="s3://test-bucket/extracted/COUNTERPARTY/test_doc_001.json",
            correlation_id="corr_test_001"
        )
    
    @pytest.fixture
    def sample_trade_data(self):
        """Create sample extracted trade data."""
        return {
            "Trade_ID": "GCS382857",
            "TRADE_SOURCE": "COUNTERPARTY",
            "trade_date": "2024-10-15",
            "notional": 1000000.0,
            "currency": "USD",
            "counterparty": "Goldman Sachs",
            "product_type": "SWAP",
            "effective_date": "2024-10-17",
            "maturity_date": "2025-10-17",
            "commodity_type": "CRUDE_OIL",
            "settlement_type": "CASH"
        }
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly."""
        assert agent.agent_id == "test_extraction_agent"
        assert agent.region_name == "us-east-1"
        assert agent.bank_table_name == "BankTradeData"
        assert agent.counterparty_table_name == "CounterpartyTradeData"
    
    def test_register_agent(self, agent):
        """Test agent registration."""
        with patch.object(agent.registry, 'register_agent') as mock_register:
            mock_register.return_value = {"success": True, "agent_id": agent.agent_id}
            
            result = agent.register()
            
            assert result["success"] is True
            assert result["agent_id"] == agent.agent_id
            mock_register.assert_called_once()
    
    @patch('boto3.client')
    def test_extract_trade_success(self, mock_boto_client, agent, sample_canonical_output, sample_trade_data):
        """Test successful trade extraction."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: sample_canonical_output.model_dump_json().encode('utf-8'))
        }
        agent.s3 = mock_s3
        
        # Mock DynamoDB client
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.return_value = {}
        agent.dynamodb = mock_dynamodb
        
        # Mock SQS client
        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {}
        agent.sqs = mock_sqs
        
        # Mock LLM extraction tool
        mock_canonical_trade = CanonicalTradeModel(**sample_trade_data)
        agent.llm_extraction_tool.extract_trade_fields = Mock(return_value={
            "success": True,
            "trade_data": sample_trade_data,
            "canonical_trade": mock_canonical_trade,
            "extraction_confidence": 0.92
        })
        
        # Mock trade source classifier
        agent.trade_source_classifier.classify_trade_source = Mock(return_value={
            "success": True,
            "source_type": "COUNTERPARTY",
            "confidence": 0.95
        })
        
        # Mock registry
        agent.registry.update_agent_status = Mock(return_value={"success": True})
        
        # Create test event
        test_event = StandardEventMessage(
            event_id="evt_test_001",
            event_type=EventTaxonomy.PDF_PROCESSED,
            source_agent="pdf_adapter_agent",
            correlation_id="corr_test_001",
            payload={
                "document_id": "test_doc_001",
                "canonical_output_location": "s3://test-bucket/extracted/COUNTERPARTY/test_doc_001.json"
            }
        )
        
        # Execute extraction
        result = agent.extract_trade(test_event)
        
        # Verify result
        assert result["success"] is True
        assert result["trade_id"] == "GCS382857"
        assert result["source_type"] == "COUNTERPARTY"
        assert result["table_name"] == "CounterpartyTradeData"
        assert result["extraction_confidence"] == 0.92
        
        # Verify S3 was called
        mock_s3.get_object.assert_called_once()
        mock_s3.put_object.assert_called_once()
        
        # Verify DynamoDB was called
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args
        assert call_args[1]["TableName"] == "CounterpartyTradeData"
        
        # Verify SQS was called
        mock_sqs.send_message.assert_called_once()
    
    @patch('boto3.client')
    def test_extract_trade_bank_routing(self, mock_boto_client, agent, sample_canonical_output, sample_trade_data):
        """Test that BANK trades are routed to BankTradeData table."""
        # Modify sample data for BANK source
        sample_canonical_output.source_type = "BANK"
        sample_trade_data["TRADE_SOURCE"] = "BANK"
        
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: sample_canonical_output.model_dump_json().encode('utf-8'))
        }
        agent.s3 = mock_s3
        
        # Mock DynamoDB client
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.return_value = {}
        agent.dynamodb = mock_dynamodb
        
        # Mock SQS client
        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {}
        agent.sqs = mock_sqs
        
        # Mock LLM extraction tool
        mock_canonical_trade = CanonicalTradeModel(**sample_trade_data)
        agent.llm_extraction_tool.extract_trade_fields = Mock(return_value={
            "success": True,
            "trade_data": sample_trade_data,
            "canonical_trade": mock_canonical_trade,
            "extraction_confidence": 0.92
        })
        
        # Mock trade source classifier
        agent.trade_source_classifier.classify_trade_source = Mock(return_value={
            "success": True,
            "source_type": "BANK",
            "confidence": 0.95
        })
        
        # Mock registry
        agent.registry.update_agent_status = Mock(return_value={"success": True})
        
        # Create test event
        test_event = StandardEventMessage(
            event_id="evt_test_002",
            event_type=EventTaxonomy.PDF_PROCESSED,
            source_agent="pdf_adapter_agent",
            correlation_id="corr_test_002",
            payload={
                "document_id": "test_doc_002",
                "canonical_output_location": "s3://test-bucket/extracted/BANK/test_doc_002.json"
            }
        )
        
        # Execute extraction
        result = agent.extract_trade(test_event)
        
        # Verify result
        assert result["success"] is True
        assert result["source_type"] == "BANK"
        assert result["table_name"] == "BankTradeData"
        
        # Verify DynamoDB was called with correct table
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args
        assert call_args[1]["TableName"] == "BankTradeData"
    
    @patch('boto3.client')
    def test_extract_trade_extraction_failure(self, mock_boto_client, agent, sample_canonical_output):
        """Test handling of extraction failures."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: sample_canonical_output.model_dump_json().encode('utf-8'))
        }
        agent.s3 = mock_s3
        
        # Mock SQS client
        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {}
        agent.sqs = mock_sqs
        
        # Mock LLM extraction tool to fail
        agent.llm_extraction_tool.extract_trade_fields = Mock(return_value={
            "success": False,
            "error": "Failed to extract mandatory field: Trade_ID"
        })
        
        # Create test event
        test_event = StandardEventMessage(
            event_id="evt_test_003",
            event_type=EventTaxonomy.PDF_PROCESSED,
            source_agent="pdf_adapter_agent",
            correlation_id="corr_test_003",
            payload={
                "document_id": "test_doc_003",
                "canonical_output_location": "s3://test-bucket/extracted/COUNTERPARTY/test_doc_003.json"
            }
        )
        
        # Execute extraction
        result = agent.extract_trade(test_event)
        
        # Verify result
        assert result["success"] is False
        assert "error" in result
        
        # Verify exception event was published
        mock_sqs.send_message.assert_called_once()
        call_args = mock_sqs.send_message.call_args
        message_body = json.loads(call_args[1]["MessageBody"])
        assert message_body["event_type"] == EventTaxonomy.EXCEPTION_RAISED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
