import pytest
import asyncio
from tova.memory.rag_service import RAGService
from tova.memory.redis_cache import RedisCache
from tova.memory.conversation_store import ConversationStore

@pytest.mark.asyncio
async def test_rag_service():
    """Test RAG service basic operations"""
    rag = RAGService(persist_path="data/test_rag")
    
    # Store a memory
    doc_id = await rag.store(
        "user_preferences",
        "User prefers dark mode and minimal UI",
        {"user_id": "test_user", "category": "ui", "confidence": 0.9}
    )
    assert doc_id
    
    # Search for it
    results = await rag.search(
        "dark mode preferences",
        collections=["user_preferences"],
        limit=1
    )
    assert len(results) > 0
    assert "dark mode" in results[0]["content"].lower()

@pytest.mark.asyncio
async def test_redis_cache():
    """Test Redis cache operations"""
    cache = RedisCache()
    
    if cache.enabled:
        # Test basic get/set
        success = await cache.set("test_key", "test_value", ttl=60)
        assert success
        
        value = await cache.get("test_key")
        assert value == "test_value"
        
        # Test JSON operations
        success = await cache.set_json(
            "test_json",
            {"name": "TOVA", "version": "4.0"},
            ttl=60
        )
        assert success
        
        obj = await cache.get_json("test_json")
        assert obj["name"] == "TOVA"
    else:
        pytest.skip("Redis not available")

@pytest.mark.asyncio 
async def test_conversation_continuity():
    """Test conversation persistence across sessions"""
    store = ConversationStore(db_path="data/test_conversations.db")
    rag = RAGService(persist_path="data/test_rag")
    
    # Create conversation
    conv_id = "test_conv_001"
    await store.create_conversation("test_user", conv_id, "Test Conversation")
    
    # Store messages
    await store.store_message(conv_id, "user", "Hello TOVA")
    await store.store_message(conv_id, "tova", "Hey glitchbrain! Ready to fuck shit up?")
    
    # Extract to RAG
    if rag.enabled:
        messages = await store.get_conversation_history(conv_id)
        insights = await rag.extract_conversation_insights(
            messages=messages,
            user_id="test_user",
            conversation_id=conv_id
        )
        
        # Search for context in new session
        context = await rag.get_conversation_context(
            user_id="test_user",
            query="greeting",
            limit=5
        )
        
        # Should find the stored conversation
        assert len(context) > 0 or not rag.enabled

if __name__ == "__main__":
    asyncio.run(test_rag_service())
    asyncio.run(test_redis_cache())
    asyncio.run(test_conversation_continuity()) 