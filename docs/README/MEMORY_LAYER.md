# MEMORY_LAYER.md

## Purpose
Complete memory layer for TOVA v4 with persistent conversation storage, semantic RAG capabilities, and fast caching for optimal performance.

## Architecture

### **Three-Tier Memory System**
```
┌─────────────────────────────────────────────────────────────┐
│                    Memory Manager                           │
│              (tova/memory/memory_manager.py)                │
├─────────────────────────────────────────────────────────────┤
│  📝 Conversation Store  │  📚 RAG Service  │  ⚡ Cache Service │
│  (JSON files)          │  (ChromaDB)      │  (Redis)         │
└─────────────────────────────────────────────────────────────┘
```

## Components

### **1. Conversation Store** (`tova/memory/conversation_store.py`)
- **Purpose**: Persistent conversation history storage
- **Format**: JSON files with structured message data
- **Features**: 
  - Message storage with metadata
  - Conversation retrieval and management
  - User-specific conversation organization
  - Message threading and context preservation

### **2. RAG Service** (`tova/memory/rag_service.py`)
- **Purpose**: Semantic search and long-term memory
- **Backend**: ChromaDB with sentence-transformers embeddings
- **Collections**:
  - `conversation_history`: Compressed conversation segments
  - `user_preferences`: Extracted user preferences and patterns
  - `important_events`: Key moments and decisions
  - `context_threads`: Ongoing conversation threads
  - `personality_memory`: How user likes to be talked to

### **3. Cache Service** (`tova/memory/cache_service.py`)
- **Purpose**: Fast access to frequently used data
- **Backend**: Redis with TTL management
- **Namespaces**:
  - `conversation`: Conversation context caching
  - `user`: User preferences and data
  - `search`: RAG search results
  - `prompt`: Assembled prompt caching
  - `session`: Session data

### **4. Memory Manager** (`tova/memory/memory_manager.py`)
- **Purpose**: Unified interface for all memory operations
- **Features**:
  - Integrated conversation storage and retrieval
  - Automatic insight extraction and RAG storage
  - Intelligent caching with TTL management
  - Memory statistics and health monitoring

## Usage

### **Basic Memory Operations**

```python
from tova.memory.memory_manager import MemoryManager

# Initialize memory manager
memory = MemoryManager(
    conversation_path="data/conversations",
    rag_path="data/rag", 
    redis_url="redis://localhost:6379"
)

# Store a message
message_id = await memory.store_message(
    user_id="user_123",
    conversation_id="conv_456", 
    role="user",
    content="Hello Tova, how are you?"
)

# Get conversation context
context = await memory.get_conversation_context(
    user_id="user_123",
    conversation_id="conv_456",
    limit=10
)

# Search memory
results = await memory.search_memory(
    user_id="user_123",
    query="Italian food preferences",
    limit=5
)

# Get user preferences
preferences = await memory.get_user_preferences("user_123")
```

### **Advanced Memory Operations**

```python
# Update user preference
await memory.update_user_preference(
    user_id="user_123",
    preference="Prefers morning meetings",
    category="schedule",
    confidence=0.9
)

# Get conversation summary with insights
summary = await memory.get_conversation_summary(
    user_id="user_123",
    conversation_id="conv_456",
    phi_client=phi_client  # Optional Phi analysis
)

# Get comprehensive memory statistics
stats = await memory.get_memory_stats()
```

## Configuration

### **ChromaDB Configuration**
```python
# Initialize RAG service
rag_service = RAGService(
    persist_path="data/rag",
    embedding_model="all-MiniLM-L6-v2"  # Local sentence-transformers model
)
```

### **Redis Configuration**
```python
# Initialize cache service
cache_service = CacheService(
    redis_url="redis://localhost:6379",
    default_ttl=3600  # 1 hour default TTL
)
```

### **Memory Manager Configuration**
```python
# Initialize complete memory system
memory_manager = MemoryManager(
    conversation_path="data/conversations",
    rag_path="data/rag",
    redis_url="redis://localhost:6379"
)
```

## Data Flow

### **Message Storage Flow**
```
1. User sends message
   ↓
2. Store in conversation_store (JSON)
   ↓
3. Update conversation cache (Redis)
   ↓
4. Extract insights (Phi analysis)
   ↓
5. Store insights in RAG (ChromaDB)
```

### **Memory Retrieval Flow**
```
1. User query received
   ↓
2. Check cache first (Redis)
   ↓
3. If cache miss, search RAG (ChromaDB)
   ↓
4. Get conversation context (JSON files)
   ↓
5. Cache results for future use
   ↓
6. Return integrated results
```

## RAG Collections

### **conversation_history**
- **Purpose**: Store compressed conversation segments
- **Metadata**: user_id, conversation_id, timestamp, mood, function, importance
- **Use Case**: Semantic search across conversation history

### **user_preferences**
- **Purpose**: Store extracted user preferences and patterns
- **Metadata**: user_id, category, confidence, timestamp, source
- **Use Case**: Personalization and preference learning

### **important_events**
- **Purpose**: Store key moments and decisions
- **Metadata**: user_id, event_type, timestamp, impact_score, related_conversations
- **Use Case**: Important moment recall and decision tracking

### **context_threads**
- **Purpose**: Store ongoing conversation threads and topics
- **Metadata**: user_id, thread_id, topic, last_mentioned, relevance
- **Use Case**: Context continuity and topic tracking

### **personality_memory**
- **Purpose**: Store how user likes to be talked to
- **Metadata**: user_id, trait, examples, confidence, last_observed
- **Use Case**: Communication style adaptation

## Caching Strategy

### **TTL (Time To Live) Settings**
- **Conversation Context**: 30 minutes
- **User Preferences**: 24 hours
- **RAG Search Results**: 1 hour
- **Prompt Cache**: 2 hours
- **Session Data**: 30 minutes

### **Cache Invalidation**
- **Automatic**: TTL-based expiration
- **Manual**: Namespace clearing for data updates
- **Selective**: Key-specific deletion for targeted updates

## Performance Optimization

### **ChromaDB Optimizations**
- **Embedding Model**: Local sentence-transformers for fast inference
- **Persistence**: Persistent storage for data durability
- **Collections**: Separate collections for different data types
- **Metadata Filtering**: Efficient query filtering

### **Redis Optimizations**
- **Connection Pooling**: Efficient connection management
- **Serialization**: JSON for simple data, pickle for complex objects
- **TTL Management**: Automatic expiration to prevent memory bloat
- **Namespace Isolation**: Separate namespaces for different data types

### **Memory Manager Optimizations**
- **Async Operations**: Non-blocking memory operations
- **Caching First**: Cache-first retrieval strategy
- **Background Processing**: Insight extraction in background
- **Error Isolation**: Graceful degradation when services fail

## Error Handling

### **Graceful Degradation**
- **RAG Disabled**: Falls back to conversation store only
- **Cache Disabled**: Direct access to underlying services
- **Service Failures**: Continues operation with reduced functionality
- **Data Corruption**: Automatic recovery and data validation

### **Error Recovery**
- **Connection Failures**: Automatic reconnection attempts
- **Data Loss**: Backup and recovery mechanisms
- **Performance Issues**: Automatic service health monitoring
- **Resource Exhaustion**: Memory cleanup and optimization

## Monitoring and Statistics

### **Memory Statistics**
```python
stats = await memory_manager.get_memory_stats()

# Returns:
{
    "conversation_store": {
        "total_conversations": 150,
        "total_messages": 2500,
        "storage_size": "45MB"
    },
    "rag_service": {
        "enabled": True,
        "collections": {
            "conversation_history": {"count": 500},
            "user_preferences": {"count": 75},
            "important_events": {"count": 25}
        }
    },
    "cache_service": {
        "enabled": True,
        "hit_rate": 85.5,
        "used_memory_human": "128MB"
    }
}
```

### **Health Monitoring**
- **Service Status**: Individual service health checks
- **Performance Metrics**: Response times and throughput
- **Resource Usage**: Memory and storage utilization
- **Error Rates**: Failure tracking and alerting

## Testing

### **Test Suite**
```bash
# Run comprehensive memory layer tests
python test/test_memory_layer.py

# Test individual components
python -c "from tova.memory.rag_service import RAGService; print('RAG Service OK')"
python -c "from tova.memory.cache_service import CacheService; print('Cache Service OK')"
```

### **Test Coverage**
- **Unit Tests**: Individual component functionality
- **Integration Tests**: Cross-component interactions
- **Performance Tests**: Load and stress testing
- **Error Tests**: Failure scenario handling

## Dependencies

### **Required Packages**
```bash
pip install chromadb sentence-transformers redis
```

### **System Requirements**
- **ChromaDB**: 2GB+ RAM for embeddings
- **Redis**: 512MB+ RAM for caching
- **Storage**: 10GB+ for conversation history and RAG data
- **CPU**: Multi-core for embedding generation

## Integration

### **With TOVA Core**
- **Conversation Management**: Automatic message storage and retrieval
- **Context Provision**: Intelligent context assembly for responses
- **Personalization**: User preference integration
- **Memory Continuity**: Cross-session memory persistence

### **With Phi Background Brain**
- **Insight Extraction**: Automatic preference and event detection
- **Importance Scoring**: Conversation importance evaluation
- **Pattern Recognition**: User behavior pattern analysis
- **Context Preparation**: Intelligent context preparation for Mixtral

### **With Plugin System**
- **Plugin Memory**: Plugin-specific RAG collections
- **Context Sharing**: Cross-plugin context sharing
- **Preference Integration**: Plugin preference learning
- **Event Tracking**: Plugin event and decision tracking 