"""
Unit tests for EKS FastAPI application.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock the crew_fixed module before importing eks_main
sys.modules['latest_trade_matching_agent.crew_fixed'] = MagicMock()
sys.modules['mcp'] = MagicMock()
sys.modules['crewai_tools'] = MagicMock()

from src.latest_trade_matching_agent.eks_main import (
    app,
    ProcessingRequest,
    ProcessingResponse,
    processing_status,
    process_document_async,
    send_completion_notification
)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_processing_request():
    """Sample processing request"""
    return ProcessingRequest(
        s3_bucket="test-bucket",
        s3_key="BANK/test.pdf",
        source_type="BANK",
        event_time="2024-01-01T00:00:00Z",
        unique_identifier="TEST123",
        metadata={"test": "data"}
    )


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    @patch('src.latest_trade_matching_agent.eks_main.app.state.s3_client')
    @patch('src.latest_trade_matching_agent.eks_main.app.state.dynamodb_client')
    @patch('src.latest_trade_matching_agent.eks_main.app.state.sns_client')
    def test_readiness_check_success(self, mock_sns, mock_dynamodb, mock_s3, client):
        """Test readiness endpoint when all services are available"""
        mock_s3.list_buckets.return_value = {"Buckets": []}
        mock_dynamodb.list_tables.return_value = {"TableNames": []}
        mock_sns.list_topics.return_value = {"Topics": []}

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'test-arn'}):
            response = client.get("/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["services"]["s3"] == True
            assert data["services"]["dynamodb"] == True
            assert data["services"]["sns"] == True

    @patch('src.latest_trade_matching_agent.eks_main.app.state.s3_client')
    def test_readiness_check_failure(self, mock_s3, client):
        """Test readiness endpoint when services are unavailable"""
        mock_s3.list_buckets.side_effect = Exception("Connection error")

        response = client.get("/ready")
        assert response.status_code == 503


class TestProcessingEndpoint:
    """Test document processing endpoint"""

    @patch('src.latest_trade_matching_agent.eks_main.BackgroundTasks')
    def test_process_valid_request(self, mock_bg_tasks, client, sample_processing_request):
        """Test processing with valid request"""
        mock_bg = Mock()
        mock_bg_tasks.return_value = mock_bg

        response = client.post(
            "/process",
            json=sample_processing_request.dict()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "initiated"
        assert data["unique_identifier"] == "TEST123"
        assert "processing_id" in data

        # Verify background task was added
        mock_bg.add_task.assert_called_once()

    def test_process_invalid_source_type(self, client):
        """Test processing with invalid source type"""
        request = {
            "s3_bucket": "test-bucket",
            "s3_key": "test.pdf",
            "source_type": "INVALID",
            "event_time": "2024-01-01T00:00:00Z",
            "unique_identifier": "TEST123"
        }

        response = client.post("/process", json=request)
        assert response.status_code == 400
        assert "Invalid source_type" in response.json()["detail"]


class TestStatusEndpoints:
    """Test status monitoring endpoints"""

    def test_get_processing_status_exists(self, client):
        """Test getting status for existing processing"""
        processing_id = "TEST123_1234567890"
        processing_status[processing_id] = {
            "status": "processing",
            "message": "In progress",
            "progress": 50
        }

        response = client.get(f"/status/{processing_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["progress"] == 50

    def test_get_processing_status_not_found(self, client):
        """Test getting status for non-existent processing"""
        response = client.get("/status/NONEXISTENT")
        assert response.status_code == 404

    def test_list_processing_status(self, client):
        """Test listing all processing status"""
        # Clear and add test data
        processing_status.clear()
        processing_status["test1"] = {"status": "completed"}
        processing_status["test2"] = {"status": "processing"}

        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["jobs"]) == 2


class TestProcessingAsync:
    """Test async document processing"""

    @pytest.mark.asyncio
    @patch('src.latest_trade_matching_agent.eks_main.MCPServerAdapter')
    @patch('boto3.client')
    async def test_process_document_success(self, mock_boto_client, mock_mcp, sample_processing_request):
        """Test successful document processing"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_s3.download_file.return_value = None
        mock_boto_client.return_value = mock_s3

        # Mock SNS client
        mock_sns = Mock()

        # Mock CrewAI
        mock_crew_instance = Mock()
        mock_crew = Mock()
        mock_crew.kickoff.return_value = "Processing result"
        mock_crew_instance.crew.return_value = mock_crew

        with patch('src.latest_trade_matching_agent.eks_main.LatestTradeMatchingAgent', return_value=mock_crew_instance):
            processing_id = "TEST_123"
            await process_document_async(
                sample_processing_request,
                processing_id,
                mock_s3,
                mock_sns
            )

            # Verify S3 download was called
            mock_s3.download_file.assert_called_once()

            # Verify status was updated to completed
            assert processing_status[processing_id]["status"] == "completed"
            assert processing_status[processing_id]["progress"] == 100

    @pytest.mark.asyncio
    @patch('boto3.client')
    async def test_process_document_failure(self, mock_boto_client, sample_processing_request):
        """Test document processing failure"""
        # Mock S3 client with error
        mock_s3 = Mock()
        mock_s3.download_file.side_effect = Exception("Download failed")
        mock_boto_client.return_value = mock_s3

        mock_sns = Mock()
        processing_id = "TEST_FAIL"

        await process_document_async(
            sample_processing_request,
            processing_id,
            mock_s3,
            mock_sns
        )

        # Verify status was updated to failed
        assert processing_status[processing_id]["status"] == "failed"
        assert processing_status[processing_id]["progress"] == -1
        assert "Download failed" in processing_status[processing_id]["error"]


class TestNotifications:
    """Test notification functionality"""

    @pytest.mark.asyncio
    async def test_send_notification_success(self, sample_processing_request):
        """Test successful notification sending"""
        mock_sns = Mock()
        mock_sns.publish.return_value = {"MessageId": "test-id"}

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'test-topic-arn'}):
            await send_completion_notification(
                sample_processing_request,
                "TEST_123",
                "success",
                mock_sns
            )

            mock_sns.publish.assert_called_once()
            call_args = mock_sns.publish.call_args
            assert call_args.kwargs['TopicArn'] == 'test-topic-arn'
            assert 'success' in call_args.kwargs['Subject'].lower()

    @pytest.mark.asyncio
    async def test_send_notification_no_topic(self, sample_processing_request):
        """Test notification when topic not configured"""
        mock_sns = Mock()

        with patch.dict(os.environ, {}, clear=True):
            await send_completion_notification(
                sample_processing_request,
                "TEST_123",
                "success",
                mock_sns
            )

            # Should not attempt to publish
            mock_sns.publish.assert_not_called()


class TestMetricsEndpoint:
    """Test metrics endpoint"""

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint returns Prometheus format"""
        # Add some test data
        processing_status.clear()
        processing_status["test1"] = {"status": "completed"}
        processing_status["test2"] = {"status": "failed"}
        processing_status["test3"] = {"status": "processing"}

        response = client.get("/metrics")
        assert response.status_code == 200

        metrics = response.text
        assert "trade_processing_total 3" in metrics
        assert "trade_processing_completed 1" in metrics
        assert "trade_processing_failed 1" in metrics
        assert "trade_processing_active 1" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])