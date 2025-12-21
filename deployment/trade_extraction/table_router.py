"""
Table routing component for the Trade Extraction Agent.

This module implements the TableRouter class that handles routing
trade data to the correct DynamoDB table based on source type,
fixing the critical table routing bug.
"""

import os
from typing import Dict, Any, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class TableRouter:
    """
    Routes trade data to appropriate DynamoDB tables based on source type.
    
    This class implements explicit source_type validation and table routing
    to fix the critical bug where trades were being routed to incorrect tables.
    """
    
    # Valid source types and their corresponding table mappings
    VALID_SOURCE_TYPES = {'BANK', 'COUNTERPARTY'}
    
    def __init__(self):
        """Initialize the TableRouter with environment-based table names."""
        self.bank_table = os.getenv('DYNAMODB_BANK_TABLE', 'BankTradeData')
        self.counterparty_table = os.getenv('DYNAMODB_COUNTERPARTY_TABLE', 'CounterpartyTradeData')
        
        logger.info(f"TableRouter initialized with bank_table={self.bank_table}, "
                   f"counterparty_table={self.counterparty_table}")
    
    def get_target_table(self, source_type: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Get the target DynamoDB table name for the given source type.
        
        Args:
            source_type: The source type ("BANK" or "COUNTERPARTY")
            
        Returns:
            Tuple of (success, table_name, error_message)
            - success: True if routing successful, False otherwise
            - table_name: Target table name if successful, None otherwise
            - error_message: Error description if unsuccessful, None otherwise
        """
        if not source_type:
            error_msg = "source_type cannot be empty or None"
            logger.error(f"Table routing failed: {error_msg}")
            return False, None, error_msg
        
        # Normalize source_type to uppercase for consistency
        normalized_source_type = source_type.upper().strip()
        
        if normalized_source_type not in self.VALID_SOURCE_TYPES:
            error_msg = (f"Invalid source_type '{source_type}'. "
                        f"Must be one of: {', '.join(sorted(self.VALID_SOURCE_TYPES))}")
            logger.error(f"Table routing failed: {error_msg}")
            return False, None, error_msg
        
        # Route to appropriate table
        if normalized_source_type == 'BANK':
            table_name = self.bank_table
        elif normalized_source_type == 'COUNTERPARTY':
            table_name = self.counterparty_table
        else:
            # This should never happen due to validation above, but defensive programming
            error_msg = f"Unexpected source_type after validation: {normalized_source_type}"
            logger.error(f"Table routing failed: {error_msg}")
            return False, None, error_msg
        
        logger.info(f"Successfully routed source_type '{source_type}' to table '{table_name}'")
        return True, table_name, None
    
    def validate_source_type(self, source_type: str) -> Tuple[bool, List[str]]:
        """
        Validate source_type parameter.
        
        Args:
            source_type: The source type to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        logger.debug(f"VALIDATION_START - Validating source_type: '{source_type}'", extra={
            'source_type': source_type,
            'source_type_type': type(source_type).__name__
        })
        
        errors = []
        
        if source_type is None:
            error_msg = "source_type is required"
            errors.append(error_msg)
            logger.warning(f"VALIDATION_ERROR - {error_msg}", extra={
                'validation_type': 'null_check',
                'source_type': source_type
            })
            return False, errors
        
        if not isinstance(source_type, str):
            error_msg = "source_type must be a string"
            errors.append(error_msg)
            logger.warning(f"VALIDATION_ERROR - {error_msg}", extra={
                'validation_type': 'type_check',
                'source_type': source_type,
                'actual_type': type(source_type).__name__
            })
            return False, errors
        
        # Check for empty or whitespace-only strings
        if not source_type.strip():
            error_msg = "source_type is required"
            errors.append(error_msg)
            logger.warning(f"VALIDATION_ERROR - {error_msg}", extra={
                'validation_type': 'empty_check',
                'source_type': repr(source_type),
                'stripped_length': len(source_type.strip())
            })
            return False, errors
        
        normalized_source_type = source_type.upper().strip()
        if normalized_source_type not in self.VALID_SOURCE_TYPES:
            error_msg = f"source_type must be one of: {', '.join(sorted(self.VALID_SOURCE_TYPES))}"
            errors.append(error_msg)
            logger.warning(f"VALIDATION_ERROR - Invalid source_type", extra={
                'validation_type': 'value_check',
                'source_type': source_type,
                'normalized_source_type': normalized_source_type,
                'valid_types': list(self.VALID_SOURCE_TYPES)
            })
        
        is_valid = len(errors) == 0
        logger.debug(f"VALIDATION_COMPLETE - Validation result: {is_valid}", extra={
            'source_type': source_type,
            'is_valid': is_valid,
            'error_count': len(errors),
            'errors': errors
        })
        
        return is_valid, errors
    
    def get_table_mapping(self) -> Dict[str, str]:
        """
        Get the complete source type to table mapping.
        
        Returns:
            Dictionary mapping source types to table names
        """
        return {
            'BANK': self.bank_table,
            'COUNTERPARTY': self.counterparty_table
        }
    
    def get_valid_source_types(self) -> List[str]:
        """
        Get list of valid source types.
        
        Returns:
            List of valid source type strings
        """
        return sorted(list(self.VALID_SOURCE_TYPES))