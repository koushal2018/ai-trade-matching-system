"""
HTTP Interface for Trade Extraction Agent.

This module implements HTTP request/response handling for integration
with the trade_matching_swarm_agentcore_http orchestrator.
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone

try:
    from data_models import TradeExtractionRequest, TradeExtractionResponse
except ImportError:
    # For testing, create minimal classes
    from dataclasses import dataclass
    from typing import Dict, Any, Optional, List, Tuple
    
    @dataclass
    class TradeExtractionRequest:
        document_path: str
        source_type: str
        correlation_id: str
        
        def validate(self) -> Tuple[bool, List[str]]:
            errors = []
            if not self.document_path or not self.document_path.startswith('s3://'):
                errors.append("document_path must be a valid S3 URI")
            if self.source_type not in ['BANK', 'COUNTERPARTY']:
                errors.append("source_type must be either 'BANK' or 'COUNTERPARTY'")
            import re
            if not re.match(r'^corr_[a-f0-9]{12}$', self.correlation_id):
                errors.append("correlation_id must follow format 'corr_[a-f0-9]{12}'")
            return len(errors) == 0, errors
    
    @dataclass
    class TradeExtractionResponse:
        success: bool
        correlation_id: str
        extracted_data: Optional[Dict[str, Any]]
        table_name: Optional[str]
        error_message: Optional[str]
        processing_time_ms: int
        
        def to_dict(self) -> Dict[str, Any]:
            return {
                'success': self.success,
                'correlation_id': self.correlation_id,
                'extracted_data': self.extracted_data,
                'table_name': self.table_name,
                'error_message': self.error_message,
                'processing_time_ms': self.processing_time_ms
            }

logger = logging.getLogger(__name__)


class HTTPInterface:
    """
    Handles HTTP request/response processing for the Trade Extraction Agent.
    
    This class implements request parsing, validation, and standardized
    response formatting with correlation_id propagation.
    """
    
    def __init__(self):
        """Initialize the HTTP interface."""
        logger.info("HTTPInterface initialized")
    
    def parse_request(self, http_payload: Dict[str, Any]) -> Tuple[bool, Optional[TradeExtractionRequest], Optional[str]]:
        """
        Parse and validate HTTP request payload.
        
        Args:
            http_payload: Raw HTTP request payload
            
        Returns:
            Tuple of (success, request_object, error_message)
        """
        try:
            # Extract correlation_id or generate one
            correlation_id = http_payload.get('correlation_id')
            if not correlation_id:
                correlation_id = f"corr_{uuid.uuid4().hex[:12]}"
                logger.info(f"Generated correlation_id: {correlation_id}")
            
            logger.info(f"Parsing HTTP request for correlation_id {correlation_id}")
            
            # Validate required fields
            required_fields = ['document_path', 'source_type']
            missing_fields = []
            
            for field in required_fields:
                if field not in http_payload or not http_payload[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                logger.error(f"Request validation failed for {correlation_id}: {error_msg}")
                return False, None, error_msg
            
            # Create TradeExtractionRequest
            request = TradeExtractionRequest(
                document_path=http_payload['document_path'],
                source_type=http_payload['source_type'],
                correlation_id=correlation_id
            )
            
            # Validate the request
            is_valid, validation_errors = request.validate()
            if not is_valid:
                error_msg = f"Request validation failed: {'; '.join(validation_errors)}"
                logger.error(f"Request validation failed for {correlation_id}: {error_msg}")
                return False, None, error_msg
            
            logger.info(f"Successfully parsed HTTP request for correlation_id {correlation_id}")
            return True, request, None
            
        except Exception as e:
            error_msg = f"Unexpected error parsing HTTP request: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def format_success_response(
        self,
        correlation_id: str,
        extracted_data: Dict[str, Any],
        table_name: str,
        processing_time_ms: int,
        agent_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format successful response for HTTP return.
        
        Args:
            correlation_id: Request correlation ID
            extracted_data: Successfully extracted trade data
            table_name: Target DynamoDB table name
            processing_time_ms: Processing time in milliseconds
            agent_metadata: Optional agent metadata
            
        Returns:
            Formatted HTTP response dictionary
        """
        response = TradeExtractionResponse(
            success=True,
            correlation_id=correlation_id,
            extracted_data=extracted_data,
            table_name=table_name,
            error_message=None,
            processing_time_ms=processing_time_ms
        )
        
        # Convert to dictionary and add standard fields
        response_dict = response.to_dict()
        response_dict.update({
            'agent_name': 'trade-extraction-agent',
            'agent_version': '1.0.0',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'SUCCESS'
        })
        
        # Add agent metadata if provided
        if agent_metadata:
            response_dict['agent_metadata'] = agent_metadata
        
        logger.info(f"Formatted success response for correlation_id {correlation_id}")
        return response_dict
    
    def format_error_response(
        self,
        correlation_id: str,
        error_message: str,
        processing_time_ms: int,
        error_code: Optional[str] = None,
        agent_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format error response for HTTP return.
        
        Args:
            correlation_id: Request correlation ID
            error_message: Error description
            processing_time_ms: Processing time in milliseconds
            error_code: Optional error code for categorization
            agent_metadata: Optional agent metadata
            
        Returns:
            Formatted HTTP error response dictionary
        """
        response = TradeExtractionResponse(
            success=False,
            correlation_id=correlation_id,
            extracted_data=None,
            table_name=None,
            error_message=error_message,
            processing_time_ms=processing_time_ms
        )
        
        # Convert to dictionary and add standard fields
        response_dict = response.to_dict()
        response_dict.update({
            'agent_name': 'trade-extraction-agent',
            'agent_version': '1.0.0',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'ERROR'
        })
        
        # Add error code if provided
        if error_code:
            response_dict['error_code'] = error_code
        
        # Add agent metadata if provided
        if agent_metadata:
            response_dict['agent_metadata'] = agent_metadata
        
        logger.error(f"Formatted error response for correlation_id {correlation_id}: {error_message}")
        return response_dict
    
    def validate_correlation_id(self, correlation_id: str) -> bool:
        """
        Validate correlation_id format.
        
        Args:
            correlation_id: Correlation ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not correlation_id:
            return False
        
        # Should match pattern: corr_[a-f0-9]{12}
        import re
        return bool(re.match(r'^corr_[a-f0-9]{12}$', correlation_id))
    
    def propagate_correlation_id(
        self,
        source_payload: Dict[str, Any],
        target_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Propagate correlation_id from source to target payload.
        
        Args:
            source_payload: Source payload containing correlation_id
            target_payload: Target payload to receive correlation_id
            
        Returns:
            Target payload with correlation_id added
        """
        correlation_id = source_payload.get('correlation_id')
        if correlation_id:
            target_payload['correlation_id'] = correlation_id
            logger.debug(f"Propagated correlation_id {correlation_id} to target payload")
        
        return target_payload
    
    def extract_request_metadata(self, http_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from HTTP request for logging and tracking.
        
        Args:
            http_payload: HTTP request payload
            
        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {
            'request_timestamp': datetime.now(timezone.utc).isoformat(),
            'request_size_bytes': len(json.dumps(http_payload, default=str)),
        }
        
        # Extract optional fields
        optional_fields = [
            'client_id', 'session_id', 'user_agent', 'source_ip',
            'request_id', 'trace_id', 'span_id'
        ]
        
        for field in optional_fields:
            if field in http_payload:
                metadata[field] = http_payload[field]
        
        # Extract document metadata if available
        if 'document_metadata' in http_payload:
            metadata['document_metadata'] = http_payload['document_metadata']
        
        return metadata
    
    def create_audit_payload(
        self,
        request: TradeExtractionRequest,
        response: Dict[str, Any],
        processing_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create audit payload for logging and compliance.
        
        Args:
            request: Original trade extraction request
            response: Agent response
            processing_metadata: Metadata from processing steps
            
        Returns:
            Audit payload dictionary
        """
        audit_payload = {
            'audit_timestamp': datetime.now(timezone.utc).isoformat(),
            'correlation_id': request.correlation_id,
            'operation': 'trade_extraction',
            'agent_name': 'trade-extraction-agent',
            'agent_version': '1.0.0',
            'request_summary': {
                'document_path': request.document_path,
                'source_type': request.source_type,
            },
            'response_summary': {
                'success': response['success'],
                'processing_time_ms': response['processing_time_ms'],
                'table_name': response.get('table_name'),
                'error_message': response.get('error_message')
            },
            'processing_metadata': processing_metadata
        }
        
        # Add extracted data summary (without sensitive details)
        if response.get('extracted_data'):
            extracted_data = response['extracted_data']
            audit_payload['extracted_data_summary'] = {
                'trade_id': extracted_data.get('trade_id'),
                'currency': extracted_data.get('currency'),
                'product_type': extracted_data.get('product_type'),
                'has_notional_amount': 'notional_amount' in extracted_data,
                'has_trade_date': 'trade_date' in extracted_data
            }
        
        return audit_payload
    
    def serialize_response(self, response_dict: Dict[str, Any]) -> str:
        """
        Serialize response dictionary to JSON string.
        
        Args:
            response_dict: Response dictionary to serialize
            
        Returns:
            JSON string representation
        """
        try:
            return json.dumps(response_dict, default=str, indent=2)
        except Exception as e:
            logger.error(f"Failed to serialize response: {str(e)}")
            # Return minimal error response
            error_response = {
                'success': False,
                'error_message': 'Response serialization failed',
                'correlation_id': response_dict.get('correlation_id', 'unknown'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            return json.dumps(error_response, default=str)