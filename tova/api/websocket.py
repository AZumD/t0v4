"""WebSocket endpoints."""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from tova.brains.streaming import WebSocketManager

router = APIRouter(tags=["ws"])
manager = WebSocketManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            text = await websocket.receive_text()
            await manager.broadcast(f"echo:{text}")
    except WebSocketDisconnect:
        manager.disconnect(websocket) 