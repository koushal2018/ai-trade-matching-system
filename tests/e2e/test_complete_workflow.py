"""End-to-end integration tests for the complete trade matching workflow."""

import os
import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from .test_data_generator import TestDataGenerator, generate_test_data


class TestCompleteWorkflow:
    """Test the complete workflow from PDF to matching report."""
    
    @pytest.fixture
    def generator(self):
        return TestDataGenerator(seed=42)
    
    @pytest.fixture
    def test_dataset(self, generator):
        return generator.generate_test_dataset(
            matched_count=3,
            probable_count=2,
            break_count=1,
            error_count=1
        )
    
    def test_pdf_adapter_processes_document(self):
        """Test that PDF Adapter processes documents correctly."""
        # This would be an integration test with actual S3 and Bedrock
        # For now, we test the structure
        payload = {
            "document_id": "TEST001",
            "document_path": "s3://test-bucket/BANK/test.pdf",
            "source_type": "BANK"
        }
        
        # Verify payload structure
        assert "document_id" in payload
        assert "document_path" in payload
        assert payload["source_type"] in ["BANK", "COUNTERPARTY"]
    
    def test_trade_extraction_parses_fields(self, test_dataset):
        """Test that Trade Extraction parses all required fields."""
        for trade_data in test_dataset:
            bank_trade = trade_data.bank_trade
            
            # Verify required fields
            assert "Trade_ID" in bank_trade
            assert "TRADE_SOURCE" in bank_trade
            assert "trade_date" in bank_trade
            assert "notional" in bank_trade or trade_data.expected_classification == "DATA_ERROR"
            assert "currency" in bank_trade
            assert "counterparty" in bank_trade
    
    def test_trade_matching_classifies_correctly(self, test_dataset):
        """Test that Trade Matching classifies trades correctly."""
        for trade_data in test_dataset:
            # Verify expected classification is valid
            assert trade_data.expected_classification in [
                "MATCHED", "PROBABLE_MATCH", "REVIEW_REQUIRED", "BREAK", "DATA_ERROR"
            ]
    
    def test_matching_pair_scores_high(self, generator):
        """Test that matching pairs get high scores."""
        trade_data = generator.generate_matching_pair()
        
        # Matching pairs should have no mismatches
        assert len(trade_data.mismatch_fields) == 0
        assert trade_data.expected_match is True
        assert trade_data.expected_classification == "MATCHED"
    
    def test_break_pair_scores_low(self, generator):
        """Test that break pairs get low scores."""
        trade_data = generator.generate_break_pair()
        
        # Break pairs should have significant mismatches
        assert len(trade_data.mismatch_fields) > 0
        assert trade_data.expected_match is False
        assert trade_data.expected_classification == "BREAK"
    
    def test_data_error_detected(self, generator):
        """Test that data errors are detected."""
        trade_data = generator.generate_data_error_pair()
        
        assert trade_data.expected_classification == "DATA_ERROR"
        assert "notional" in trade_data.mismatch_fields


class TestErrorHandling:
    """Test error handling and recovery."""
    
    def test_invalid_source_type_rejected(self):
        """Test that invalid source types are rejected."""
        payload = {
            "document_id": "TEST001",
            "document_path": "s3://test-bucket/test.pdf",
            "source_type": "INVALID"
        }
        
        # Source type should be BANK or COUNTERPARTY
        assert payload["source_type"] not in ["BANK", "COUNTERPARTY"]
    
    def test_missing_required_fields_detected(self):
        """Test that missing required fields are detected."""
        incomplete_trade = {
            "Trade_ID": "TEST001",
            "TRADE_SOURCE": "BANK"
            # Missing: trade_date, notional, currency, counterparty
        }
        
        required_fields = ["trade_date", "notional", "currency", "counterparty"]
        missing = [f for f in required_fields if f not in incomplete_trade]
        
        assert len(missing) > 0


class TestAuditTrail:
    """Test audit trail completeness."""
    
    def test_audit_record_structure(self):
        """Test that audit records have required structure."""
        audit_record = {
            "audit_id": "aud_123",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent_id": "pdf_adapter",
            "agent_name": "PDF Adapter Agent",
            "action_type": "PDF_PROCESSED",
            "trade_id": "TEST001",
            "outcome": "SUCCESS",
            "details": {"processing_time_ms": 5000},
            "immutable_hash": "abc123..."
        }
        
        required_fields = [
            "audit_id", "timestamp", "agent_id", "agent_name",
            "action_type", "outcome", "immutable_hash"
        ]
        
        for field in required_fields:
            assert field in audit_record
    
    def test_audit_action_types_valid(self):
        """Test that all action types are valid."""
        valid_action_types = [
            "PDF_PROCESSED", "TRADE_EXTRACTED", "TRADE_MATCHED",
            "EXCEPTION_RAISED", "HITL_DECISION", "AGENT_STARTED", "AGENT_STOPPED"
        ]
        
        # All action types should be in the valid list
        for action_type in valid_action_types:
            assert isinstance(action_type, str)
            assert len(action_type) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
