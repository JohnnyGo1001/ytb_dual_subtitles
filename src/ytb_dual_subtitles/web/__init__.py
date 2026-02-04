"""Web package for WebSocket and real-time communication."""

from .websocket import WebSocketManager, websocket_endpoint, websocket_manager

__all__ = [
    "WebSocketManager",
    "websocket_endpoint", 
    "websocket_manager",
]
