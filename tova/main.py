"""FastAPI application entry point for TOVA v4.

Exposes HTTP and WebSocket endpoints and wires up core subsystems.
"""
from fastapi import FastAPI

from tova.api.chat import router as chat_router
from tova.api.websocket import router as websocket_router
from tova.api.admin import memory as admin_memory
from tova.api.admin import personality as admin_personality
from tova.api.admin import logs as admin_logs
from tova.api.admin import control as admin_control

app = FastAPI(title="TOVA v4", version="0.1.0")

app.include_router(chat_router, prefix="/api")
app.include_router(admin_memory.router, prefix="/api")
app.include_router(admin_personality.router, prefix="/api")
app.include_router(admin_logs.router, prefix="/api")
app.include_router(admin_control.router, prefix="/api")
app.include_router(websocket_router)


@app.get("/health")
def health() -> dict:
    """Liveness endpoint."""
    return {"status": "ok"} 