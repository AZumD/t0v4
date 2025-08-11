"""Redis caching service for TOVA v4 memory layer"""
from typing import Any, Optional, Dict, List
import redis.asyncio as redis
import json
import logging
from datetime import datetime, timedelta
import pickle
import hashlib

class CacheService:
    def __init__(self, redis_url: str = "redis://localhost:6379", default_ttl: int = 3600):
        """Initialize Redis cache service"""
        self.logger = logging.getLogger(__name__)
        self.default_ttl = default_ttl
        
        try:
            # Initialize Redis client
            self.redis = redis.from_url(redis_url, decode_responses=False)
            self.enabled = True
            self.logger.info(f"✅ Redis cache initialized at {redis_url}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Redis initialization failed: {e}. Cache disabled.")
            self.redis = None
            self.enabled = False
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "tova"
    ) -> bool:
        """Set a value in cache with optional TTL"""
        if not self.enabled:
            return False
        
        try:
            full_key = f"{namespace}:{key}"
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value, default=str)
            else:
                serialized = pickle.dumps(value)
            
            # Set with TTL
            ttl_seconds = ttl or self.default_ttl
            await self.redis.setex(full_key, ttl_seconds, serialized)
            
            self.logger.debug(f"Cached {full_key} (TTL: {ttl_seconds}s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cache {key}: {e}")
            return False
    
    async def get(
        self,
        key: str,
        namespace: str = "tova",
        default: Any = None
    ) -> Any:
        """Get a value from cache"""
        if not self.enabled:
            return default
        
        try:
            full_key = f"{namespace}:{key}"
            value = await self.redis.get(full_key)
            
            if value is None:
                return default
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, UnicodeDecodeError):
                try:
                    return pickle.loads(value)
                except:
                    return value.decode('utf-8') if isinstance(value, bytes) else value
                    
        except Exception as e:
            self.logger.error(f"Failed to get {key} from cache: {e}")
            return default
    
    async def delete(self, key: str, namespace: str = "tova") -> bool:
        """Delete a key from cache"""
        if not self.enabled:
            return False
        
        try:
            full_key = f"{namespace}:{key}"
            result = await self.redis.delete(full_key)
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Failed to delete {key} from cache: {e}")
            return False
    
    async def exists(self, key: str, namespace: str = "tova") -> bool:
        """Check if a key exists in cache"""
        if not self.enabled:
            return False
        
        try:
            full_key = f"{namespace}:{key}"
            return await self.redis.exists(full_key) > 0
            
        except Exception as e:
            self.logger.error(f"Failed to check existence of {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int, namespace: str = "tova") -> bool:
        """Set TTL for an existing key"""
        if not self.enabled:
            return False
        
        try:
            full_key = f"{namespace}:{key}"
            return await self.redis.expire(full_key, ttl)
            
        except Exception as e:
            self.logger.error(f"Failed to set TTL for {key}: {e}")
            return False
    
    async def get_ttl(self, key: str, namespace: str = "tova") -> int:
        """Get remaining TTL for a key"""
        if not self.enabled:
            return -1
        
        try:
            full_key = f"{namespace}:{key}"
            return await self.redis.ttl(full_key)
            
        except Exception as e:
            self.logger.error(f"Failed to get TTL for {key}: {e}")
            return -1
    
    async def set_conversation_context(
        self,
        user_id: str,
        conversation_id: str,
        context: Dict[str, Any],
        ttl: int = 1800  # 30 minutes
    ) -> bool:
        """Cache conversation context"""
        key = f"context:{user_id}:{conversation_id}"
        return await self.set(key, context, ttl, "conversation")
    
    async def get_conversation_context(
        self,
        user_id: str,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached conversation context"""
        key = f"context:{user_id}:{conversation_id}"
        return await self.get(key, "conversation")
    
    async def set_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
        ttl: int = 86400  # 24 hours
    ) -> bool:
        """Cache user preferences"""
        key = f"preferences:{user_id}"
        return await self.set(key, preferences, ttl, "user")
    
    async def get_user_preferences(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached user preferences"""
        key = f"preferences:{user_id}"
        return await self.get(key, "user")
    
    async def set_rag_results(
        self,
        query_hash: str,
        results: List[Dict[str, Any]],
        ttl: int = 3600  # 1 hour
    ) -> bool:
        """Cache RAG search results"""
        key = f"rag:{query_hash}"
        return await self.set(key, results, ttl, "search")
    
    async def get_rag_results(
        self,
        query_hash: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached RAG search results"""
        key = f"rag:{query_hash}"
        return await self.get(key, "search")
    
    async def set_prompt_cache(
        self,
        prompt_hash: str,
        prompt_data: Dict[str, Any],
        ttl: int = 7200  # 2 hours
    ) -> bool:
        """Cache assembled prompts"""
        key = f"prompt:{prompt_hash}"
        return await self.set(key, prompt_data, ttl, "prompt")
    
    async def get_prompt_cache(
        self,
        prompt_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached prompt data"""
        key = f"prompt:{prompt_hash}"
        return await self.get(key, "prompt")
    
    async def set_session_data(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: int = 1800  # 30 minutes
    ) -> bool:
        """Cache session data"""
        key = f"session:{session_id}"
        return await self.set(key, data, ttl, "session")
    
    async def get_session_data(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached session data"""
        key = f"session:{session_id}"
        return await self.get(key, "session")
    
    async def clear_namespace(self, namespace: str) -> bool:
        """Clear all keys in a namespace"""
        if not self.enabled:
            return False
        
        try:
            pattern = f"{namespace}:*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                await self.redis.delete(*keys)
                self.logger.info(f"Cleared {len(keys)} keys from namespace '{namespace}'")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear namespace '{namespace}': {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = await self.redis.info()
            
            stats = {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
            
            # Calculate hit rate
            hits = stats["keyspace_hits"]
            misses = stats["keyspace_misses"]
            total = hits + misses
            stats["hit_rate"] = (hits / total * 100) if total > 0 else 0
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}
    
    async def health_check(self) -> bool:
        """Check if Redis is healthy"""
        if not self.enabled:
            return False
        
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.enabled and self.redis:
            await self.redis.close()
            self.logger.info("Redis connection closed") 