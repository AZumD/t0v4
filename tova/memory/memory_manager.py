"""TOVA v4 Memory Manager - Integrates all memory systems"""
from typing import Dict, List, Any, Optional
import asyncio
import logging
import hashlib
import json
from datetime import datetime
from pathlib import Path

from .conversation_store import ConversationStore
from .rag_service import RAGService
from .cache_service import CacheService

class MemoryManager:
    def __init__(
        self,
        conversation_path: str = "data/conversations",
        rag_path: str = "data/rag",
        redis_url: str = "redis://localhost:6379"
    ):
        """Initialize TOVA v4 memory manager with all subsystems"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize memory subsystems
        self.conversation_store = ConversationStore(conversation_path)
        self.rag_service = RAGService(rag_path)
        self.cache_service = CacheService(redis_url)
        
        self.logger.info("🧠 TOVA v4 Memory Manager initialized")
        self.logger.info(f"  📝 Conversation Store: {conversation_path}")
        self.logger.info(f"  📚 RAG Service: {'✅ Enabled' if self.rag_service.enabled else '❌ Disabled'}")
        self.logger.info(f"  ⚡ Cache Service: {'✅ Enabled' if self.cache_service.enabled else '❌ Disabled'}")
    
    async def store_message(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a message in conversation history and extract insights"""
        # Store in conversation store
        message_id = await self.conversation_store.add_message(
            conversation_id, role, content, metadata or {}
        )
        
        # Cache conversation context for fast access
        await self._update_conversation_cache(user_id, conversation_id)
        
        # Extract insights for RAG storage (async, don't wait)
        asyncio.create_task(
            self._extract_and_store_insights(user_id, conversation_id)
        )
        
        return message_id
    
    async def get_conversation_context(
        self,
        user_id: str,
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get conversation context with caching"""
        # Try cache first
        cache_key = f"context:{user_id}:{conversation_id}"
        cached_context = await self.cache_service.get(cache_key, "conversation")
        
        if cached_context:
            return cached_context[:limit]
        
        # Get from conversation store
        messages = await self.conversation_store.get_messages(conversation_id, limit)
        
        # Cache the result
        await self.cache_service.set_conversation_context(
            user_id, conversation_id, messages
        )
        
        return messages
    
    async def search_memory(
        self,
        user_id: str,
        query: str,
        collections: Optional[List[str]] = None,
        limit: int = 5,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Search across all memory systems"""
        if use_cache:
            # Try cache first
            query_hash = hashlib.md5(query.encode()).hexdigest()
            cached_results = await self.cache_service.get_rag_results(query_hash)
            
            if cached_results:
                # Filter by user_id if needed
                if user_id != "all":
                    cached_results = [
                        r for r in cached_results 
                        if r.get("metadata", {}).get("user_id") == user_id
                    ]
                return cached_results[:limit]
        
        # Search RAG service
        results = await self.rag_service.search(
            query=query,
            collections=collections,
            limit=limit,
            metadata_filter={"user_id": user_id} if user_id != "all" else None
        )
        
        # Cache results
        if use_cache and results:
            query_hash = hashlib.md5(query.encode()).hexdigest()
            await self.cache_service.set_rag_results(query_hash, results)
        
        return results
    
    async def get_user_preferences(
        self,
        user_id: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Get user preferences from RAG and cache"""
        if use_cache:
            cached_prefs = await self.cache_service.get_user_preferences(user_id)
            if cached_prefs:
                return cached_prefs
        
        # Search RAG for user preferences
        results = await self.rag_service.search(
            query="user preferences",
            collections=["user_preferences"],
            metadata_filter={"user_id": user_id},
            limit=10
        )
        
        # Compile preferences
        preferences = {
            "categories": {},
            "last_updated": None,
            "confidence_scores": {}
        }
        
        for result in results:
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            category = metadata.get("category", "general")
            
            if category not in preferences["categories"]:
                preferences["categories"][category] = []
            
            preferences["categories"][category].append(content)
            
            # Track confidence and timestamps
            confidence = metadata.get("confidence", 0.5)
            timestamp = metadata.get("timestamp")
            
            if timestamp:
                if not preferences["last_updated"] or timestamp > preferences["last_updated"]:
                    preferences["last_updated"] = timestamp
            
            if category not in preferences["confidence_scores"]:
                preferences["confidence_scores"][category] = []
            preferences["confidence_scores"][category].append(confidence)
        
        # Cache preferences
        if use_cache:
            await self.cache_service.set_user_preferences(user_id, preferences)
        
        return preferences
    
    async def update_user_preference(
        self,
        user_id: str,
        preference: str,
        category: str = "general",
        confidence: float = 0.8
    ):
        """Update user preference in RAG and cache"""
        # Store in RAG
        await self.rag_service.update_user_preference(
            user_id, preference, category, confidence
        )
        
        # Invalidate cache
        await self.cache_service.delete(f"preferences:{user_id}", "user")
        
        self.logger.info(f"Updated preference for user {user_id}: {category} - {preference}")
    
    async def get_conversation_summary(
        self,
        user_id: str,
        conversation_id: str,
        phi_client=None
    ) -> Dict[str, Any]:
        """Get conversation summary with insights"""
        # Get conversation messages
        messages = await self.conversation_store.get_messages(conversation_id, limit=50)
        
        if not messages:
            return {"summary": "", "insights": {}, "importance": 0.0}
        
        # Extract insights using Phi if available
        insights = await self.rag_service.extract_conversation_insights(
            messages, user_id, conversation_id, phi_client
        )
        
        # Generate summary
        summary = await self._generate_summary(messages, phi_client)
        
        # Calculate importance score
        importance = await self._calculate_importance(messages, insights, phi_client)
        
        return {
            "summary": summary,
            "insights": insights,
            "importance": importance,
            "message_count": len(messages),
            "last_updated": datetime.now().isoformat()
        }
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        stats = {
            "conversation_store": await self.conversation_store.get_stats(),
            "rag_service": await self.rag_service.get_stats(),
            "cache_service": await self.cache_service.get_stats(),
            "total_conversations": 0,
            "total_messages": 0,
            "total_rag_documents": 0
        }
        
        # Get conversation stats
        try:
            conv_stats = await self.conversation_store.get_stats()
            stats["total_conversations"] = conv_stats.get("total_conversations", 0)
            stats["total_messages"] = conv_stats.get("total_messages", 0)
        except:
            pass
        
        # Get RAG stats
        try:
            rag_stats = await self.rag_service.get_stats()
            if rag_stats.get("enabled"):
                total_docs = sum(
                    coll.get("count", 0) 
                    for coll in rag_stats.get("collections", {}).values()
                )
                stats["total_rag_documents"] = total_docs
        except:
            pass
        
        return stats
    
    async def clear_user_data(self, user_id: str) -> bool:
        """Clear all data for a specific user"""
        try:
            # Clear conversation data
            conversations = await self.conversation_store.get_conversations(user_id)
            for conv in conversations:
                await self.conversation_store.delete_conversation(conv["id"])
            
            # Clear RAG data (this would require collection-specific deletion)
            # For now, we'll just clear cache
            await self.cache_service.clear_namespace("conversation")
            await self.cache_service.clear_namespace("user")
            
            self.logger.info(f"Cleared all data for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear user data for {user_id}: {e}")
            return False
    
    async def _update_conversation_cache(
        self,
        user_id: str,
        conversation_id: str
    ):
        """Update conversation cache after new message"""
        try:
            messages = await self.conversation_store.get_messages(conversation_id, limit=20)
            await self.cache_service.set_conversation_context(
                user_id, conversation_id, messages
            )
        except Exception as e:
            self.logger.error(f"Failed to update conversation cache: {e}")
    
    async def _extract_and_store_insights(
        self,
        user_id: str,
        conversation_id: str
    ):
        """Extract insights from conversation and store in RAG"""
        try:
            messages = await self.conversation_store.get_messages(conversation_id, limit=10)
            
            # Store conversation segment in RAG
            if messages:
                conversation_text = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                    for msg in messages
                ])
                
                await self.rag_service.store(
                    "conversation_history",
                    conversation_text,
                    {
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "timestamp": datetime.now().isoformat(),
                        "message_count": len(messages)
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Failed to extract insights: {e}")
    
    async def _generate_summary(
        self,
        messages: List[Dict[str, Any]],
        phi_client=None
    ) -> str:
        """Generate conversation summary"""
        if not messages:
            return ""
        
        # Simple summary for now
        user_messages = [
            msg["content"] for msg in messages 
            if msg.get("role") == "user"
        ]
        
        if not user_messages:
            return "No user messages found"
        
        # Use Phi for better summary if available
        if phi_client:
            try:
                conversation_text = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                    for msg in messages[-10:]  # Last 10 messages
                ])
                
                summary = await phi_client.analyze_text(
                    conversation_text,
                    "summarize_conversation"
                )
                return summary or "Conversation summary unavailable"
                
            except Exception as e:
                self.logger.error(f"Phi summary generation failed: {e}")
        
        # Fallback to simple summary
        return f"Conversation with {len(messages)} messages, {len(user_messages)} from user"
    
    async def _calculate_importance(
        self,
        messages: List[Dict[str, Any]],
        insights: Dict[str, List[str]],
        phi_client=None
    ) -> float:
        """Calculate conversation importance score"""
        if not messages:
            return 0.0
        
        # Base importance on message count and insights
        base_score = min(len(messages) / 20.0, 1.0)  # Normalize to 0-1
        
        # Boost for important events
        if insights.get("important_events"):
            base_score += 0.3
        
        # Boost for preferences
        if insights.get("preferences"):
            base_score += 0.2
        
        # Use Phi for importance analysis if available
        if phi_client:
            try:
                conversation_text = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                    for msg in messages
                ])
                
                importance = await phi_client.analyze_text(
                    conversation_text,
                    "rate_importance"
                )
                
                try:
                    phi_score = float(importance)
                    return min(base_score + phi_score, 1.0)
                except:
                    pass
                    
            except Exception as e:
                self.logger.error(f"Phi importance calculation failed: {e}")
        
        return min(base_score, 1.0)
    
    async def close(self):
        """Close all memory system connections"""
        await self.cache_service.close()
        self.logger.info("Memory manager connections closed") 