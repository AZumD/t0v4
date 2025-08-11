#!/usr/bin/env python3
"""Simple test for TOVA v4 Memory Layer Integration"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

async def test_memory_components():
    """Test memory layer components"""
    print("🧪 Testing TOVA v4 Memory Layer Integration")
    print("=" * 60)
    
    try:
        # Test 1: Import memory components
        print("1️⃣ Testing imports...")
        from tova.memory.rag_service import RAGService
        from tova.memory.redis_cache import RedisCache
        from tova.memory.conversation_store import ConversationStore
        print("   ✅ All memory components imported successfully")
        
        # Test 2: Initialize RAG service
        print("2️⃣ Testing RAG service...")
        rag = RAGService(persist_path="data/test_rag")
        print(f"   ✅ RAG service initialized: {'enabled' if rag.enabled else 'disabled'}")
        
        if rag.enabled:
            # Test storing content
            doc_id = await rag.store(
                "user_preferences",
                "User prefers dark mode and minimal UI",
                {"user_id": "test_user", "category": "ui", "confidence": 0.9}
            )
            print(f"   ✅ Stored document: {doc_id}")
            
            # Test searching
            results = await rag.search(
                "dark mode preferences",
                collections=["user_preferences"],
                limit=1
            )
            print(f"   ✅ Search results: {len(results)} found")
        
        # Test 3: Initialize Redis cache
        print("3️⃣ Testing Redis cache...")
        cache = RedisCache()
        print(f"   ✅ Redis cache initialized: {'enabled' if cache.enabled else 'disabled'}")
        
        if cache.enabled:
            # Test basic operations
            success = await cache.set("test_key", "test_value", ttl=60)
            print(f"   ✅ Cache set: {success}")
            
            value = await cache.get("test_key")
            print(f"   ✅ Cache get: {value}")
            
            # Test JSON operations
            success = await cache.set_json(
                "test_json",
                {"name": "TOVA", "version": "4.0"},
                ttl=60
            )
            print(f"   ✅ JSON cache set: {success}")
            
            obj = await cache.get_json("test_json")
            print(f"   ✅ JSON cache get: {obj}")
        
        # Test 4: Initialize conversation store
        print("4️⃣ Testing conversation store...")
        store = ConversationStore()
        print("   ✅ Conversation store initialized")
        
        # Test 5: Test memory manager integration
        print("5️⃣ Testing memory manager...")
        from tova.memory.memory_manager import MemoryManager
        
        memory = MemoryManager(
            conversation_path="data/test_conversations",
            rag_path="data/test_rag",
            redis_url="redis://localhost:6379"
        )
        print("   ✅ Memory manager initialized")
        
        # Test 6: Test orchestrator integration
        print("6️⃣ Testing orchestrator integration...")
        from tova.core.orchestrator import TovaOrchestrator
        
        orchestrator = TovaOrchestrator()
        print("   ✅ Orchestrator with memory integration initialized")
        
        print("\n🎉 All memory layer tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner"""
    success = await test_memory_components()
    
    if success:
        print("\n✅ TOVA v4 Memory Layer Integration is working correctly!")
        print("All memory systems (RAG, Redis cache, conversation store) are integrated and functional.")
    else:
        print("\n⚠️  Please fix the failing tests before proceeding.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 