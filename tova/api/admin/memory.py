"""Admin endpoints for memory management (placeholder)."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/admin/memory", tags=["admin", "memory"])


@router.get("/stats")
async def stats() -> dict:
    return {"memory": "ok"} 