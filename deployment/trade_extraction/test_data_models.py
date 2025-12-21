"""
Test utilities and fixtures for data models.

This module provides reusable test data and utilities for testing
the trade extraction data models.
"""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any
import uuid

from data_models import (
    TradeExtractionRequest,
    TradeExtractionResponse, 
    CanonicalTradeData,
    AgentRegistryEntry
)


class TestDataFactory:
    """Factory for creating test data instances."""
    
    @staticmethod
    def create_valid_request(
        document_path: str = "s3://test-bucket/test-doc.pdf",
        source_type: str = "BANK",
        correlation_id: str = None
    ) -> TradeExtractionRequest:
        """Create a valid TradeExtractionRequest for testing."""
        if correlation_id is None:
            correlation_id = f"corr_{uuid.uuid4().hex[:12]}"
        
        return TradeExtractionRequest(
            document_path=document_path,
            source_type=source_type,
            correlation_id=correlation_id
        )
    
    @staticmethod
    def create_valid_canonical_data(
        trade_id: str = "TEST123",
        correlation_id: str = None
    ) -> CanonicalTradeData:
        """Create valid CanonicalTradeData for testing."""
        if correlation_id is None:
            correlation_id = f"corr_{uuid.uuid4().hex[:12]}"
        
        return CanonicalTradeData(
            trade_id=trade_id,
            counterparty="Test Bank Corp",
            notional_amount=Decimal("1000000.00"),
            currency="USD",
            trade_date="2024-01-15",
            maturity_date="2025-01-15",
            product_type="IRS",
            correlation_id=correlation_id,
            source_document="s3://test-bucket/test-doc.pdf",
            extracted_at=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def create_invalid_request_scenarios() -> Dict[str, Dict[str, Any]]:
        """Create various invalid request scenarios for testing."""
        return {
            "missing_document_path": {
                "document_path": "",
                "source_type": "BANK",
                "correlation_id": "corr_123456789abc"
            },
            "invalid_s3_uri": {
                "document_path": "file://local/path.pdf",
                "source_type": "BANK", 
                "correlation_id": "corr_123456789abc"
            },
            "invalid_source_type": {
                "document_path": "s3://test-bucket/test.pdf",
                "source_type": "INVALID",
                "correlation_id": "corr_123456789abc"
            },
            "invalid_correlation_id": {
                "document_path": "s3://test-bucket/test.pdf",
                "source_type": "BANK",
                "correlation_id": "invalid_format"
            }
        }


# Test data constants for reuse across tests
VALID_CURRENCY_CODES = ["USD", "EUR", "GBP", "JPY", "CHF"]
INVALID_CURRENCY_CODES = ["US", "DOLLAR", "123", ""]
VALID_SOURCE_TYPES = ["BANK", "COUNTERPARTY"]
INVALID_SOURCE_TYPES = ["BROKER", "EXCHANGE", "", None]

# Sample trade data for end-to-end testing
SAMPLE_BANK_TRADE = {
    "trade_id": "BNK-2024-001",
    "counterparty": "Goldman Sachs",
    "notional_amount": "5000000.00",
    "currency": "USD",
    "trade_date": "2024-01-15",
    "maturity_date": "2029-01-15",
    "product_type": "IRS"
}

SAMPLE_COUNTERPARTY_TRADE = {
    "trade_id": "CP-2024-001", 
    "counterparty": "JP Morgan",
    "notional_amount": "2500000.00",
    "currency": "EUR",
    "trade_date": "2024-01-16",
    "maturity_date": "2027-01-16",
    "product_type": "CDS"
}