"""WebSocket streaming primitives (placeholder)."""
from __future__ import annotations

from typing import Set

from fastapi import WebSocket


class WebSocketManager:
    """Tracks connected websockets and supports broadcast."""

    def __init__(self) -> None:
        self.connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)

    async def broadcast(self, message: str) -> None:
        for ws in list(self.connections):
            try:
                await ws.send_text(message)
            except Exception:
                self.disconnect(ws) 