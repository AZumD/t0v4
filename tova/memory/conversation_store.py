"""Conversation persistence and retrieval system"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import sqlite3
import asyncio
from pathlib import Path
import logging

class ConversationStore:
    def __init__(self, db_path: str = "data/conversations/conversations.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with conversation tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    metadata TEXT  -- JSON metadata
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,  -- 'user', 'tova', 'system'
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,  -- JSON metadata (mood, function, etc.)
                    tokens_used INTEGER,
                    processing_time_ms REAL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation 
                ON messages(conversation_id, timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_user 
                ON conversations(user_id, updated_at DESC)
            """)
    
    async def create_conversation(
        self, 
        user_id: str, 
        conversation_id: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new conversation"""
        def _create():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO conversations (id, user_id, title, metadata)
                    VALUES (?, ?, ?, ?)
                """, (
                    conversation_id,
                    user_id, 
                    title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    json.dumps({})
                ))
                
                return {
                    "id": conversation_id,
                    "user_id": user_id,
                    "title": title,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "message_count": 0
                }
        
        return await asyncio.get_event_loop().run_in_executor(None, _create)
    
    async def store_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
        tokens_used: Optional[int] = None,
        processing_time_ms: Optional[float] = None
    ) -> str:
        """Store a message in the conversation"""
        import uuid
        message_id = str(uuid.uuid4())
        
        def _store():
            with sqlite3.connect(self.db_path) as conn:
                # Insert message
                conn.execute("""
                    INSERT INTO messages 
                    (id, conversation_id, role, content, metadata, tokens_used, processing_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    message_id,
                    conversation_id,
                    role,
                    content,
                    json.dumps(metadata or {}),
                    tokens_used,
                    processing_time_ms
                ))
                
                # Update conversation
                conn.execute("""
                    UPDATE conversations 
                    SET updated_at = CURRENT_TIMESTAMP,
                        message_count = message_count + 1
                    WHERE id = ?
                """, (conversation_id,))
                
                return message_id
        
        return await asyncio.get_event_loop().run_in_executor(None, _store)
    
    async def get_conversation_history(
        self, 
        conversation_id: str,
        limit: Optional[int] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Get messages from a conversation"""
        def _get_history():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = """
                    SELECT role, content, timestamp, metadata, tokens_used, processing_time_ms
                    FROM messages 
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor = conn.execute(query, (conversation_id,))
                messages = []
                
                for row in cursor.fetchall():
                    message = {
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"]
                    }
                    
                    if include_metadata and row["metadata"]:
                        try:
                            message["metadata"] = json.loads(row["metadata"])
                        except json.JSONDecodeError:
                            pass
                    
                    if row["tokens_used"]:
                        message["tokens_used"] = row["tokens_used"]
                    
                    if row["processing_time_ms"]:
                        message["processing_time_ms"] = row["processing_time_ms"]
                    
                    messages.append(message)
                
                return messages
        
        return await asyncio.get_event_loop().run_in_executor(None, _get_history)
    
    async def get_recent_conversations(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent conversations for a user"""
        def _get_recent():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT id, title, created_at, updated_at, message_count
                    FROM conversations
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (user_id, limit))
                
                return [dict(row) for row in cursor.fetchall()]
        
        return await asyncio.get_event_loop().run_in_executor(None, _get_recent)
    
    async def get_conversation_context(
        self,
        conversation_id: str,
        max_messages: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent context for conversation continuation"""
        return await self.get_conversation_history(
            conversation_id, 
            limit=max_messages,
            include_metadata=True
        )
    
    async def update_conversation_title(
        self, 
        conversation_id: str, 
        title: str
    ) -> bool:
        """Update conversation title"""
        def _update():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE conversations 
                    SET title = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (title, conversation_id))
                return cursor.rowcount > 0
        
        return await asyncio.get_event_loop().run_in_executor(None, _update)
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Soft delete a conversation"""
        def _delete():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE conversations 
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (conversation_id,))
                return cursor.rowcount > 0
        
        return await asyncio.get_event_loop().run_in_executor(None, _delete)
    
    async def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """Get statistics for a conversation"""
        def _get_stats():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_messages,
                        SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) as user_messages,
                        SUM(CASE WHEN role = 'tova' THEN 1 ELSE 0 END) as tova_messages,
                        AVG(processing_time_ms) as avg_processing_time,
                        SUM(tokens_used) as total_tokens
                    FROM messages
                    WHERE conversation_id = ?
                """, (conversation_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "total_messages": row[0],
                        "user_messages": row[1], 
                        "tova_messages": row[2],
                        "avg_processing_time_ms": row[3],
                        "total_tokens": row[4]
                    }
                return {}
        
        return await asyncio.get_event_loop().run_in_executor(None, _get_stats) 