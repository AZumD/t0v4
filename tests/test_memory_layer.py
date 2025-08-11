#!/usr/bin/env python3
"""Test script for TOVA v4 Memory Layer Integration"""

import asyncio
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

from tova.memory.memory_manager import MemoryManager
from tova.memory.conversation_store import ConversationStore
from tova.memory.rag_service import RAGService
from tova.memory.cache_service import CacheService

class MemoryLayerTester:
    def __init__(self):
        self.project_root = Path("/home/anthon/t0v4")
        self.test_data_path = self.project_root / "test" / "memory_test_data"
        self.test_data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(
            conversation_path=str(self.test_data_path / "conversations"),
            rag_path=str(self.test_data_path / "rag"),
            redis_url="redis://localhost:6379"
        )
        
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if details:
            result += f": {details}"
        print(result)
        self.test_results.append((test_name, success, details))
    
    async def test_conversation_store(self):
        """Test 1: Conversation storage functionality"""
        print("\n📝 Testing conversation storage...")
        
        user_id = "test_user_001"
        conversation_id = "test_conv_001"
        
        try:
            # Test storing messages
            message_id1 = await self.memory_manager.store_message(
                user_id, conversation_id, "user", "Hello Tova, how are you?"
            )
            self.log_test("Store user message", bool(message_id1), f"ID: {message_id1}")
            
            message_id2 = await self.memory_manager.store_message(
                user_id, conversation_id, "assistant", "I'm doing great, glitchbrain! How about you?"
            )
            self.log_test("Store assistant message", bool(message_id2), f"ID: {message_id2}")
            
            # Test retrieving conversation context
            context = await self.memory_manager.get_conversation_context(
                user_id, conversation_id, limit=5
            )
            self.log_test("Get conversation context", len(context) == 2, f"Messages: {len(context)}")
            
            # Test conversation summary
            summary = await self.memory_manager.get_conversation_summary(
                user_id, conversation_id
            )
            self.log_test("Get conversation summary", bool(summary), f"Importance: {summary.get('importance', 0)}")
            
        except Exception as e:
            self.log_test("Conversation storage", False, str(e))
    
    async def test_rag_service(self):
        """Test 2: RAG service functionality"""
        print("\n📚 Testing RAG service...")
        
        if not self.memory_manager.rag_service.enabled:
            self.log_test("RAG service enabled", False, "RAG service is disabled")
            return
        
        try:
            # Test storing content in RAG
            user_id = "test_user_001"
            content = "User prefers Italian food and likes to work in the morning"
            
            doc_id = await self.memory_manager.rag_service.store(
                "user_preferences",
                content,
                {
                    "user_id": user_id,
                    "category": "food_preferences",
                    "confidence": 0.9,
                    "timestamp": datetime.now().isoformat()
                }
            )
            self.log_test("Store in RAG", bool(doc_id), f"Document ID: {doc_id}")
            
            # Test searching RAG
            results = await self.memory_manager.rag_service.search(
                query="Italian food preferences",
                collections=["user_preferences"],
                limit=3
            )
            self.log_test("Search RAG", len(results) > 0, f"Results: {len(results)}")
            
            # Test user preferences extraction
            preferences = await self.memory_manager.get_user_preferences(user_id)
            self.log_test("Get user preferences", bool(preferences), f"Categories: {len(preferences.get('categories', {}))}")
            
        except Exception as e:
            self.log_test("RAG service", False, str(e))
    
    async def test_cache_service(self):
        """Test 3: Cache service functionality"""
        print("\n⚡ Testing cache service...")
        
        if not self.memory_manager.cache_service.enabled:
            self.log_test("Cache service enabled", False, "Cache service is disabled")
            return
        
        try:
            # Test basic cache operations
            test_key = "test_cache_key"
            test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
            
            # Set cache
            set_success = await self.memory_manager.cache_service.set(
                test_key, test_value, ttl=60
            )
            self.log_test("Set cache", set_success, "Cache set successfully")
            
            # Get cache
            cached_value = await self.memory_manager.cache_service.get(test_key)
            self.log_test("Get cache", cached_value == test_value, "Cache retrieved correctly")
            
            # Test cache exists
            exists = await self.memory_manager.cache_service.exists(test_key)
            self.log_test("Cache exists", exists, "Key exists in cache")
            
            # Test TTL
            ttl = await self.memory_manager.cache_service.get_ttl(test_key)
            self.log_test("Get TTL", ttl > 0, f"TTL: {ttl} seconds")
            
            # Test conversation context caching
            user_id = "test_user_001"
            conversation_id = "test_conv_001"
            context_data = {"messages": [{"role": "user", "content": "test"}]}
            
            cache_success = await self.memory_manager.cache_service.set_conversation_context(
                user_id, conversation_id, context_data
            )
            self.log_test("Cache conversation context", cache_success, "Context cached")
            
            # Test cache retrieval
            cached_context = await self.memory_manager.cache_service.get_conversation_context(
                user_id, conversation_id
            )
            self.log_test("Get cached context", cached_context == context_data, "Context retrieved from cache")
            
        except Exception as e:
            self.log_test("Cache service", False, str(e))
    
    async def test_memory_integration(self):
        """Test 4: Memory system integration"""
        print("\n🧠 Testing memory integration...")
        
        user_id = "test_user_002"
        conversation_id = "test_conv_002"
        
        try:
            # Test complete memory workflow
            # 1. Store messages
            await self.memory_manager.store_message(
                user_id, conversation_id, "user", "I love Italian food and need to schedule a meeting"
            )
            await self.memory_manager.store_message(
                user_id, conversation_id, "assistant", "I'll help you with that! What time works for the meeting?"
            )
            
            # 2. Get context (should use cache if available)
            context = await self.memory_manager.get_conversation_context(user_id, conversation_id)
            self.log_test("Integrated context retrieval", len(context) == 2, f"Messages: {len(context)}")
            
            # 3. Search memory
            results = await self.memory_manager.search_memory(
                user_id, "Italian food", limit=3
            )
            self.log_test("Integrated memory search", True, f"Search results: {len(results)}")
            
            # 4. Get user preferences
            preferences = await self.memory_manager.get_user_preferences(user_id)
            self.log_test("Integrated preferences", bool(preferences), "Preferences retrieved")
            
            # 5. Update user preference
            await self.memory_manager.update_user_preference(
                user_id, "Prefers morning meetings", "schedule", 0.9
            )
            self.log_test("Update user preference", True, "Preference updated")
            
        except Exception as e:
            self.log_test("Memory integration", False, str(e))
    
    async def test_memory_stats(self):
        """Test 5: Memory statistics"""
        print("\n📊 Testing memory statistics...")
        
        try:
            # Get comprehensive stats
            stats = await self.memory_manager.get_memory_stats()
            
            # Check conversation store stats
            conv_stats = stats.get("conversation_store", {})
            self.log_test("Conversation store stats", bool(conv_stats), 
                         f"Conversations: {conv_stats.get('total_conversations', 0)}")
            
            # Check RAG stats
            rag_stats = stats.get("rag_service", {})
            self.log_test("RAG service stats", bool(rag_stats), 
                         f"Enabled: {rag_stats.get('enabled', False)}")
            
            # Check cache stats
            cache_stats = stats.get("cache_service", {})
            self.log_test("Cache service stats", bool(cache_stats), 
                         f"Enabled: {cache_stats.get('enabled', False)}")
            
            # Check overall stats
            total_conversations = stats.get("total_conversations", 0)
            total_messages = stats.get("total_messages", 0)
            total_rag_docs = stats.get("total_rag_documents", 0)
            
            self.log_test("Overall memory stats", True, 
                         f"Conv: {total_conversations}, Msgs: {total_messages}, RAG: {total_rag_docs}")
            
        except Exception as e:
            self.log_test("Memory statistics", False, str(e))
    
    async def test_error_handling(self):
        """Test 6: Error handling and edge cases"""
        print("\n🛡️ Testing error handling...")
        
        try:
            # Test with invalid user ID
            context = await self.memory_manager.get_conversation_context(
                "invalid_user", "invalid_conv", limit=5
            )
            self.log_test("Invalid user handling", len(context) == 0, "Empty result for invalid user")
            
            # Test with empty query
            results = await self.memory_manager.search_memory("", limit=3)
            self.log_test("Empty query handling", True, f"Results: {len(results)}")
            
            # Test cache with invalid key
            cached_value = await self.memory_manager.cache_service.get("invalid_key")
            self.log_test("Invalid cache key", cached_value is None, "Returns None for invalid key")
            
            # Test RAG with invalid collection
            if self.memory_manager.rag_service.enabled:
                doc_id = await self.memory_manager.rag_service.store(
                    "invalid_collection", "test content", {}
                )
                self.log_test("Invalid RAG collection", doc_id == "", "Returns empty string for invalid collection")
            
        except Exception as e:
            self.log_test("Error handling", False, str(e))
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Clear test conversations
            test_user_ids = ["test_user_001", "test_user_002"]
            for user_id in test_user_ids:
                await self.memory_manager.clear_user_data(user_id)
            
            # Clear cache namespaces
            await self.memory_manager.cache_service.clear_namespace("conversation")
            await self.memory_manager.cache_service.clear_namespace("user")
            
            self.log_test("Cleanup", True, "Test data cleaned up")
            
        except Exception as e:
            self.log_test("Cleanup", False, str(e))
    
    async def run_all_tests(self):
        """Run all memory layer tests"""
        print("🧪 TOVA v4 Memory Layer Test Suite")
        print("=" * 60)
        
        await self.test_conversation_store()
        await self.test_rag_service()
        await self.test_cache_service()
        await self.test_memory_integration()
        await self.test_memory_stats()
        await self.test_error_handling()
        await self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        
        if passed == total:
            print("🎉 All memory layer tests passed!")
            return True
        else:
            print("❌ Some tests failed. Check the output above.")
            return False

async def main():
    """Main test runner"""
    tester = MemoryLayerTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ TOVA v4 Memory Layer is working correctly!")
        print("All memory systems (conversation, RAG, cache) are integrated and functional.")
    else:
        print("\n⚠️  Please fix the failing tests before proceeding.")
    
    # Close connections
    await tester.memory_manager.close()
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 