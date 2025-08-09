"""Admin endpoints for logs (placeholder)."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/admin/logs", tags=["admin", "logs"])


@router.get("")
async def list_logs() -> dict:
    return {"items": [], "count": 0} 