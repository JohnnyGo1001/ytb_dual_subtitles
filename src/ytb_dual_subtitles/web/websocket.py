"""WebSocket manager for real-time communication.

Subtask 4.1-4.5: WebSocket 实时进度服务
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import WebSocket


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self) -> None:
        """Initialize WebSocket manager."""
        self.active_connections: dict[str, WebSocket] = {}

    def add_connection(self, websocket: WebSocket) -> str:
        """Add a WebSocket connection.

        Args:
            websocket: WebSocket connection to add

        Returns:
            Connection ID
        """
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        return connection_id

    def remove_connection(self, connection_id: str) -> None:
        """Remove a WebSocket connection.

        Args:
            connection_id: ID of connection to remove
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients.

        Args:
            message: Message to broadcast
        """
        if not self.active_connections:
            return

        # Send message to all connections
        disconnected = []

        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception:
                # Connection is broken, mark for removal
                disconnected.append(connection_id)

        # Remove disconnected connections
        for connection_id in disconnected:
            self.remove_connection(connection_id)

    async def send_to_connection(self, connection_id: str, message: dict[str, Any]) -> bool:
        """Send message to a specific connection.

        Args:
            connection_id: Target connection ID
            message: Message to send

        Returns:
            True if message was sent successfully, False otherwise
        """
        if connection_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_json(message)
            return True
        except Exception:
            # Connection is broken, remove it
            self.remove_connection(connection_id)
            return False

    async def broadcast_download_progress(self, task_id: str, progress_data: dict[str, Any]) -> None:
        """Broadcast download progress to all clients.

        Args:
            task_id: ID of the download task
            progress_data: Progress information including percentage, speed, eta, etc.
        """
        message = {
            "type": "download_progress",
            "task_id": task_id,
            "progress": progress_data,
            "status": "downloading"
        }
        await self.broadcast(message)

    async def broadcast_task_status(self, task_id: str, status: str, **kwargs) -> None:
        """Broadcast task status update to all clients.

        Args:
            task_id: ID of the task
            status: New status of the task
            **kwargs: Additional status information
        """
        message = {
            "type": "task_status_update",
            "task_id": task_id,
            "status": status,
            **kwargs
        }
        await self.broadcast(message)

    async def broadcast_error(self, task_id: str, error_message: str) -> None:
        """Broadcast error message to all clients.

        Args:
            task_id: ID of the task that errored
            error_message: Error description
        """
        message = {
            "type": "download_error",
            "task_id": task_id,
            "error": error_message,
            "status": "error"
        }
        await self.broadcast(message)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time communication.

    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()
    connection_id = websocket_manager.add_connection(websocket)

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # For now, we just echo back received messages
            # In the future, this could handle client commands
            await websocket.send_json({"type": "echo", "data": data})
    except Exception:
        # Connection closed or error occurred
        pass
    finally:
        websocket_manager.remove_connection(connection_id)