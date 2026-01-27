"""
Unit tests for agents router.

Tests the agent filtering functionality to ensure only ACTIVE agents are returned.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.models import AgentStatus


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_service():
    """Mock DynamoDB service."""
    with patch('app.routers.agents.db_service') as mock_service:
        yield mock_service


class TestAgentStatusFiltering:
    """Test suite for agent filtering by deployment_status."""
    
    def test_filters_only_active_agents(self, client, mock_db_service):
        """
        Test that get_agent_status filters for deployment_status === 'ACTIVE'.
        
        Requirements: 5.1, 5.2
        """
        # Arrange
        now = datetime.now(timezone.utc).isoformat()
        
        # Mix of ACTIVE and INACTIVE agents
        mock_items = [
            {
                "agent_id": "agent_1",
                "agent_type": "PDF_ADAPTER",
                "deployment_status": "ACTIVE",
                "last_heartbeat": now,
                "error_rate": 0.01,
                "avg_latency_ms": 2000,
                "active_tasks": 2
            },
            {
                "agent_id": "agent_2",
                "agent_type": "TRADE_EXTRACTOR",
                "deployment_status": "INACTIVE",  # Should be filtered out
                "last_heartbeat": now,
                "error_rate": 0.01,
                "avg_latency_ms": 2000,
                "active_tasks": 0
            },
            {
                "agent_id": "agent_3",
                "agent_type": "TRADE_MATCHER",
                "deployment_status": "ACTIVE",
                "last_heartbeat": now,
                "error_rate": 0.02,
                "avg_latency_ms": 3000,
                "active_tasks": 1
            },
            {
                "agent_id": "agent_4",
                "agent_type": "EXCEPTION_HANDLER",
                "deployment_status": "PENDING",  # Should be filtered out
                "last_heartbeat": now,
                "error_rate": 0.01,
                "avg_latency_ms": 1500,
                "active_tasks": 0
            }
        ]
        
        mock_db_service.scan_table.return_value = mock_items
        
        # Act
        response = client.get("/api/agents/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should only return 2 ACTIVE agents
        assert len(data) == 2
        
        # Verify all returned agents have ACTIVE deployment_status
        agent_ids = [agent["agentId"] for agent in data]
        assert "agent_1" in agent_ids
        assert "agent_3" in agent_ids
        assert "agent_2" not in agent_ids  # INACTIVE
        assert "agent_4" not in agent_ids  # PENDING
    
    def test_returns_empty_list_when_no_active_agents(self, client, mock_db_service):
        """
        Test that endpoint returns empty list when no ACTIVE agents exist.
        
        Requirements: 5.2, 5.3
        """
        # Arrange
        now = datetime.now(timezone.utc).isoformat()
        
        # All agents are INACTIVE
        mock_items = [
            {
                "agent_id": "agent_1",
                "agent_type": "PDF_ADAPTER",
                "deployment_status": "INACTIVE",
                "last_heartbeat": now,
                "error_rate": 0.01,
                "avg_latency_ms": 2000,
                "active_tasks": 0
            },
            {
                "agent_id": "agent_2",
                "agent_type": "TRADE_EXTRACTOR",
                "deployment_status": "PENDING",
                "last_heartbeat": now,
                "error_rate": 0.01,
                "avg_latency_ms": 2000,
                "active_tasks": 0
            }
        ]
        
        mock_db_service.scan_table.return_value = mock_items
        
        # Act
        response = client.get("/api/agents/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
    
    def test_returns_all_agents_when_all_are_active(self, client, mock_db_service):
        """
        Test that endpoint returns all agents when all have ACTIVE status.
        
        Requirements: 5.1, 5.3
        """
        # Arrange
        now = datetime.now(timezone.utc).isoformat()
        
        # All agents are ACTIVE
        mock_items = [
            {
                "agent_id": f"agent_{i}",
                "agent_type": "PDF_ADAPTER",
                "deployment_status": "ACTIVE",
                "last_heartbeat": now,
                "error_rate": 0.01,
                "avg_latency_ms": 2000,
                "active_tasks": i
            }
            for i in range(6)
        ]
        
        mock_db_service.scan_table.return_value = mock_items
        
        # Act
        response = client.get("/api/agents/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 6
    
    def test_handles_missing_deployment_status_field(self, client, mock_db_service):
        """
        Test that agents without deployment_status field are filtered out.
        
        Requirements: 5.2
        """
        # Arrange
        now = datetime.now(timezone.utc).isoformat()
        
        mock_items = [
            {
                "agent_id": "agent_1",
                "agent_type": "PDF_ADAPTER",
                "deployment_status": "ACTIVE",
                "last_heartbeat": now,
                "error_rate": 0.01,
                "avg_latency_ms": 2000,
                "active_tasks": 1
            },
            {
                "agent_id": "agent_2",
                "agent_type": "TRADE_EXTRACTOR",
                # Missing deployment_status field
                "last_heartbeat": now,
                "error_rate": 0.01,
                "avg_latency_ms": 2000,
                "active_tasks": 0
            }
        ]
        
        mock_db_service.scan_table.return_value = mock_items
        
        # Act
        response = client.get("/api/agents/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should only return agent_1 with ACTIVE status
        assert len(data) == 1
        assert data[0]["agentId"] == "agent_1"


class TestAgentStatusCalculation:
    """Test suite for agent status calculation logic."""
    
    def test_agent_status_offline_when_heartbeat_old(self, client, mock_db_service):
        """
        Test that agent is OFFLINE when heartbeat > 5 minutes old.
        
        Requirements: 9.5
        """
        # Arrange
        old_heartbeat = (datetime.now(timezone.utc) - timedelta(minutes=6)).isoformat()
        
        mock_items = [
            {
                "agent_id": "agent_1",
                "agent_type": "PDF_ADAPTER",
                "deployment_status": "ACTIVE",
                "last_heartbeat": old_heartbeat,
                "error_rate": 0.01,
                "avg_latency_ms": 2000,
                "active_tasks": 0
            }
        ]
        
        mock_db_service.scan_table.return_value = mock_items
        
        # Act
        response = client.get("/api/agents/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "OFFLINE"
    
    def test_agent_status_degraded_when_high_error_rate(self, client, mock_db_service):
        """
        Test that agent is DEGRADED when error rate exceeds threshold.
        
        Requirements: 9.5
        """
        # Arrange
        now = datetime.now(timezone.utc).isoformat()
        
        mock_items = [
            {
                "agent_id": "agent_1",
                "agent_type": "PDF_ADAPTER",
                "deployment_status": "ACTIVE",
                "last_heartbeat": now,
                "error_rate": 0.06,  # Exceeds 2% threshold for PDF_ADAPTER
                "avg_latency_ms": 2000,
                "active_tasks": 1
            }
        ]
        
        mock_db_service.scan_table.return_value = mock_items
        
        # Act
        response = client.get("/api/agents/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "DEGRADED"
    
    def test_agent_status_healthy_under_normal_conditions(self, client, mock_db_service):
        """
        Test that agent is HEALTHY under normal conditions.
        
        Requirements: 9.5
        """
        # Arrange
        now = datetime.now(timezone.utc).isoformat()
        
        mock_items = [
            {
                "agent_id": "agent_1",
                "agent_type": "PDF_ADAPTER",
                "deployment_status": "ACTIVE",
                "last_heartbeat": now,
                "error_rate": 0.01,  # Below threshold
                "avg_latency_ms": 2000,  # Below threshold
                "active_tasks": 2
            }
        ]
        
        mock_db_service.scan_table.return_value = mock_items
        
        # Act
        response = client.get("/api/agents/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "HEALTHY"


class TestAgentStatusErrorHandling:
    """Test suite for error handling in agent status endpoint."""
    
    def test_returns_500_on_dynamodb_error(self, client, mock_db_service):
        """
        Test that endpoint returns 500 when DynamoDB fails.
        
        Requirements: Error Handling
        """
        # Arrange
        mock_db_service.scan_table.side_effect = Exception("DynamoDB connection failed")
        
        # Act
        response = client.get("/api/agents/status")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Failed to fetch agent status" in data["detail"]
    
    def test_handles_empty_table_gracefully(self, client, mock_db_service):
        """
        Test that endpoint handles empty table gracefully.
        
        Requirements: 5.3
        """
        # Arrange
        mock_db_service.scan_table.return_value = []
        
        # Act
        response = client.get("/api/agents/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
