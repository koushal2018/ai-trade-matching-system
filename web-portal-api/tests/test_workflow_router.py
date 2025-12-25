"""
Integration tests for workflow router.

Tests the DynamoDB query functionality for workflow status tracking.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table."""
    with patch('app.routers.workflow.processing_status_table') as mock_table:
        yield mock_table


class TestWorkflowStatusEndpoint:
    """Test suite for GET /workflow/{session_id}/status endpoint."""
    
    def test_query_returns_correct_status_for_existing_session(self, client, mock_dynamodb_table):
        """
        Test that query returns correct status for existing sessionId.
        
        Requirements: 3.1, 3.3
        """
        # Arrange
        session_id = "session-test-123"
        now = datetime.now(timezone.utc).isoformat()
        
        mock_item = {
            "sessionId": session_id,
            "correlationId": "corr_abc123",
            "documentId": "test-doc.pdf",
            "sourceType": "BANK",
            "overallStatus": "processing",
            "pdfAdapter": {
                "status": "success",
                "activity": "Extracted text from PDF document",
                "startedAt": now,
                "completedAt": now,
                "duration": 17.095,
                "tokenUsage": {
                    "inputTokens": 11689,
                    "outputTokens": 2480,
                    "totalTokens": 14169
                }
            },
            "tradeExtraction": {
                "status": "in-progress",
                "activity": "Extracting structured trade data",
                "startedAt": now,
                "tokenUsage": {
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "totalTokens": 0
                }
            },
            "tradeMatching": {
                "status": "pending",
                "activity": "Waiting for extraction",
                "tokenUsage": {
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "totalTokens": 0
                }
            },
            "exceptionManagement": {
                "status": "pending",
                "activity": "No exceptions",
                "tokenUsage": {
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "totalTokens": 0
                }
            },
            "lastUpdated": now
        }
        
        mock_dynamodb_table.get_item.return_value = {"Item": mock_item}
        
        # Act
        response = client.get(f"/api/workflow/{session_id}/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["sessionId"] == session_id
        assert data["overallStatus"] == "processing"
        assert data["agents"]["pdfAdapter"]["status"] == "success"
        assert data["agents"]["tradeExtraction"]["status"] == "in-progress"
        assert data["agents"]["tradeMatching"]["status"] == "pending"
        assert data["agents"]["exceptionManagement"]["status"] == "pending"
        
        # Verify token usage is included in activity
        assert "14,169" in data["agents"]["pdfAdapter"]["activity"]
        
        # Verify DynamoDB was queried correctly
        mock_dynamodb_table.get_item.assert_called_once_with(Key={"sessionId": session_id})
    
    def test_query_returns_pending_status_for_nonexistent_session(self, client, mock_dynamodb_table):
        """
        Test that query returns pending status for non-existent sessionId.
        
        Requirements: 3.2, 3.3
        """
        # Arrange
        session_id = "session-nonexistent-456"
        mock_dynamodb_table.get_item.return_value = {}  # No Item key
        
        # Act
        response = client.get(f"/api/workflow/{session_id}/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["sessionId"] == session_id
        assert data["overallStatus"] == "pending"
        assert data["agents"]["pdfAdapter"]["status"] == "pending"
        assert data["agents"]["tradeExtraction"]["status"] == "pending"
        assert data["agents"]["tradeMatching"]["status"] == "pending"
        assert data["agents"]["exceptionManagement"]["status"] == "pending"
        
        # Verify activities are set correctly
        assert data["agents"]["pdfAdapter"]["activity"] == "Waiting for upload"
        assert data["agents"]["tradeExtraction"]["activity"] == "Waiting for PDF processing"
        
        # Verify DynamoDB was queried
        mock_dynamodb_table.get_item.assert_called_once_with(Key={"sessionId": session_id})
    
    def test_dynamodb_error_handling_returns_500_status(self, client, mock_dynamodb_table):
        """
        Test that DynamoDB error handling returns 500 status.
        
        Requirements: 3.5, 5.5
        """
        # Arrange
        session_id = "session-error-789"
        error_response = {
            'Error': {
                'Code': 'InternalServerError',
                'Message': 'DynamoDB service error'
            }
        }
        mock_dynamodb_table.get_item.side_effect = ClientError(error_response, 'GetItem')
        
        # Act
        response = client.get(f"/api/workflow/{session_id}/status")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Failed to get workflow status" in data["detail"]
        assert "DynamoDB service error" in data["detail"]
    
    def test_response_format_matches_frontend_api_contract(self, client, mock_dynamodb_table):
        """
        Test that response format matches frontend API contract.
        
        Requirements: 3.4
        """
        # Arrange
        session_id = "session-format-test"
        now = datetime.now(timezone.utc).isoformat()
        
        mock_item = {
            "sessionId": session_id,
            "overallStatus": "completed",
            "pdfAdapter": {
                "status": "success",
                "activity": "Complete",
                "startedAt": now,
                "completedAt": now,
                "duration": 10.5,
                "tokenUsage": {"inputTokens": 100, "outputTokens": 50, "totalTokens": 150}
            },
            "tradeExtraction": {
                "status": "success",
                "activity": "Complete",
                "startedAt": now,
                "completedAt": now,
                "duration": 20.3,
                "tokenUsage": {"inputTokens": 200, "outputTokens": 100, "totalTokens": 300}
            },
            "tradeMatching": {
                "status": "success",
                "activity": "Complete",
                "startedAt": now,
                "completedAt": now,
                "duration": 15.7,
                "tokenUsage": {"inputTokens": 150, "outputTokens": 75, "totalTokens": 225}
            },
            "exceptionManagement": {
                "status": "success",
                "activity": "Complete",
                "tokenUsage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}
            },
            "lastUpdated": now
        }
        
        mock_dynamodb_table.get_item.return_value = {"Item": mock_item}
        
        # Act
        response = client.get(f"/api/workflow/{session_id}/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify required top-level fields
        assert "sessionId" in data
        assert "agents" in data
        assert "overallStatus" in data
        assert "lastUpdated" in data
        
        # Verify agents structure
        assert "pdfAdapter" in data["agents"]
        assert "tradeExtraction" in data["agents"]
        assert "tradeMatching" in data["agents"]
        assert "exceptionManagement" in data["agents"]
        
        # Verify agent status fields
        for agent_key in ["pdfAdapter", "tradeExtraction", "tradeMatching", "exceptionManagement"]:
            agent = data["agents"][agent_key]
            assert "status" in agent
            assert "activity" in agent
            assert "subSteps" in agent
            
            # Optional fields
            if agent["status"] in ["success", "error"]:
                # These may or may not be present depending on agent state
                pass
    
    def test_token_usage_metrics_in_response(self, client, mock_dynamodb_table):
        """
        Test that token usage metrics are returned in response.
        
        Requirements: 6.9
        """
        # Arrange
        session_id = "session-tokens-test"
        now = datetime.now(timezone.utc).isoformat()
        
        mock_item = {
            "sessionId": session_id,
            "overallStatus": "processing",
            "pdfAdapter": {
                "status": "success",
                "activity": "Extracted text",
                "tokenUsage": {
                    "inputTokens": 5000,
                    "outputTokens": 1000,
                    "totalTokens": 6000
                }
            },
            "tradeExtraction": {
                "status": "pending",
                "activity": "Waiting",
                "tokenUsage": {
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "totalTokens": 0
                }
            },
            "tradeMatching": {
                "status": "pending",
                "activity": "Waiting",
                "tokenUsage": {
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "totalTokens": 0
                }
            },
            "exceptionManagement": {
                "status": "pending",
                "activity": "Waiting",
                "tokenUsage": {
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "totalTokens": 0
                }
            },
            "lastUpdated": now
        }
        
        mock_dynamodb_table.get_item.return_value = {"Item": mock_item}
        
        # Act
        response = client.get(f"/api/workflow/{session_id}/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify token usage is included in activity for completed agents
        assert "6,000" in data["agents"]["pdfAdapter"]["activity"]
    
    def test_error_field_included_when_agent_fails(self, client, mock_dynamodb_table):
        """
        Test that error field is included when agent fails.
        
        Requirements: 3.3, 3.4
        """
        # Arrange
        session_id = "session-error-test"
        now = datetime.now(timezone.utc).isoformat()
        
        mock_item = {
            "sessionId": session_id,
            "overallStatus": "failed",
            "pdfAdapter": {
                "status": "error",
                "activity": "Text extraction failed",
                "error": "Failed to process PDF: Invalid file format",
                "startedAt": now,
                "completedAt": now,
                "duration": 5.2,
                "tokenUsage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}
            },
            "tradeExtraction": {
                "status": "pending",
                "activity": "Waiting",
                "tokenUsage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}
            },
            "tradeMatching": {
                "status": "pending",
                "activity": "Waiting",
                "tokenUsage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}
            },
            "exceptionManagement": {
                "status": "pending",
                "activity": "Waiting",
                "tokenUsage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}
            },
            "lastUpdated": now
        }
        
        mock_dynamodb_table.get_item.return_value = {"Item": mock_item}
        
        # Act
        response = client.get(f"/api/workflow/{session_id}/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["overallStatus"] == "failed"
        assert data["agents"]["pdfAdapter"]["status"] == "error"
        assert data["agents"]["pdfAdapter"]["error"] == "Failed to process PDF: Invalid file format"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
