"""FastAPI application entry point for TOVA v4.

Exposes HTTP and WebSocket endpoints and wires up core subsystems.
"""
from fastapi import FastAPI

from tova.api.chat import router as chat_router
from tova.api.websocket import router as websocket_router

app = FastAPI(title="TOVA v4", version="0.1.0")

app.include_router(chat_router, prefix="/api")
app.include_router(websocket_router)


@app.get("/health")
def health() -> dict:
    """Liveness endpoint."""
    return {"status": "ok"} 