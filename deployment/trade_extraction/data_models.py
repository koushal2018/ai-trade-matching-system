"""
Core data models for the Trade Extraction Agent.

This module defines the core data classes and interfaces used throughout
the trade extraction system, including request/response models and
canonical trade data structures.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
import re
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TradeExtractionRequest:
    """
    Request model for trade extraction operations.
    
    This class represents the input to the trade extraction agent,
    containing all necessary information to process a trade document.
    """
    document_path: str      # S3 URI of PDF document
    source_type: str        # "BANK" or "COUNTERPARTY"
    correlation_id: str     # Tracing identifier
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate request parameters before processing.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        logger.info(f"Starting validation for TradeExtractionRequest with correlation_id: {self.correlation_id}")
        logger.debug(f"Request validation inputs - document_path: {self.document_path}, source_type: {self.source_type}")
        
        errors = []
        
        # Validate document_path
        if not self.document_path or not self.document_path.startswith('s3://'):
            error_msg = "document_path must be a valid S3 URI"
            errors.append(error_msg)
            logger.error(f"Validation failed for correlation_id {self.correlation_id}: {error_msg} (provided: {self.document_path})")
        else:
            logger.debug(f"Document path validation passed for correlation_id {self.correlation_id}: {self.document_path}")
        
        # Validate source_type
        if self.source_type not in ['BANK', 'COUNTERPARTY']:
            error_msg = "source_type must be either 'BANK' or 'COUNTERPARTY'"
            errors.append(error_msg)
            logger.error(f"Validation failed for correlation_id {self.correlation_id}: {error_msg} (provided: {self.source_type})")
        else:
            logger.debug(f"Source type validation passed for correlation_id {self.correlation_id}: {self.source_type}")
        
        # Validate correlation_id format
        if not re.match(r'^corr_[a-f0-9]{12}$', self.correlation_id):
            error_msg = "correlation_id must follow format 'corr_[a-f0-9]{12}'"
            errors.append(error_msg)
            logger.error(f"Validation failed: {error_msg} (provided: {self.correlation_id})")
        else:
            logger.debug(f"Correlation ID format validation passed: {self.correlation_id}")
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.info(f"TradeExtractionRequest validation successful for correlation_id: {self.correlation_id}")
        else:
            logger.error(f"TradeExtractionRequest validation failed for correlation_id {self.correlation_id} with {len(errors)} errors: {errors}")
        
        return is_valid, errors


@dataclass
class TradeExtractionResponse:
    """
    Response model for trade extraction operations.
    
    This class represents the output from the trade extraction agent,
    containing the results of processing a trade document.
    """
    success: bool
    correlation_id: str
    extracted_data: Optional[Dict[str, Any]]
    table_name: Optional[str]
    error_message: Optional[str]
    processing_time_ms: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for JSON serialization."""
        logger.debug(f"Converting TradeExtractionResponse to dict for correlation_id: {self.correlation_id}")
        
        result = {
            'success': self.success,
            'correlation_id': self.correlation_id,
            'extracted_data': self.extracted_data,
            'table_name': self.table_name,
            'error_message': self.error_message,
            'processing_time_ms': self.processing_time_ms
        }
        
        logger.debug(f"Response serialization completed for correlation_id {self.correlation_id} - success: {self.success}, processing_time: {self.processing_time_ms}ms")
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradeExtractionResponse':
        """Create response from dictionary (JSON deserialization)."""
        correlation_id = data.get('correlation_id', 'unknown')
        logger.debug(f"Deserializing TradeExtractionResponse from dict for correlation_id: {correlation_id}")
        
        try:
            response = cls(
                success=data['success'],
                correlation_id=correlation_id,
                extracted_data=data.get('extracted_data'),
                table_name=data.get('table_name'),
                error_message=data.get('error_message'),
                processing_time_ms=data['processing_time_ms']
            )
            logger.debug(f"Response deserialization successful for correlation_id: {correlation_id}")
            return response
        except KeyError as e:
            logger.error(f"Response deserialization failed for correlation_id {correlation_id}: missing required field {e}")
            raise ValueError(f"Missing required field in response data: {e}")


@dataclass
class CanonicalTradeData:
    """
    Canonical trade data structure.
    
    This class represents the standardized format for trade data
    after extraction and validation, ensuring consistency across
    the system.
    """
    trade_id: str                    # Unique trade identifier
    counterparty: str               # Counterparty name
    notional_amount: Decimal        # Trade notional amount
    currency: str                   # ISO 4217 currency code
    trade_date: str                 # ISO 8601 date format
    maturity_date: Optional[str]    # ISO 8601 date format
    product_type: str               # Derivative product type
    correlation_id: str             # Tracing identifier
    source_document: str            # S3 URI of source PDF
    extracted_at: str               # ISO 8601 timestamp
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the canonical trade data.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        logger.info(f"Starting CanonicalTradeData validation for correlation_id: {self.correlation_id}, trade_id: {self.trade_id}")
        logger.debug(f"Validation inputs - counterparty: {self.counterparty}, notional: {self.notional_amount}, currency: {self.currency}")
        
        errors = []
        
        # Validate trade_id
        if not self.trade_id:
            error_msg = "trade_id is required"
            errors.append(error_msg)
            logger.error(f"Validation failed for correlation_id {self.correlation_id}: {error_msg}")
        else:
            logger.debug(f"Trade ID validation passed for correlation_id {self.correlation_id}: {self.trade_id}")
        
        # Validate counterparty
        if not self.counterparty:
            error_msg = "counterparty is required"
            errors.append(error_msg)
            logger.error(f"Validation failed for correlation_id {self.correlation_id}: {error_msg}")
        else:
            logger.debug(f"Counterparty validation passed for correlation_id {self.correlation_id}: {self.counterparty}")
        
        # Validate notional_amount
        if self.notional_amount <= 0:
            error_msg = "notional_amount must be positive"
            errors.append(error_msg)
            logger.error(f"Validation failed for correlation_id {self.correlation_id}: {error_msg} (value: {self.notional_amount})")
        else:
            logger.debug(f"Notional amount validation passed for correlation_id {self.correlation_id}: {self.notional_amount}")
        
        # Validate currency (ISO 4217 format)
        if not re.match(r'^[A-Z]{3}$', self.currency):
            error_msg = "currency must be valid ISO 4217 code"
            errors.append(error_msg)
            logger.error(f"Validation failed for correlation_id {self.correlation_id}: {error_msg} (provided: {self.currency})")
        else:
            logger.debug(f"Currency validation passed for correlation_id {self.correlation_id}: {self.currency}")
        
        # Validate trade_date
        if not self._is_valid_iso8601_date(self.trade_date):
            error_msg = "trade_date must be valid ISO 8601 format"
            errors.append(error_msg)
            logger.error(f"Validation failed for correlation_id {self.correlation_id}: {error_msg} (provided: {self.trade_date})")
        else:
            logger.debug(f"Trade date validation passed for correlation_id {self.correlation_id}: {self.trade_date}")
        
        # Validate maturity_date (optional)
        if self.maturity_date and not self._is_valid_iso8601_date(self.maturity_date):
            error_msg = "maturity_date must be valid ISO 8601 format"
            errors.append(error_msg)
            logger.error(f"Validation failed for correlation_id {self.correlation_id}: {error_msg} (provided: {self.maturity_date})")
        elif self.maturity_date:
            logger.debug(f"Maturity date validation passed for correlation_id {self.correlation_id}: {self.maturity_date}")
        
        # Validate product_type
        if not self.product_type:
            error_msg = "product_type is required"
            errors.append(error_msg)
            logger.error(f"Validation failed for correlation_id {self.correlation_id}: {error_msg}")
        else:
            logger.debug(f"Product type validation passed for correlation_id {self.correlation_id}: {self.product_type}")
        
        # Validate correlation_id format
        if not re.match(r'^corr_[a-f0-9]{12}$', self.correlation_id):
            error_msg = "correlation_id must follow format 'corr_[a-f0-9]{12}'"
            errors.append(error_msg)
            logger.error(f"Validation failed: {error_msg} (provided: {self.correlation_id})")
        
        # Validate source_document
        if not self.source_document.startswith('s3://'):
            error_msg = "source_document must be valid S3 URI"
            errors.append(error_msg)
            logger.error(f"Validation failed for correlation_id {self.correlation_id}: {error_msg} (provided: {self.source_document})")
        else:
            logger.debug(f"Source document validation passed for correlation_id {self.correlation_id}: {self.source_document}")
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.info(f"CanonicalTradeData validation successful for correlation_id {self.correlation_id}, trade_id: {self.trade_id}")
        else:
            logger.error(f"CanonicalTradeData validation failed for correlation_id {self.correlation_id} with {len(errors)} errors: {errors}")
        
        return is_valid, errors
    
    def _is_valid_iso8601_date(self, date_str: str) -> bool:
        """Check if date string is valid ISO 8601 format."""
        logger.debug(f"Validating ISO 8601 date format for: {date_str}")
        
        try:
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            logger.debug(f"ISO 8601 date validation successful: {date_str}")
            return True
        except ValueError as e:
            logger.debug(f"ISO 8601 date validation failed for {date_str}: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        logger.debug(f"Converting CanonicalTradeData to dict for correlation_id: {self.correlation_id}, trade_id: {self.trade_id}")
        
        # Convert Decimal to string for JSON serialization
        notional_str = str(self.notional_amount)
        logger.debug(f"Converted notional amount from Decimal to string: {self.notional_amount} -> {notional_str}")
        
        result = {
            'trade_id': self.trade_id,
            'counterparty': self.counterparty,
            'notional_amount': notional_str,
            'currency': self.currency,
            'trade_date': self.trade_date,
            'maturity_date': self.maturity_date,
            'product_type': self.product_type,
            'correlation_id': self.correlation_id,
            'source_document': self.source_document,
            'extracted_at': self.extracted_at
        }
        
        logger.debug(f"CanonicalTradeData serialization completed for correlation_id {self.correlation_id}")
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CanonicalTradeData':
        """Create from dictionary (database retrieval)."""
        correlation_id = data.get('correlation_id', 'unknown')
        trade_id = data.get('trade_id', 'unknown')
        logger.debug(f"Deserializing CanonicalTradeData from dict for correlation_id: {correlation_id}, trade_id: {trade_id}")
        
        try:
            # Convert string back to Decimal
            notional_str = data['notional_amount']
            notional_decimal = Decimal(notional_str)
            logger.debug(f"Converted notional amount from string to Decimal: {notional_str} -> {notional_decimal}")
            
            trade_data = cls(
                trade_id=data['trade_id'],
                counterparty=data['counterparty'],
                notional_amount=notional_decimal,
                currency=data['currency'],
                trade_date=data['trade_date'],
                maturity_date=data.get('maturity_date'),
                product_type=data['product_type'],
                correlation_id=correlation_id,
                source_document=data['source_document'],
                extracted_at=data['extracted_at']
            )
            
            logger.info(f"CanonicalTradeData deserialization successful for correlation_id: {correlation_id}, trade_id: {trade_id}")
            return trade_data
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"CanonicalTradeData deserialization failed for correlation_id {correlation_id}: {e}")
            logger.error(f"Input data keys: {list(data.keys()) if data else 'None'}")
            raise ValueError(f"Failed to deserialize CanonicalTradeData: {e}")


@dataclass
class AgentRegistryEntry:
    """
    Agent registry entry for DynamoDB Model Registry.
    
    This class represents the metadata for an agent registered
    in the system's agent registry.
    """
    agent_id: str                   # Unique agent identifier
    agent_name: str                 # Human-readable agent name
    agent_type: str                 # Agent classification
    runtime_arn: str                # AgentCore runtime ARN
    status: str                     # "active", "inactive", "maintenance"
    version: str                    # Semantic version
    capabilities: List[str]         # List of agent capabilities
    created_at: str                 # ISO 8601 timestamp
    updated_at: str                 # ISO 8601 timestamp
    sop_enabled: bool               # Whether SOP is enabled
    sop_version: Optional[str]      # SOP version if enabled
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB storage."""
        logger.debug(f"Converting AgentRegistryEntry to dict for agent_id: {self.agent_id}")
        logger.debug(f"Agent details - name: {self.agent_name}, type: {self.agent_type}, status: {self.status}, version: {self.version}")
        
        result = {
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
        
        logger.debug(f"AgentRegistryEntry serialization completed for agent_id: {self.agent_id} with {len(self.capabilities)} capabilities")
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentRegistryEntry':
        """Create from dictionary (DynamoDB retrieval)."""
        agent_id = data.get('agent_id', 'unknown')
        logger.debug(f"Deserializing AgentRegistryEntry from dict for agent_id: {agent_id}")
        
        try:
            entry = cls(
                agent_id=data['agent_id'],
                agent_name=data['agent_name'],
                agent_type=data['agent_type'],
                runtime_arn=data['runtime_arn'],
                status=data['status'],
                version=data['version'],
                capabilities=data['capabilities'],
                created_at=data['created_at'],
                updated_at=data['updated_at'],
                sop_enabled=data['sop_enabled'],
                sop_version=data.get('sop_version')
            )
            
            logger.info(f"AgentRegistryEntry deserialization successful for agent_id: {agent_id} - {entry.agent_name} v{entry.version}")
            return entry
            
        except KeyError as e:
            logger.error(f"AgentRegistryEntry deserialization failed for agent_id {agent_id}: missing required field {e}")
            logger.error(f"Available data keys: {list(data.keys()) if data else 'None'}")
            raise ValueError(f"Missing required field in agent registry data: {e}")