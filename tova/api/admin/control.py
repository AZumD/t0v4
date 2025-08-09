"""Admin endpoints for runtime control (placeholder)."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/admin/control", tags=["admin", "control"])


@router.post("/reload")
async def reload_configs() -> dict:
    return {"status": "reloaded"} 