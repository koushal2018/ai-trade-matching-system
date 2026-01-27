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


class TestMatchingStatusEndpoint:
    """Test suite for GET /workflow/matching-status endpoint."""
    
    def test_matching_status_with_various_session_states(self, client, mock_dynamodb_table):
        """
        Test matching status calculation with various session states.
        
        Requirements: 6.3, 6.4, 6.5, 6.6
        """
        # Arrange
        now = datetime.now(timezone.utc).isoformat()
        
        mock_items = [
            # Matched trade
            {
                "processing_id": "session-1",
                "overallStatus": "completed",
                "tradeMatching": {"status": "success"},
                "exceptionManagement": {"status": "success"},
                "pdfAdapter": {"status": "success"},
                "tradeExtraction": {"status": "success"}
            },
            # Another matched trade
            {
                "processing_id": "session-2",
                "overallStatus": "completed",
                "tradeMatching": {"status": "success"},
                "exceptionManagement": {"status": "success"},
                "pdfAdapter": {"status": "success"},
                "tradeExtraction": {"status": "success"}
            },
            # Unmatched trade (completed but not success)
            {
                "processing_id": "session-3",
                "overallStatus": "completed",
                "tradeMatching": {"status": "failed"},
                "exceptionManagement": {"status": "success"},
                "pdfAdapter": {"status": "success"},
                "tradeExtraction": {"status": "success"}
            },
            # Pending trade (processing)
            {
                "processing_id": "session-4",
                "overallStatus": "processing",
                "tradeMatching": {"status": "in-progress"},
                "exceptionManagement": {"status": "pending"},
                "pdfAdapter": {"status": "success"},
                "tradeExtraction": {"status": "success"}
            },
            # Pending trade (initializing)
            {
                "processing_id": "session-5",
                "overallStatus": "initializing",
                "tradeMatching": {"status": "pending"},
                "exceptionManagement": {"status": "pending"},
                "pdfAdapter": {"status": "pending"},
                "tradeExtraction": {"status": "pending"}
            },
            # Exception in exceptionManagement
            {
                "processing_id": "session-6",
                "overallStatus": "completed",
                "tradeMatching": {"status": "success"},
                "exceptionManagement": {"status": "error"},
                "pdfAdapter": {"status": "success"},
                "tradeExtraction": {"status": "success"}
            },
            # Exception in agent status
            {
                "processing_id": "session-7",
                "overallStatus": "processing",
                "tradeMatching": {"status": "in-progress"},
                "exceptionManagement": {"status": "pending"},
                "pdfAdapter": {"status": "error"},
                "tradeExtraction": {"status": "success"}
            }
        ]
        
        mock_dynamodb_table.scan.return_value = {"Items": mock_items}
        
        # Act
        response = client.get("/api/workflow/matching-status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify counts
        assert data["matched"] == 2  # session-1, session-2
        assert data["unmatched"] == 1  # session-3
        assert data["pending"] == 2  # session-4, session-5
        assert data["exceptions"] == 2  # session-6, session-7
        
        # Verify DynamoDB was scanned
        mock_dynamodb_table.scan.assert_called_once()
    
    def test_matching_status_with_empty_table(self, client, mock_dynamodb_table):
        """
        Test matching status returns zeros when no sessions exist.
        
        Requirements: 6.8
        """
        # Arrange
        mock_dynamodb_table.scan.return_value = {"Items": []}
        
        # Act
        response = client.get("/api/workflow/matching-status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["matched"] == 0
        assert data["unmatched"] == 0
        assert data["pending"] == 0
        assert data["exceptions"] == 0
    
    def test_matching_status_handles_missing_fields(self, client, mock_dynamodb_table):
        """
        Test matching status handles missing fields gracefully.
        
        Requirements: 6.8
        """
        # Arrange
        mock_items = [
            # Missing tradeMatching field
            {
                "processing_id": "session-1",
                "overallStatus": "completed",
                "exceptionManagement": {"status": "success"}
            },
            # Missing overallStatus field
            {
                "processing_id": "session-2",
                "tradeMatching": {"status": "success"},
                "exceptionManagement": {"status": "success"}
            },
            # Missing exceptionManagement field
            {
                "processing_id": "session-3",
                "overallStatus": "completed",
                "tradeMatching": {"status": "success"}
            }
        ]
        
        mock_dynamodb_table.scan.return_value = {"Items": mock_items}
        
        # Act
        response = client.get("/api/workflow/matching-status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should handle missing fields gracefully
        # session-1: unmatched (completed but no tradeMatching.status)
        # session-2: not counted (no overallStatus)
        # session-3: matched (completed + success, no exception)
        assert data["matched"] == 1
        assert data["unmatched"] == 1
    
    def test_matching_status_dynamodb_error_returns_500(self, client, mock_dynamodb_table):
        """
        Test matching status returns 500 on DynamoDB error.
        
        Requirements: 6.10
        """
        # Arrange
        error_response = {
            'Error': {
                'Code': 'InternalServerError',
                'Message': 'DynamoDB service error'
            }
        }
        mock_dynamodb_table.scan.side_effect = ClientError(error_response, 'Scan')
        
        # Act
        response = client.get("/api/workflow/matching-status")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Failed to get matching status" in data["detail"]
    
    def test_matching_status_counts_all_exception_types(self, client, mock_dynamodb_table):
        """
        Test that exceptions are counted from both exceptionManagement and agent errors.
        
        Requirements: 6.6
        """
        # Arrange
        mock_items = [
            # Exception in exceptionManagement
            {
                "processing_id": "session-1",
                "overallStatus": "completed",
                "tradeMatching": {"status": "success"},
                "exceptionManagement": {"status": "error"},
                "pdfAdapter": {"status": "success"},
                "tradeExtraction": {"status": "success"}
            },
            # Exception in pdfAdapter
            {
                "processing_id": "session-2",
                "overallStatus": "processing",
                "tradeMatching": {"status": "pending"},
                "exceptionManagement": {"status": "pending"},
                "pdfAdapter": {"status": "error"},
                "tradeExtraction": {"status": "success"}
            },
            # Exception in tradeExtraction
            {
                "processing_id": "session-3",
                "overallStatus": "processing",
                "tradeMatching": {"status": "pending"},
                "exceptionManagement": {"status": "pending"},
                "pdfAdapter": {"status": "success"},
                "tradeExtraction": {"status": "error"}
            },
            # Exception in tradeMatching
            {
                "processing_id": "session-4",
                "overallStatus": "processing",
                "tradeMatching": {"status": "error"},
                "exceptionManagement": {"status": "pending"},
                "pdfAdapter": {"status": "success"},
                "tradeExtraction": {"status": "success"}
            },
            # No exceptions
            {
                "processing_id": "session-5",
                "overallStatus": "completed",
                "tradeMatching": {"status": "success"},
                "exceptionManagement": {"status": "success"},
                "pdfAdapter": {"status": "success"},
                "tradeExtraction": {"status": "success"}
            }
        ]
        
        mock_dynamodb_table.scan.return_value = {"Items": mock_items}
        
        # Act
        response = client.get("/api/workflow/matching-status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should count all 4 sessions with exceptions
        assert data["exceptions"] == 4
    
    def test_matching_status_unmatched_includes_non_success_statuses(self, client, mock_dynamodb_table):
        """
        Test that unmatched includes all non-success statuses for completed trades.
        
        Requirements: 6.4
        """
        # Arrange
        mock_items = [
            # Unmatched with failed status
            {
                "processing_id": "session-1",
                "overallStatus": "completed",
                "tradeMatching": {"status": "failed"},
                "exceptionManagement": {"status": "success"}
            },
            # Unmatched with error status
            {
                "processing_id": "session-2",
                "overallStatus": "completed",
                "tradeMatching": {"status": "error"},
                "exceptionManagement": {"status": "success"}
            },
            # Unmatched with pending status (shouldn't happen but test it)
            {
                "processing_id": "session-3",
                "overallStatus": "completed",
                "tradeMatching": {"status": "pending"},
                "exceptionManagement": {"status": "success"}
            },
            # Matched
            {
                "processing_id": "session-4",
                "overallStatus": "completed",
                "tradeMatching": {"status": "success"},
                "exceptionManagement": {"status": "success"}
            }
        ]
        
        mock_dynamodb_table.scan.return_value = {"Items": mock_items}
        
        # Act
        response = client.get("/api/workflow/matching-status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # All non-success completed trades should be unmatched
        assert data["unmatched"] == 3
        assert data["matched"] == 1

