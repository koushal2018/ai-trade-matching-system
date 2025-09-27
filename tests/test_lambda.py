"""
Unit tests for Lambda S3 event processor.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))

from s3_event_processor import (
    lambda_handler,
    extract_source_type,
    extract_unique_identifier,
    validate_s3_event,
    process_s3_event,
    call_eks_api,
    send_to_dlq,
    get_eks_api_endpoint
)


class TestHelperFunctions:
    """Test helper functions"""

    def test_extract_source_type_bank(self):
        """Test extracting BANK source type"""
        assert extract_source_type("BANK/test.pdf") == "BANK"
        assert extract_source_type("/uploads/BANK/doc.pdf") == "BANK"
        assert extract_source_type("bank/lowercase.pdf") == "BANK"

    def test_extract_source_type_counterparty(self):
        """Test extracting COUNTERPARTY source type"""
        assert extract_source_type("COUNTERPARTY/test.pdf") == "COUNTERPARTY"
        assert extract_source_type("/data/COUNTERPARTY/file.pdf") == "COUNTERPARTY"
        assert extract_source_type("counterparty/lower.pdf") == "COUNTERPARTY"

    def test_extract_source_type_none(self):
        """Test extracting source type when not found"""
        assert extract_source_type("random/file.pdf") is None
        assert extract_source_type("documents/test.pdf") is None

    def test_extract_unique_identifier(self):
        """Test extracting unique identifier"""
        assert extract_unique_identifier("GCS382857_V1.pdf") == "GCS382857"
        assert extract_unique_identifier("trade_12345_20240101.pdf") == "12345"
        assert extract_unique_identifier("simple.pdf") == "simple"
        assert extract_unique_identifier("/path/to/DOC123_V2.pdf") == "DOC123"

    def test_validate_s3_event_valid(self):
        """Test validating valid S3 event"""
        event = {
            "Records": [{
                "eventSource": "aws:s3",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "test.pdf"}
                }
            }]
        }
        assert validate_s3_event(event) == True

    def test_validate_s3_event_invalid(self):
        """Test validating invalid S3 events"""
        assert validate_s3_event({}) == False
        assert validate_s3_event({"Records": []}) == False
        assert validate_s3_event({
            "Records": [{
                "eventSource": "aws:lambda",
                "eventName": "ObjectCreated:Put"
            }]
        }) == False


class TestProcessS3Event:
    """Test S3 event processing"""

    def test_process_s3_event_valid_pdf(self):
        """Test processing valid PDF S3 event"""
        record = {
            "eventTime": "2024-01-01T00:00:00Z",
            "s3": {
                "bucket": {"name": "test-bucket"},
                "object": {
                    "key": "BANK/TEST123_V1.pdf",
                    "size": 1024000
                }
            }
        }

        result = process_s3_event(record)

        assert result is not None
        assert result['s3_bucket'] == "test-bucket"
        assert result['s3_key'] == "BANK/TEST123_V1.pdf"
        assert result['source_type'] == "BANK"
        assert result['unique_identifier'] == "TEST123"

    def test_process_s3_event_skip_non_pdf(self):
        """Test skipping non-PDF files"""
        record = {
            "eventTime": "2024-01-01T00:00:00Z",
            "s3": {
                "bucket": {"name": "test-bucket"},
                "object": {
                    "key": "BANK/document.txt",
                    "size": 1024
                }
            }
        }

        result = process_s3_event(record)
        assert result is None

    @patch.dict(os.environ, {'MAX_FILE_SIZE': '1000'})
    def test_process_s3_event_skip_large_file(self):
        """Test skipping files that are too large"""
        record = {
            "eventTime": "2024-01-01T00:00:00Z",
            "s3": {
                "bucket": {"name": "test-bucket"},
                "object": {
                    "key": "BANK/large.pdf",
                    "size": 2000
                }
            }
        }

        result = process_s3_event(record)
        assert result is None

    def test_process_s3_event_infer_source_type(self):
        """Test inferring source type from bucket/key"""
        record = {
            "eventTime": "2024-01-01T00:00:00Z",
            "s3": {
                "bucket": {"name": "bank-documents"},
                "object": {
                    "key": "uploads/test.pdf",
                    "size": 1024
                }
            }
        }

        result = process_s3_event(record)
        assert result['source_type'] == "BANK"


class TestCallEksApi:
    """Test EKS API calling"""

    @patch('s3_event_processor.get_eks_api_endpoint')
    @patch('s3_event_processor.http')
    def test_call_eks_api_success(self, mock_http, mock_get_endpoint):
        """Test successful EKS API call"""
        mock_get_endpoint.return_value = "http://eks-api.example.com"

        mock_response = Mock()
        mock_response.status = 200
        mock_response.data = json.dumps({
            "processing_id": "PROC123",
            "message": "Success"
        }).encode('utf-8')
        mock_http.request.return_value = mock_response

        processing_request = {
            "s3_bucket": "test",
            "s3_key": "test.pdf",
            "metadata": {"lambda_request_id": "req123"}
        }

        result = call_eks_api(processing_request)

        assert result['success'] == True
        assert result['processing_id'] == "PROC123"
        mock_http.request.assert_called_once()

    @patch('s3_event_processor.get_eks_api_endpoint')
    @patch('s3_event_processor.http')
    def test_call_eks_api_failure(self, mock_http, mock_get_endpoint):
        """Test failed EKS API call"""
        mock_get_endpoint.return_value = "http://eks-api.example.com"

        mock_response = Mock()
        mock_response.status = 500
        mock_response.data = json.dumps({"error": "Internal error"}).encode('utf-8')
        mock_http.request.return_value = mock_response

        result = call_eks_api({"metadata": {}})

        assert result['success'] == False
        assert 'error' in result


class TestSendToDlq:
    """Test DLQ functionality"""

    @patch('boto3.client')
    @patch.dict(os.environ, {'DLQ_NAME': 'test-dlq'})
    def test_send_to_dlq_success(self, mock_boto):
        """Test sending to DLQ successfully"""
        mock_sqs = Mock()
        mock_sqs.get_queue_url.return_value = {'QueueUrl': 'http://queue.url'}
        mock_sqs.send_message.return_value = {'MessageId': 'msg123'}
        mock_boto.return_value = mock_sqs

        event = {"test": "event"}
        send_to_dlq(event, "Test error")

        mock_sqs.send_message.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    def test_send_to_dlq_not_configured(self):
        """Test when DLQ is not configured"""
        # Should not raise exception
        send_to_dlq({"test": "event"}, "Error")


class TestLambdaHandler:
    """Test main Lambda handler"""

    @patch('s3_event_processor.call_eks_api')
    @patch('s3_event_processor.process_s3_event')
    def test_lambda_handler_success(self, mock_process, mock_api):
        """Test successful Lambda execution"""
        event = {
            "Records": [{
                "eventSource": "aws:s3",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "BANK/test.pdf", "size": 1024}
                }
            }]
        }

        mock_process.return_value = {
            "s3_key": "BANK/test.pdf",
            "s3_bucket": "test-bucket",
            "source_type": "BANK"
        }
        mock_api.return_value = {
            "success": True,
            "processing_id": "PROC123"
        }

        class MockContext:
            aws_request_id = "test-id"

        result = lambda_handler(event, MockContext())

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['processed'] == 1
        assert body['failed'] == 0

    @patch('s3_event_processor.send_to_dlq')
    def test_lambda_handler_invalid_event(self, mock_dlq):
        """Test Lambda with invalid event"""
        event = {"invalid": "event"}

        class MockContext:
            aws_request_id = "test-id"

        result = lambda_handler(event, MockContext())

        assert result['statusCode'] == 400
        mock_dlq.assert_called_once()

    @patch('s3_event_processor.call_eks_api')
    @patch('s3_event_processor.process_s3_event')
    @patch('s3_event_processor.send_to_dlq')
    def test_lambda_handler_partial_failure(self, mock_dlq, mock_process, mock_api):
        """Test Lambda with partial failures"""
        event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "eventName": "ObjectCreated:Put",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "BANK/test1.pdf", "size": 1024}
                    }
                },
                {
                    "eventSource": "aws:s3",
                    "eventName": "ObjectCreated:Put",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "BANK/test2.pdf", "size": 1024}
                    }
                }
            ]
        }

        # First record succeeds, second fails
        mock_process.side_effect = [
            {"s3_key": "BANK/test1.pdf", "source_type": "BANK"},
            {"s3_key": "BANK/test2.pdf", "source_type": "BANK"}
        ]
        mock_api.side_effect = [
            {"success": True, "processing_id": "PROC1"},
            {"success": False, "error": "API Error"}
        ]

        class MockContext:
            aws_request_id = "test-id"

        result = lambda_handler(event, MockContext())

        assert result['statusCode'] == 207  # Multi-status
        body = json.loads(result['body'])
        assert body['processed'] == 1
        assert body['failed'] == 1
        assert 'failures' in body


class TestGetEksApiEndpoint:
    """Test EKS API endpoint retrieval"""

    @patch('boto3.client')
    def test_get_eks_api_endpoint_cached(self, mock_boto):
        """Test getting cached endpoint"""
        import s3_event_processor
        s3_event_processor._eks_api_endpoint = "http://cached.endpoint"

        result = get_eks_api_endpoint()
        assert result == "http://cached.endpoint"
        mock_boto.assert_not_called()

    @patch('boto3.client')
    @patch.dict(os.environ, {'EKS_API_ENDPOINT_PARAM': '/test/param'})
    def test_get_eks_api_endpoint_from_ssm(self, mock_boto):
        """Test getting endpoint from SSM"""
        import s3_event_processor
        s3_event_processor._eks_api_endpoint = None

        mock_ssm = Mock()
        mock_ssm.get_parameter.return_value = {
            'Parameter': {'Value': 'http://new.endpoint'}
        }
        mock_boto.return_value = mock_ssm

        result = get_eks_api_endpoint()
        assert result == "http://new.endpoint"
        mock_ssm.get_parameter.assert_called_once_with(Name='/test/param')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])