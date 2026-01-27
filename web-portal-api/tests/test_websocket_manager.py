"""
Unit tests for WebSocket ConnectionManager.

Tests the handle_subscribe method and SUBSCRIBE message handling.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket
from app.services.websocket import ConnectionManager


class TestConnectionManager:
    """Test suite for ConnectionManager WebSocket handling."""
    
    @pytest.fixture
    def manager(self):
        """Create a ConnectionManager instance for testing."""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        ws = AsyncMock(spec=WebSocket)
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_adds_connection_to_session(self, manager, mock_websocket):
        """
        Test that handle_subscribe adds the connection to session-specific list.
        Requirements: 1.5
        """
        session_id = "test-session-123"
        
        # Mock the polling task to prevent actual DynamoDB calls
        with patch.object(manager, '_poll_status', new_callable=AsyncMock):
            await manager.handle_subscribe(mock_websocket, session_id)
        
        # Verify connection was added to session connections
        assert session_id in manager.session_connections
        assert mock_websocket in manager.session_connections[session_id]
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_starts_polling_task(self, manager, mock_websocket):
        """
        Test that handle_subscribe starts polling task if not already running.
        Requirements: 1.5
        """
        session_id = "test-session-456"
        
        # Mock the polling task
        mock_poll = AsyncMock()
        with patch.object(manager, '_poll_status', mock_poll):
            await manager.handle_subscribe(mock_websocket, session_id)
        
        # Verify polling task was created
        assert session_id in manager._polling_tasks
        assert not manager._polling_tasks[session_id].done()
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_sends_confirmation_message(self, manager, mock_websocket):
        """
        Test that handle_subscribe sends SUBSCRIBED confirmation message.
        Requirements: 1.6
        """
        session_id = "test-session-789"
        
        # Mock the polling task to prevent actual DynamoDB calls
        with patch.object(manager, '_poll_status', new_callable=AsyncMock):
            await manager.handle_subscribe(mock_websocket, session_id)
        
        # Verify SUBSCRIBED message was sent
        mock_websocket.send_json.assert_called_once_with({
            "type": "SUBSCRIBED",
            "sessionId": session_id
        })
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_does_not_duplicate_connections(self, manager, mock_websocket):
        """
        Test that handle_subscribe doesn't add duplicate connections.
        """
        session_id = "test-session-duplicate"
        
        # Mock the polling task
        with patch.object(manager, '_poll_status', new_callable=AsyncMock):
            # Subscribe twice with same websocket
            await manager.handle_subscribe(mock_websocket, session_id)
            await manager.handle_subscribe(mock_websocket, session_id)
        
        # Verify connection only appears once
        assert len(manager.session_connections[session_id]) == 1
        assert mock_websocket in manager.session_connections[session_id]
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_reuses_existing_polling_task(self, manager, mock_websocket):
        """
        Test that handle_subscribe reuses existing polling task if still running.
        """
        session_id = "test-session-reuse"
        
        # Create a mock task that's not done
        mock_task = MagicMock()
        mock_task.done.return_value = False
        manager._polling_tasks[session_id] = mock_task
        
        # Mock the polling task creation
        with patch.object(manager, '_poll_status', new_callable=AsyncMock) as mock_poll:
            await manager.handle_subscribe(mock_websocket, session_id)
        
        # Verify new task was NOT created (reused existing)
        mock_poll.assert_not_called()
        assert manager._polling_tasks[session_id] == mock_task
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_restarts_completed_polling_task(self, manager, mock_websocket):
        """
        Test that handle_subscribe restarts polling task if previous one completed.
        """
        session_id = "test-session-restart"
        
        # Create a mock task that's done
        mock_old_task = MagicMock()
        mock_old_task.done.return_value = True
        manager._polling_tasks[session_id] = mock_old_task
        
        # Mock the polling task creation
        with patch.object(manager, '_poll_status', new_callable=AsyncMock):
            await manager.handle_subscribe(mock_websocket, session_id)
        
        # Verify new task was created
        assert manager._polling_tasks[session_id] != mock_old_task
        assert not manager._polling_tasks[session_id].done()
    
    @pytest.mark.asyncio
    async def test_connect_calls_handle_subscribe_when_session_id_provided(self, manager, mock_websocket):
        """
        Test that connect method calls handle_subscribe when session_id is provided.
        """
        session_id = "test-session-connect"
        
        # Mock handle_subscribe
        with patch.object(manager, 'handle_subscribe', new_callable=AsyncMock) as mock_handle:
            await manager.connect(mock_websocket, session_id=session_id)
        
        # Verify handle_subscribe was called
        mock_handle.assert_called_once_with(mock_websocket, session_id)
    
    @pytest.mark.asyncio
    async def test_multiple_clients_can_subscribe_to_same_session(self, manager):
        """
        Test that multiple clients can subscribe to the same session.
        """
        session_id = "test-session-multi"
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        ws1.send_json = AsyncMock()
        ws2.send_json = AsyncMock()
        
        # Mock the polling task
        with patch.object(manager, '_poll_status', new_callable=AsyncMock):
            await manager.handle_subscribe(ws1, session_id)
            await manager.handle_subscribe(ws2, session_id)
        
        # Verify both connections are tracked
        assert len(manager.session_connections[session_id]) == 2
        assert ws1 in manager.session_connections[session_id]
        assert ws2 in manager.session_connections[session_id]
        
        # Verify both received confirmation
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()
