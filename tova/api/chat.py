"""Chat HTTP endpoints."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(message: dict) -> dict:
    """Echo endpoint placeholder.

    Expects: {"message": "..."}
    """
    content = message.get("message", "")
    return {"received": content, "response": "stub"} 