"""
Property-based tests for HTTP Interface.

These tests validate HTTP request processing and correlation ID propagation
using Hypothesis for comprehensive property testing.
"""

import pytest
from hypothesis import given, strategies as st, assume
import json
import os
import sys
from datetime import datetime

# Add the deployment directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'deployment', 'trade_extraction'))

from http_interface import HTTPInterface
try:
    from data_models import TradeExtractionRequest
except ImportError:
    # Create minimal class for testing
    from dataclasses import dataclass
    from typing import Tuple, List
    
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


class TestHTTPInterfaceProperties:
    """Property-based tests for HTTP interface functionality."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.interface = HTTPInterface()
    
    @given(st.dictionaries(
        keys=st.sampled_from(['document_path', 'source_type', 'correlation_id', 'extra_field']),
        values=st.one_of(st.text(), st.integers(), st.none()),
        min_size=0,
        max_size=10
    ))
    def test_property_5_http_request_processing(self, http_payload: dict):
        """
        Property 5: HTTP Request Processing
        
        For any HTTP payload, the interface must:
        1. Parse the request safely without crashing
        2. Validate required fields correctly
        3. Generate correlation_id if missing
        4. Return appropriate success/error status
        5. Provide meaningful error messages for invalid requests
        """
        success, request, error_message = self.interface.parse_request(http_payload)
        
        # Must return proper types
        assert isinstance(success, bool)
        assert error_message is None or isinstance(error_message, str)
        
        if success:
            # Successful parsing must return valid request object
            assert request is not None
            assert hasattr(request, 'document_path')
            assert hasattr(request, 'source_type')
            assert hasattr(request, 'correlation_id')
            
            # Correlation ID must be valid format
            assert self.interface.validate_correlation_id(request.correlation_id)
            
            # Required fields must be present and valid
            assert request.document_path and request.document_path.startswith('s3://')
            assert request.source_type in ['BANK', 'COUNTERPARTY']
        else:
            # Failed parsing must return None request and error message
            assert request is None
            assert error_message is not None
            assert len(error_message) > 0
            
            # Error message should be descriptive
            if 'document_path' not in http_payload or not http_payload.get('document_path'):
                assert 'document_path' in error_message.lower()
            if 'source_type' not in http_payload or not http_payload.get('source_type'):
                assert 'source_type' in error_message.lower()
    
    @given(st.text(min_size=1, max_size=50))
    def test_property_7_correlation_id_propagation(self, correlation_id: str):
        """
        Property 7: Correlation ID Propagation
        
        For any correlation_id, the interface must:
        1. Propagate correlation_id from source to target payloads
        2. Preserve correlation_id format and value
        3. Handle missing correlation_id gracefully
        4. Maintain correlation_id throughout request processing
        """
        # Test propagation with valid correlation_id
        source_payload = {'correlation_id': correlation_id, 'other_field': 'value'}
        target_payload = {'target_field': 'target_value'}
        
        result = self.interface.propagate_correlation_id(source_payload, target_payload)
        
        # Must return target payload with correlation_id added
        assert isinstance(result, dict)
        assert 'correlation_id' in result
        assert result['correlation_id'] == correlation_id
        assert 'target_field' in result  # Original fields preserved
        assert result['target_field'] == 'target_value'
        
        # Test propagation without correlation_id
        source_without_corr = {'other_field': 'value'}
        target_payload_2 = {'target_field': 'target_value'}
        
        result_2 = self.interface.propagate_correlation_id(source_without_corr, target_payload_2)
        
        # Should return target payload unchanged if no correlation_id in source
        assert 'correlation_id' not in result_2 or result_2.get('correlation_id') is None
        assert result_2['target_field'] == 'target_value'
    
    @given(st.text(min_size=1, max_size=100))
    def test_property_5_success_response_formatting(self, correlation_id: str):
        """
        Property 5 Extension: Success response formatting must be consistent.
        """
        extracted_data = {
            'trade_id': 'TEST123',
            'counterparty': 'Test Bank',
            'notional_amount': '1000000',
            'currency': 'USD'
        }
        table_name = 'BankTradeData'
        processing_time_ms = 1500
        
        response = self.interface.format_success_response(
            correlation_id=correlation_id,
            extracted_data=extracted_data,
            table_name=table_name,
            processing_time_ms=processing_time_ms
        )
        
        # Must have required response fields
        assert isinstance(response, dict)
        assert response['success'] is True
        assert response['correlation_id'] == correlation_id
        assert response['extracted_data'] == extracted_data
        assert response['table_name'] == table_name
        assert response['processing_time_ms'] == processing_time_ms
        assert response['error_message'] is None
        
        # Must have standard agent fields
        assert response['agent_name'] == 'trade-extraction-agent'
        assert response['agent_version'] == '1.0.0'
        assert response['status'] == 'SUCCESS'
        assert 'timestamp' in response
        
        # Timestamp must be valid ISO format
        datetime.fromisoformat(response['timestamp'].replace('Z', '+00:00'))
    
    @given(st.text(min_size=1, max_size=100), st.text(min_size=1, max_size=200))
    def test_property_5_error_response_formatting(self, correlation_id: str, error_message: str):
        """
        Property 5 Extension: Error response formatting must be consistent.
        """
        processing_time_ms = 500
        error_code = 'VALIDATION_ERROR'
        
        response = self.interface.format_error_response(
            correlation_id=correlation_id,
            error_message=error_message,
            processing_time_ms=processing_time_ms,
            error_code=error_code
        )
        
        # Must have required error response fields
        assert isinstance(response, dict)
        assert response['success'] is False
        assert response['correlation_id'] == correlation_id
        assert response['error_message'] == error_message
        assert response['processing_time_ms'] == processing_time_ms
        assert response['extracted_data'] is None
        assert response['table_name'] is None
        
        # Must have standard agent fields
        assert response['agent_name'] == 'trade-extraction-agent'
        assert response['agent_version'] == '1.0.0'
        assert response['status'] == 'ERROR'
        assert response['error_code'] == error_code
        assert 'timestamp' in response
        
        # Timestamp must be valid ISO format
        datetime.fromisoformat(response['timestamp'].replace('Z', '+00:00'))
    
    @given(st.one_of(
        st.just('corr_123456789abc'),
        st.just('corr_abcdef123456'),
        st.just('invalid_format'),
        st.just('corr_12345'),  # too short
        st.just('corr_123456789abcdef'),  # too long
        st.just(''),
        st.none()
    ))
    def test_property_7_correlation_id_validation(self, correlation_id):
        """
        Property 7 Extension: Correlation ID validation must be strict.
        """
        is_valid = self.interface.validate_correlation_id(correlation_id)
        
        if correlation_id and isinstance(correlation_id, str):
            # Valid format: corr_[a-f0-9]{12}
            import re
            expected_valid = bool(re.match(r'^corr_[a-f0-9]{12}$', correlation_id))
            assert is_valid == expected_valid
        else:
            # None or non-string should be invalid
            assert is_valid is False
    
    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.floats(), st.booleans()),
        min_size=1,
        max_size=10
    ))
    def test_property_5_request_metadata_extraction(self, http_payload: dict):
        """
        Property 5 Extension: Request metadata extraction must be comprehensive.
        """
        metadata = self.interface.extract_request_metadata(http_payload)
        
        # Must return dictionary with required fields
        assert isinstance(metadata, dict)
        assert 'request_timestamp' in metadata
        assert 'request_size_bytes' in metadata
        
        # Timestamp must be valid
        datetime.fromisoformat(metadata['request_timestamp'].replace('Z', '+00:00'))
        
        # Size must be positive integer
        assert isinstance(metadata['request_size_bytes'], int)
        assert metadata['request_size_bytes'] > 0
        
        # Optional fields should be extracted if present
        optional_fields = ['client_id', 'session_id', 'user_agent', 'source_ip']
        for field in optional_fields:
            if field in http_payload:
                assert field in metadata
                assert metadata[field] == http_payload[field]
    
    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.floats()),
        min_size=1,
        max_size=5
    ))
    def test_property_5_response_serialization(self, response_dict: dict):
        """
        Property 5 Extension: Response serialization must handle all data types.
        """
        # Add required fields to make it a valid response
        response_dict.update({
            'success': True,
            'correlation_id': 'corr_123456789abc',
            'timestamp': datetime.now().isoformat()
        })
        
        serialized = self.interface.serialize_response(response_dict)
        
        # Must return valid JSON string
        assert isinstance(serialized, str)
        assert len(serialized) > 0
        
        # Must be parseable as JSON
        parsed = json.loads(serialized)
        assert isinstance(parsed, dict)
        
        # Required fields must be preserved
        assert parsed['success'] == response_dict['success']
        assert parsed['correlation_id'] == response_dict['correlation_id']
    
    def test_property_audit_payload_creation(self):
        """
        Property: Audit payload creation must include all required fields.
        """
        # Create test request
        request = TradeExtractionRequest(
            document_path='s3://test-bucket/test.pdf',
            source_type='BANK',
            correlation_id='corr_123456789abc'
        )
        
        # Create test response
        response = {
            'success': True,
            'processing_time_ms': 1000,
            'table_name': 'BankTradeData',
            'extracted_data': {'trade_id': 'TEST123'}
        }
        
        # Create test processing metadata
        processing_metadata = {
            'workflow_steps': ['validation', 'extraction', 'routing'],
            'model_used': 'nova-pro'
        }
        
        audit_payload = self.interface.create_audit_payload(
            request, response, processing_metadata
        )
        
        # Must have required audit fields
        assert isinstance(audit_payload, dict)
        assert 'audit_timestamp' in audit_payload
        assert audit_payload['correlation_id'] == request.correlation_id
        assert audit_payload['operation'] == 'trade_extraction'
        assert audit_payload['agent_name'] == 'trade-extraction-agent'
        assert 'request_summary' in audit_payload
        assert 'response_summary' in audit_payload
        assert 'processing_metadata' in audit_payload
        
        # Request summary must include key fields
        req_summary = audit_payload['request_summary']
        assert req_summary['document_path'] == request.document_path
        assert req_summary['source_type'] == request.source_type
        
        # Response summary must include key fields
        resp_summary = audit_payload['response_summary']
        assert resp_summary['success'] == response['success']
        assert resp_summary['processing_time_ms'] == response['processing_time_ms']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])