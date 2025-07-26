"""
Data Format Adapters for Enhanced AI Reconciliation

This module provides adapters for different data formats including:
- Email processing
- Electronic trading data
- Exchange confirmations
- SWIFT messages
- PDF documents
- CSV/Excel files
- JSON/XML data
"""

import logging
import re
import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import email
import email.policy
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from pathlib import Path

from .extensible_architecture import PluginInterface, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


# ============================================================================
# Base Data Format Adapter
# ============================================================================

@dataclass
class ProcessingResult:
    """Result from data format processing"""
    success: bool
    extracted_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DataFormatAdapter(PluginInterface):
    """Base class for data format adapters"""
    
    def __init__(self):
        super().__init__()
        self.supported_formats: List[str] = []
        self.extraction_patterns: Dict[str, str] = {}
        
    @abstractmethod
    async def process_data(self, data: Union[str, bytes, Dict[str, Any]]) -> ProcessingResult:
        """Process data and extract structured information"""
        pass
    
    @abstractmethod
    def detect_format(self, data: Union[str, bytes]) -> bool:
        """Detect if this adapter can handle the given data format"""
        pass
    
    def add_extraction_pattern(self, field_name: str, pattern: str):
        """Add a regex pattern for extracting specific fields"""
        self.extraction_patterns[field_name] = pattern
        
    def extract_with_patterns(self, text: str) -> Dict[str, Any]:
        """Extract fields using configured patterns"""
        extracted = {}
        for field_name, pattern in self.extraction_patterns.items():
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    extracted[field_name] = match.group(1) if match.groups() else match.group(0)
            except Exception as e:
                logger.warning(f"Pattern extraction failed for {field_name}: {e}")
        return extracted


# ============================================================================
# Email Data Format Adapter
# ============================================================================

class EmailAdapter(DataFormatAdapter):
    """Adapter for processing email messages containing trade data"""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ['email', 'eml', 'msg']
        
        # Common email patterns for trade data
        self.extraction_patterns.update({
            'trade_id': r'(?:Trade\s*ID|Reference|Deal\s*ID):\s*([A-Z0-9-]+)',
            'trade_date': r'(?:Trade\s*Date|Value\s*Date):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'counterparty': r'(?:Counterparty|Client):\s*([^\n\r]+)',
            'notional': r'(?:Notional|Amount):\s*([0-9,]+(?:\.\d{2})?)',
            'currency': r'(?:Currency|CCY):\s*([A-Z]{3})',
            'product_type': r'(?:Product|Instrument):\s*([^\n\r]+)',
            'maturity_date': r'(?:Maturity|Settlement\s*Date):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        })
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="email_adapter",
            version="1.0.0",
            plugin_type=PluginType.DATA_FORMAT_ADAPTER,
            description="Adapter for processing email messages containing trade data",
            author="Enhanced AI Reconciliation System",
            supported_regions=["global"]
        )
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize email adapter with configuration"""
        try:
            # Add custom patterns from config
            custom_patterns = config.get('extraction_patterns', {})
            self.extraction_patterns.update(custom_patterns)
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize email adapter: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup email adapter resources"""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate email adapter configuration"""
        return True  # Email adapter has minimal config requirements
    
    def detect_format(self, data: Union[str, bytes]) -> bool:
        """Detect if data is an email format"""
        if isinstance(data, bytes):
            try:
                data = data.decode('utf-8', errors='ignore')
            except:
                return False
                
        # Check for email headers
        email_indicators = [
            'From:', 'To:', 'Subject:', 'Date:',
            'Message-ID:', 'Content-Type:', 'MIME-Version:'
        ]
        
        return any(indicator in data for indicator in email_indicators)
    
    async def process_data(self, data: Union[str, bytes, Dict[str, Any]]) -> ProcessingResult:
        """Process email data and extract trade information"""
        try:
            if isinstance(data, dict):
                # Already parsed email data
                email_content = data.get('body', '')
                headers = data.get('headers', {})
            else:
                # Parse raw email data
                if isinstance(data, bytes):
                    data = data.decode('utf-8', errors='ignore')
                    
                msg = email.message_from_string(data, policy=email.policy.default)
                headers = dict(msg.items())
                email_content = self._extract_email_body(msg)
            
            # Extract trade data using patterns
            extracted_data = self.extract_with_patterns(email_content)
            
            # Add email metadata
            metadata = {
                'format_type': 'email',
                'processing_timestamp': datetime.now().isoformat(),
                'headers': headers,
                'content_length': len(email_content)
            }
            
            # Additional email-specific extractions
            extracted_data.update({
                'sender': headers.get('From', ''),
                'recipient': headers.get('To', ''),
                'subject': headers.get('Subject', ''),
                'email_date': headers.get('Date', ''),
                'message_id': headers.get('Message-ID', '')
            })
            
            return ProcessingResult(
                success=True,
                extracted_data=extracted_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Email processing failed: {e}")
            return ProcessingResult(
                success=False,
                extracted_data={},
                errors=[str(e)]
            )
    
    def _extract_email_body(self, msg) -> str:
        """Extract text body from email message"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_content()
        else:
            if msg.get_content_type() == "text/plain":
                body = msg.get_content()
                
        return body


# ============================================================================
# Electronic Trading Data Adapter
# ============================================================================

class ElectronicTradingAdapter(DataFormatAdapter):
    """Adapter for electronic trading data formats (FIX, proprietary formats)"""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ['fix', 'electronic_trading', 'eti', 'trading_system']
        
        # FIX message field mappings
        self.fix_field_map = {
            '11': 'order_id',
            '17': 'execution_id',
            '37': 'order_id',
            '38': 'order_quantity',
            '44': 'price',
            '54': 'side',
            '55': 'symbol',
            '60': 'transaction_time',
            '75': 'trade_date',
            '150': 'execution_type',
            '151': 'leaves_quantity',
            '14': 'cumulative_quantity',
            '6': 'average_price'
        }
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="electronic_trading_adapter",
            version="1.0.0",
            plugin_type=PluginType.DATA_FORMAT_ADAPTER,
            description="Adapter for electronic trading data formats including FIX messages",
            author="Enhanced AI Reconciliation System",
            supported_regions=["global"]
        )
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize electronic trading adapter"""
        try:
            # Load custom field mappings
            custom_mappings = config.get('field_mappings', {})
            self.fix_field_map.update(custom_mappings)
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize electronic trading adapter: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup adapter resources"""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate adapter configuration"""
        return True
    
    def detect_format(self, data: Union[str, bytes]) -> bool:
        """Detect electronic trading data format"""
        if isinstance(data, bytes):
            try:
                data = data.decode('utf-8', errors='ignore')
            except:
                return False
        
        # Check for FIX message format
        if re.match(r'8=FIX\.\d+\.\d+', data):
            return True
            
        # Check for other electronic trading indicators
        trading_indicators = [
            'ExecutionReport', 'NewOrderSingle', 'OrderCancelRequest',
            'TradingSessionID', 'SecurityID', 'OrderQty'
        ]
        
        return any(indicator in data for indicator in trading_indicators)
    
    async def process_data(self, data: Union[str, bytes, Dict[str, Any]]) -> ProcessingResult:
        """Process electronic trading data"""
        try:
            if isinstance(data, dict):
                # Already structured data
                extracted_data = data
            else:
                if isinstance(data, bytes):
                    data = data.decode('utf-8', errors='ignore')
                
                # Parse based on format
                if data.startswith('8=FIX'):
                    extracted_data = self._parse_fix_message(data)
                else:
                    extracted_data = self._parse_generic_trading_data(data)
            
            metadata = {
                'format_type': 'electronic_trading',
                'processing_timestamp': datetime.now().isoformat(),
                'data_length': len(str(data))
            }
            
            return ProcessingResult(
                success=True,
                extracted_data=extracted_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Electronic trading data processing failed: {e}")
            return ProcessingResult(
                success=False,
                extracted_data={},
                errors=[str(e)]
            )
    
    def _parse_fix_message(self, fix_message: str) -> Dict[str, Any]:
        """Parse FIX protocol message"""
        extracted = {}
        
        # Split FIX message into fields
        fields = fix_message.split('\x01')  # FIX uses SOH (Start of Header) as delimiter
        
        for field in fields:
            if '=' in field:
                tag, value = field.split('=', 1)
                if tag in self.fix_field_map:
                    extracted[self.fix_field_map[tag]] = value
                else:
                    extracted[f'fix_tag_{tag}'] = value
        
        return extracted
    
    def _parse_generic_trading_data(self, data: str) -> Dict[str, Any]:
        """Parse generic electronic trading data"""
        extracted = {}
        
        # Use regex patterns to extract common trading fields
        patterns = {
            'order_id': r'(?:OrderID|Order\s*ID):\s*([A-Z0-9-]+)',
            'symbol': r'(?:Symbol|Instrument):\s*([A-Z0-9]+)',
            'quantity': r'(?:Quantity|Qty):\s*([0-9,]+)',
            'price': r'(?:Price):\s*([0-9.]+)',
            'side': r'(?:Side):\s*(BUY|SELL|B|S)',
            'execution_time': r'(?:ExecutionTime|Time):\s*([0-9T:-]+)',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, data, re.IGNORECASE)
            if match:
                extracted[field] = match.group(1)
        
        return extracted


# ============================================================================
# Exchange Confirmation Adapter
# ============================================================================

class ExchangeConfirmationAdapter(DataFormatAdapter):
    """Adapter for exchange confirmation messages"""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ['exchange_confirmation', 'trade_confirmation', 'settlement']
        
        # Common confirmation patterns
        self.extraction_patterns.update({
            'confirmation_id': r'(?:Confirmation|Confirm)\s*(?:ID|Number):\s*([A-Z0-9-]+)',
            'trade_reference': r'(?:Trade\s*Ref|Reference):\s*([A-Z0-9-]+)',
            'execution_venue': r'(?:Exchange|Venue):\s*([A-Z]+)',
            'settlement_date': r'(?:Settlement|Value)\s*Date:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'clearing_member': r'(?:Clearing\s*Member|CM):\s*([^\n\r]+)',
            'commission': r'(?:Commission|Fee):\s*([0-9.]+)',
            'net_amount': r'(?:Net\s*Amount|Net):\s*([0-9,]+(?:\.\d{2})?)',
        })
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="exchange_confirmation_adapter",
            version="1.0.0",
            plugin_type=PluginType.DATA_FORMAT_ADAPTER,
            description="Adapter for exchange confirmation messages",
            author="Enhanced AI Reconciliation System",
            supported_regions=["global"]
        )
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize exchange confirmation adapter"""
        try:
            custom_patterns = config.get('extraction_patterns', {})
            self.extraction_patterns.update(custom_patterns)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize exchange confirmation adapter: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup adapter resources"""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate adapter configuration"""
        return True
    
    def detect_format(self, data: Union[str, bytes]) -> bool:
        """Detect exchange confirmation format"""
        if isinstance(data, bytes):
            try:
                data = data.decode('utf-8', errors='ignore')
            except:
                return False
        
        confirmation_indicators = [
            'Trade Confirmation', 'Settlement Confirmation', 'Execution Report',
            'Clearing Member', 'Exchange:', 'Confirmation ID', 'Settlement Date'
        ]
        
        return any(indicator in data for indicator in confirmation_indicators)
    
    async def process_data(self, data: Union[str, bytes, Dict[str, Any]]) -> ProcessingResult:
        """Process exchange confirmation data"""
        try:
            if isinstance(data, dict):
                extracted_data = data
            else:
                if isinstance(data, bytes):
                    data = data.decode('utf-8', errors='ignore')
                
                extracted_data = self.extract_with_patterns(data)
            
            metadata = {
                'format_type': 'exchange_confirmation',
                'processing_timestamp': datetime.now().isoformat(),
                'data_length': len(str(data))
            }
            
            return ProcessingResult(
                success=True,
                extracted_data=extracted_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Exchange confirmation processing failed: {e}")
            return ProcessingResult(
                success=False,
                extracted_data={},
                errors=[str(e)]
            )


# ============================================================================
# SWIFT Message Adapter
# ============================================================================

class SwiftMessageAdapter(DataFormatAdapter):
    """Adapter for SWIFT message formats"""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ['swift', 'mt', 'mx', 'iso20022']
        
        # SWIFT MT message field mappings
        self.mt_field_map = {
            '20': 'transaction_reference',
            '21': 'related_reference',
            '23B': 'bank_operation_code',
            '32A': 'value_date_currency_amount',
            '50K': 'ordering_customer',
            '59': 'beneficiary_customer',
            '70': 'remittance_information',
            '71A': 'details_of_charges',
            '72': 'sender_to_receiver_information'
        }
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="swift_message_adapter",
            version="1.0.0",
            plugin_type=PluginType.DATA_FORMAT_ADAPTER,
            description="Adapter for SWIFT message formats (MT and MX)",
            author="Enhanced AI Reconciliation System",
            supported_regions=["global"]
        )
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize SWIFT message adapter"""
        try:
            custom_mappings = config.get('field_mappings', {})
            self.mt_field_map.update(custom_mappings)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SWIFT adapter: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup adapter resources"""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate adapter configuration"""
        return True
    
    def detect_format(self, data: Union[str, bytes]) -> bool:
        """Detect SWIFT message format"""
        if isinstance(data, bytes):
            try:
                data = data.decode('utf-8', errors='ignore')
            except:
                return False
        
        # Check for SWIFT MT format
        if re.match(r'\{1:[A-Z]{12}\d{4}\}', data):
            return True
        
        # Check for SWIFT MX format (ISO 20022)
        if '<Document xmlns=' in data and 'iso:std:iso:20022' in data:
            return True
        
        # Check for other SWIFT indicators
        swift_indicators = [':20:', ':21:', ':23B:', ':32A:', ':50K:', ':59:']
        return any(indicator in data for indicator in swift_indicators)
    
    async def process_data(self, data: Union[str, bytes, Dict[str, Any]]) -> ProcessingResult:
        """Process SWIFT message data"""
        try:
            if isinstance(data, dict):
                extracted_data = data
            else:
                if isinstance(data, bytes):
                    data = data.decode('utf-8', errors='ignore')
                
                if data.startswith('<Document'):
                    extracted_data = self._parse_mx_message(data)
                else:
                    extracted_data = self._parse_mt_message(data)
            
            metadata = {
                'format_type': 'swift',
                'processing_timestamp': datetime.now().isoformat(),
                'data_length': len(str(data))
            }
            
            return ProcessingResult(
                success=True,
                extracted_data=extracted_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"SWIFT message processing failed: {e}")
            return ProcessingResult(
                success=False,
                extracted_data={},
                errors=[str(e)]
            )
    
    def _parse_mt_message(self, mt_message: str) -> Dict[str, Any]:
        """Parse SWIFT MT message"""
        extracted = {}
        
        # Extract message type
        mt_type_match = re.search(r'\{2:[A-Z]{4}(\d{3})', mt_message)
        if mt_type_match:
            extracted['message_type'] = f"MT{mt_type_match.group(1)}"
        
        # Extract fields using patterns
        for field_tag, field_name in self.mt_field_map.items():
            pattern = f':{field_tag}:([^:]*?)(?=:|$)'
            match = re.search(pattern, mt_message, re.DOTALL)
            if match:
                extracted[field_name] = match.group(1).strip()
        
        return extracted
    
    def _parse_mx_message(self, mx_message: str) -> Dict[str, Any]:
        """Parse SWIFT MX (ISO 20022) message"""
        extracted = {}
        
        try:
            root = ET.fromstring(mx_message)
            
            # Extract common fields from XML structure
            # This is a simplified extraction - real implementation would be more comprehensive
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    extracted[tag_name] = elem.text.strip()
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse MX message XML: {e}")
        
        return extracted


# ============================================================================
# Data Format Adapter Registry
# ============================================================================

class DataFormatAdapterRegistry:
    """Registry for managing data format adapters"""
    
    def __init__(self):
        self._adapters: List[DataFormatAdapter] = []
        self._initialized_adapters: Dict[str, DataFormatAdapter] = {}
        
    def register_adapter(self, adapter: DataFormatAdapter):
        """Register a data format adapter"""
        self._adapters.append(adapter)
        logger.info(f"Registered data format adapter: {adapter.__class__.__name__}")
        
    async def initialize_adapters(self, config: Dict[str, Any]):
        """Initialize all registered adapters"""
        for adapter in self._adapters:
            try:
                adapter_config = config.get(adapter.__class__.__name__, {})
                if await adapter.initialize(adapter_config):
                    self._initialized_adapters[adapter.__class__.__name__] = adapter
                    logger.info(f"Initialized adapter: {adapter.__class__.__name__}")
                else:
                    logger.error(f"Failed to initialize adapter: {adapter.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error initializing adapter {adapter.__class__.__name__}: {e}")
    
    async def process_data(self, data: Union[str, bytes, Dict[str, Any]]) -> Optional[ProcessingResult]:
        """Process data using the appropriate adapter"""
        for adapter in self._initialized_adapters.values():
            try:
                if adapter.detect_format(data):
                    logger.info(f"Processing data with {adapter.__class__.__name__}")
                    return await adapter.process_data(data)
            except Exception as e:
                logger.error(f"Error processing data with {adapter.__class__.__name__}: {e}")
                continue
        
        logger.warning("No suitable adapter found for data format")
        return None
    
    async def cleanup_all(self):
        """Cleanup all adapters"""
        for adapter in self._initialized_adapters.values():
            try:
                await adapter.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up adapter: {e}")
        
        self._initialized_adapters.clear()


# ============================================================================
# Built-in Adapter Registration
# ============================================================================

def register_builtin_adapters(registry: DataFormatAdapterRegistry):
    """Register all built-in data format adapters"""
    registry.register_adapter(EmailAdapter())
    registry.register_adapter(ElectronicTradingAdapter())
    registry.register_adapter(ExchangeConfirmationAdapter())
    registry.register_adapter(SwiftMessageAdapter())


# Global registry instance
data_format_registry = DataFormatAdapterRegistry()
register_builtin_adapters(data_format_registry)