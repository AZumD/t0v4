"""Admin endpoints for personality configuration (placeholder)."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/admin/personalities", tags=["admin", "personalities"])


@router.get("")
async def list_personalities() -> dict:
    return {"items": ["tova_core"], "count": 1} 