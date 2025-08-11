"""Redis caching layer for TOVA v4"""
from typing import Optional, Dict, Any, List
import json
import logging
import asyncio
from datetime import datetime, timedelta
import hashlib

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

class RedisCache:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: int = 3600  # 1 hour default
    ):
        self.logger = logging.getLogger(__name__)
        self.default_ttl = default_ttl
        self.client = None
        self.enabled = False
        
        if REDIS_AVAILABLE:
            self._init_redis(host, port, db, password)
        else:
            self.logger.warning("⚠️ Redis not installed. Caching disabled. Install with: pip install redis")
    
    def _init_redis(self, host: str, port: int, db: int, password: Optional[str]):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection will happen on first use (async)
            self.enabled = True
            self.logger.info(f"✅ Redis cache initialized at {host}:{port}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Redis connection failed: {e}. Caching disabled.")
            self.client = None
            self.enabled = False
    
    async def _ensure_connected(self) -> bool:
        """Ensure Redis is connected"""
        if not self.enabled or not self.client:
            return False
        
        try:
            await self.client.ping()
            return True
        except Exception as e:
            self.logger.debug(f"Redis ping failed: {e}")
            self.enabled = False
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not await self._ensure_connected():
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                self.logger.debug(f"Cache hit: {key}")
            return value
        except Exception as e:
            self.logger.debug(f"Cache get failed: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL"""
        if not await self._ensure_connected():
            return False
        
        try:
            ttl = ttl or self.default_ttl
            await self.client.setex(key, ttl, value)
            self.logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            self.logger.debug(f"Cache set failed: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON object from cache"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_json(
        self,
        key: str,
        obj: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set JSON object in cache"""
        try:
            value = json.dumps(obj)
            return await self.set(key, value, ttl)
        except (TypeError, json.JSONEncodeError) as e:
            self.logger.error(f"JSON encoding failed: {e}")
            return False
    
    async def cache_conversation_chunk(
        self,
        conversation_id: str,
        chunk_index: int,
        messages: List[Dict[str, Any]],
        ttl: int = 7200  # 2 hours
    ) -> bool:
        """Cache a conversation chunk for fast retrieval"""
        key = f"conv:{conversation_id}:chunk:{chunk_index}"
        return await self.set_json(key, {"messages": messages}, ttl)
    
    async def get_conversation_chunk(
        self,
        conversation_id: str,
        chunk_index: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached conversation chunk"""
        key = f"conv:{conversation_id}:chunk:{chunk_index}"
        data = await self.get_json(key)
        return data.get("messages") if data else None
    
    async def cache_embedding(
        self,
        text: str,
        embedding: List[float],
        ttl: int = 86400  # 24 hours
    ) -> bool:
        """Cache text embedding to avoid recomputation"""
        # Use hash of text as key
        text_hash = hashlib.md5(text.encode()).hexdigest()
        key = f"embedding:{text_hash}"
        return await self.set_json(key, {"embedding": embedding}, ttl)
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        key = f"embedding:{text_hash}"
        data = await self.get_json(key)
        return data.get("embedding") if data else None
    
    async def cache_phi_analysis(
        self,
        text_hash: str,
        analysis_type: str,
        result: str,
        ttl: int = 3600  # 1 hour
    ) -> bool:
        """Cache Phi analysis results"""
        key = f"phi:{analysis_type}:{text_hash[:16]}"
        return await self.set(key, result, ttl)
    
    async def get_phi_analysis(
        self,
        text_hash: str,
        analysis_type: str
    ) -> Optional[str]:
        """Get cached Phi analysis"""
        key = f"phi:{analysis_type}:{text_hash[:16]}"
        return await self.get(key)
    
    async def increment_counter(
        self,
        key: str,
        amount: int = 1
    ) -> Optional[int]:
        """Increment a counter in cache"""
        if not await self._ensure_connected():
            return None
        
        try:
            return await self.client.incrby(key, amount)
        except Exception:
            return None
    
    async def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get all keys matching a pattern"""
        if not await self._ensure_connected():
            return []
        
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            return keys
        except Exception:
            return []
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        if not await self._ensure_connected():
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception:
            return False
    
    async def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        keys = await self.get_keys_by_pattern(pattern)
        if keys:
            try:
                await self.client.delete(*keys)
                return len(keys)
            except Exception:
                return 0
        return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not await self._ensure_connected():
            return {"enabled": False, "connected": False}
        
        try:
            info = await self.client.info()
            return {
                "enabled": True,
                "connected": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "total_keys": await self.client.dbsize(),
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1)
            }
        except Exception as e:
            return {"enabled": True, "connected": False, "error": str(e)}
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close() 