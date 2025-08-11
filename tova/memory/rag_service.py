"""RAG (Retrieval-Augmented Generation) service using ChromaDB"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
import hashlib

class RAGService:
    def __init__(self, persist_path: str = "data/rag", embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize ChromaDB with persistent storage"""
        self.logger = logging.getLogger(__name__)
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=str(self.persist_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Use sentence-transformers for embeddings (runs locally)
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model
            )
            
            # Initialize collections based on config
            self._init_collections()
            
            self.enabled = True
            self.logger.info(f"✅ ChromaDB initialized at {self.persist_path}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ ChromaDB initialization failed: {e}. RAG disabled.")
            self.client = None
            self.enabled = False
    
    def _init_collections(self):
        """Initialize RAG collections from config"""
        self.collections = {}
        
        # Define collection schemas
        collection_configs = {
            "conversation_history": {
                "description": "Compressed conversation segments",
                "metadata": ["user_id", "conversation_id", "timestamp", "mood", "function", "importance"]
            },
            "user_preferences": {
                "description": "Extracted user preferences and patterns",
                "metadata": ["user_id", "category", "confidence", "timestamp", "source"]
            },
            "important_events": {
                "description": "Key moments and decisions",
                "metadata": ["user_id", "event_type", "timestamp", "impact_score", "related_conversations"]
            },
            "context_threads": {
                "description": "Ongoing conversation threads and topics",
                "metadata": ["user_id", "thread_id", "topic", "last_mentioned", "relevance"]
            },
            "personality_memory": {
                "description": "How user likes to be talked to",
                "metadata": ["user_id", "trait", "examples", "confidence", "last_observed"]
            }
        }
        
        for name, config in collection_configs.items():
            try:
                # Get or create collection
                self.collections[name] = self.client.get_or_create_collection(
                    name=name,
                    embedding_function=self.embedding_function,
                    metadata={"description": config["description"]}
                )
                self.logger.info(f"  📚 Collection '{name}' ready ({self.collections[name].count()} documents)")
            except Exception as e:
                self.logger.error(f"  ❌ Failed to create collection '{name}': {e}")
    
    async def store(
        self,
        collection_name: str,
        content: str,
        metadata: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> str:
        """Store content in a RAG collection"""
        if not self.enabled or collection_name not in self.collections:
            return ""
        
        def _store():
            try:
                # Generate ID if not provided
                if not document_id:
                    # Create deterministic ID from content hash
                    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
                    document_id = f"{metadata.get('user_id', 'default')}_{datetime.now().timestamp()}_{content_hash}"
                
                # Ensure metadata values are JSON-serializable
                clean_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        clean_metadata[key] = value
                    elif isinstance(value, (list, dict)):
                        clean_metadata[key] = json.dumps(value)
                    elif value is None:
                        clean_metadata[key] = ""
                    else:
                        clean_metadata[key] = str(value)
                
                # Add to collection
                self.collections[collection_name].add(
                    documents=[content],
                    metadatas=[clean_metadata],
                    ids=[document_id]
                )
                
                self.logger.debug(f"Stored document {document_id} in {collection_name}")
                return document_id
                
            except Exception as e:
                self.logger.error(f"Failed to store in {collection_name}: {e}")
                return ""
        
        return await asyncio.get_event_loop().run_in_executor(None, _store)
    
    async def search(
        self,
        query: str,
        collections: Optional[List[str]] = None,
        limit: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search across one or more collections"""
        if not self.enabled:
            return []
        
        def _search():
            results = []
            search_collections = collections or list(self.collections.keys())
            
            for coll_name in search_collections:
                if coll_name not in self.collections:
                    continue
                
                try:
                    # Build where clause for metadata filtering
                    where_clause = None
                    if metadata_filter:
                        where_clause = metadata_filter
                    
                    # Query the collection
                    query_result = self.collections[coll_name].query(
                        query_texts=[query],
                        n_results=limit,
                        where=where_clause
                    )
                    
                    # Process results
                    if query_result['documents'] and query_result['documents'][0]:
                        for idx, doc in enumerate(query_result['documents'][0]):
                            distance = query_result['distances'][0][idx] if query_result['distances'] else 0
                            
                            # Convert distance to similarity (1 - normalized_distance)
                            # ChromaDB uses L2 distance by default, typical range 0-2
                            similarity = max(0, 1 - (distance / 2))
                            
                            if similarity >= similarity_threshold:
                                results.append({
                                    'collection': coll_name,
                                    'content': doc,
                                    'metadata': query_result['metadatas'][0][idx] if query_result['metadatas'] else {},
                                    'similarity': similarity,
                                    'id': query_result['ids'][0][idx] if query_result['ids'] else None
                                })
                    
                except Exception as e:
                    self.logger.error(f"Search failed in {coll_name}: {e}")
            
            # Sort by similarity
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
        
        return await asyncio.get_event_loop().run_in_executor(None, _search)
    
    async def extract_conversation_insights(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        conversation_id: str,
        phi_client=None
    ) -> Dict[str, List[str]]:
        """Extract insights from conversation for RAG storage"""
        insights = {
            "preferences": [],
            "important_events": [],
            "personality_traits": [],
            "context_threads": []
        }
        
        if not self.enabled or not messages:
            return insights
        
        # Use Phi for analysis if available
        if phi_client:
            try:
                # Concatenate messages for analysis
                conversation_text = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                    for msg in messages
                ])
                
                # Extract preferences
                preferences = await phi_client.analyze_text(
                    conversation_text,
                    "extract_preferences"
                )
                if preferences:
                    await self.store(
                        "user_preferences",
                        preferences,
                        {
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat(),
                            "category": "extracted",
                            "confidence": 0.8
                        }
                    )
                    insights["preferences"].append(preferences)
                
                # Extract important events
                importance = await phi_client.analyze_text(
                    conversation_text,
                    "rate_importance"
                )
                
                try:
                    importance_score = float(importance)
                except:
                    importance_score = 0.5
                
                if importance_score > 0.7:
                    await self.store(
                        "important_events",
                        conversation_text[:500],  # Store summary
                        {
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat(),
                            "event_type": "conversation",
                            "impact_score": importance_score
                        }
                    )
                    insights["important_events"].append(f"Important conversation (score: {importance_score})")
                
            except Exception as e:
                self.logger.error(f"Phi analysis failed: {e}")
        
        return insights
    
    async def get_conversation_context(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get relevant context for a conversation"""
        if not self.enabled:
            return []
        
        # Search across all collections for this user
        return await self.search(
            query=query,
            collections=None,  # Search all
            limit=limit,
            metadata_filter={"user_id": user_id},
            similarity_threshold=0.6
        )
    
    async def update_user_preference(
        self,
        user_id: str,
        preference: str,
        category: str = "general",
        confidence: float = 0.8
    ):
        """Update or add a user preference"""
        await self.store(
            "user_preferences",
            preference,
            {
                "user_id": user_id,
                "category": category,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
                "source": "extracted"
            }
        )
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get RAG statistics"""
        if not self.enabled:
            return {"enabled": False}
        
        stats = {
            "enabled": True,
            "collections": {}
        }
        
        for name, collection in self.collections.items():
            try:
                stats["collections"][name] = {
                    "count": collection.count(),
                    "name": name
                }
            except:
                stats["collections"][name] = {"count": 0, "error": True}
        
        return stats
    
    async def clear_collection(self, collection_name: str) -> bool:
        """Clear all documents from a collection"""
        if not self.enabled or collection_name not in self.collections:
            return False
        
        try:
            # Delete and recreate the collection
            self.client.delete_collection(collection_name)
            self._init_collections()  # Recreate it
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear collection {collection_name}: {e}")
            return False 