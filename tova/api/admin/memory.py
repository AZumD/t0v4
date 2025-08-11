"""Admin endpoints for memory management (placeholder)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from ...memory.rag_service import RAGService
from ...memory.redis_cache import RedisCache

router = APIRouter(prefix="/admin/memory", tags=["admin", "memory"])

# Initialize services
rag_service = RAGService()
redis_cache = RedisCache()

@router.get("/stats")
async def get_memory_stats() -> Dict[str, Any]:
    """Get memory system statistics"""
    rag_stats = await rag_service.get_stats() if rag_service.enabled else {"enabled": False}
    cache_stats = await redis_cache.get_stats() if redis_cache.enabled else {"enabled": False}
    
    return {
        "rag": rag_stats,
        "cache": cache_stats
    }

@router.get("/collections")
async def list_collections() -> Dict[str, Any]:
    """List all RAG collections with counts"""
    if not rag_service.enabled:
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    stats = await rag_service.get_stats()
    return stats.get("collections", {})

@router.post("/search")
async def search_memory(
    query: str,
    collections: Optional[List[str]] = None,
    limit: int = 10,
    user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search across RAG collections"""
    if not rag_service.enabled:
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    metadata_filter = {"user_id": user_id} if user_id else None
    
    results = await rag_service.search(
        query=query,
        collections=collections,
        limit=limit,
        metadata_filter=metadata_filter
    )
    
    return results

@router.delete("/collection/{collection_name}/clear")
async def clear_collection(collection_name: str) -> Dict[str, bool]:
    """Clear all documents from a collection"""
    if not rag_service.enabled:
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    success = await rag_service.clear_collection(collection_name)
    return {"success": success}

@router.post("/cache/flush")
async def flush_cache(pattern: str = "*") -> Dict[str, Any]:
    """Flush cache entries matching pattern"""
    if not redis_cache.enabled:
        raise HTTPException(status_code=503, detail="Redis cache not available")
    
    count = await redis_cache.flush_pattern(pattern)
    return {"flushed": count}

@router.get("/cache/keys")
async def list_cache_keys(pattern: str = "*") -> List[str]:
    """List cache keys matching pattern"""
    if not redis_cache.enabled:
        raise HTTPException(status_code=503, detail="Redis cache not available")
    
    return await redis_cache.get_keys_by_pattern(pattern)

@router.delete("/cache/key/{key}")
async def delete_cache_key(key: str) -> Dict[str, bool]:
    """Delete a specific cache key"""
    if not redis_cache.enabled:
        raise HTTPException(status_code=503, detail="Redis cache not available")
    
    success = await redis_cache.delete(key)
    return {"success": success}

@router.get("/health")
async def memory_health_check() -> Dict[str, Any]:
    """Check health of memory systems"""
    health_status = {
        "rag": {
            "enabled": rag_service.enabled,
            "status": "healthy" if rag_service.enabled else "disabled"
        },
        "cache": {
            "enabled": redis_cache.enabled,
            "status": "healthy" if redis_cache.enabled else "disabled"
        }
    }
    
    # Check cache connection if enabled
    if redis_cache.enabled:
        try:
            connected = await redis_cache._ensure_connected()
            health_status["cache"]["status"] = "connected" if connected else "disconnected"
        except Exception as e:
            health_status["cache"]["status"] = f"error: {str(e)}"
    
    return health_status 