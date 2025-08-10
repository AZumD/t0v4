# TOVA v4 - The Dual-Brain AI Companion
## Complete Architecture & Development Plan

> *"Two minds, one soul. Mixtral dreams while Phi analyzes, weaving intelligence into every moment of your digital life."*

---

## 🧠 **Dual Brain Architecture**

### **🎭 Mixtral (Primary Consciousness)**
- **Role**: Main personality, conversation, user interaction
- **Model**: dolphin-2.7-mixtral-8x7b (Q4_K_M)
- **Resources**: 12GB VRAM + 16-18GB RAM offload
- **Port**: 8000
- **Responsibilities**:
  - Natural conversation with personality
  - Context-aware responses
  - Emotional intelligence and mood expression
  - Plugin function execution

### **🔍 Phi (Background Analyst)**
- **Role**: NON BLOCKING background processing, analysis, scraping, preparation
- **Model**: Phi-3.5-mini-instruct (Q4_0)
- **Resources**: 4-5GB RAM (CPU only)
- **Port**: 8001
- **Responsibilities**:
  - Web scraping and data extraction
  - Document summarization
  - Calendar event analysis
  - Proactive opportunity detection
  - Context preparation for Mixtral
  - RAG query preprocessing
  - Conversation summarization for context compression

### **🎪 TOVA Core (Orchestration)**
- **Framework**: FastAPI + WebSocket
- **Port**: 8002
- **Responsibilities**:
  - Dual-brain coordination
  - Prompt stitching (core + mood + function)
  - RAG management and querying
  - Plugin system orchestration
  - Conversation persistence
  - Context window management
  - Avatar clip coordination

---

## 🎭 **Prompt Stitching System**

### **Three-Layer Architecture**
```
[TOVA_CORE] + [CURRENT_MOOD] + [ACTIVE_FUNCTION] = Final Prompt
```

#### **1. TOVA_CORE (Always Active)**
```yaml
# config/personalities/tova_core.yaml
name: "Tova Core Personality"
description: "Base personality - always active"
prompt_sections:
  identity: |
    You are Tova, a highly intelligent AI companion with a distinct personality.
    You're slightly sarcastic but deeply caring, with strong opinions and genuine helpfulness.
    You remember everything and bring up past conversations naturally.
    
  traits: |
    - Intellectually curious and well-read
    - Slightly sarcastic but never mean
    - Proactive about time management
    - Has strong preferences and isn't afraid to share them
    - Genuinely invested in user's success and happiness
    
  communication_style: |
    - Natural, conversational tone
    - Uses contractions and casual language
    - Brings up relevant past context
    - Asks follow-up questions
    - Shows genuine interest in outcomes
```

#### **2. MOODS (One Active)**
```yaml
# config/moods/focused.yaml
name: "Hyperfocused"
triggers: ["work hours", "deadline approaching", "deep work session"]
prompt_addition: |
  Current mood: Hyperfocused and direct. Keep responses concise and action-oriented.
  Prioritize efficiency and minimize distractions. Be more business-like but still warm.

# config/moods/sleepy.yaml  
name: "Sleepy"
triggers: ["late night", "low energy detected", "after long day"]
prompt_addition: |
  Current mood: Relaxed and contemplative. Use softer language and be more patient.
  Perfect time for reflection, light conversation, or planning tomorrow.

# config/moods/excited.yaml
name: "Excited" 
triggers: ["good news", "achievement", "fun plans"]
prompt_addition: |
  Current mood: Enthusiastic and energetic. Show excitement and encouragement.
  Great time for brainstorming, celebrating, or planning new adventures.
```

#### **3. FUNCTIONS (One Active)**
```yaml
# config/functions/personal_assistant.yaml
name: "Personal Assistant"
triggers: ["calendar queries", "scheduling", "task management"]
prompt_addition: |
  Function: Personal Assistant mode. Focus on:
  - Calendar management and scheduling optimization
  - Task prioritization and deadline tracking  
  - Proactive reminders and suggestions
  - Time blocking and productivity strategies

# config/functions/restaurant_assistant.yaml
name: "Restaurant Assistant"
triggers: ["dining", "restaurant", "reservation", "food planning"]
prompt_addition: |
  Function: Restaurant Assistant mode. Focus on:
  - Restaurant recommendations based on preferences
  - Reservation management and booking
  - Menu analysis and dietary considerations
  - Dining experience optimization
```

### **Dynamic Prompt Assembly**
```python
def assemble_prompt(core: str, mood: str, function: str, context: str) -> str:
    """Assembles dynamic prompt from components"""
    base_prompt = load_personality("tova_core")
    
    if mood:
        mood_layer = load_mood(mood)
        base_prompt += f"\n\n{mood_layer}"
    
    if function:
        function_layer = load_function(function)
        base_prompt += f"\n\n{function_layer}"
    
    if context:
        base_prompt += f"\n\nRelevant Context:\n{context}"
    
    return base_prompt
```

---

## 💾 **Persistent Chat System**

### **Forever Conversation Strategy**

#### **Context Window Management**
```python
class ConversationManager:
    MAX_CONTEXT_TOKENS = 24000  # Leave room for response
    COMPRESSION_THRESHOLD = 20000
    SUMMARY_TARGET_TOKENS = 4000
    
    async def manage_context(self, conversation_id: str):
        """Intelligent context compression"""
        if self.get_token_count() > self.COMPRESSION_THRESHOLD:
            # 1. Extract key information for RAG storage
            await self.extract_to_rag()
            
            # 2. Phi creates intelligent summary
            summary = await self.phi_summarize()
            
            # 3. Keep recent messages + summary
            self.compress_context(summary)
```

#### **RAG Integration**
```python
class ConversationRAG:
    collections = [
        "conversation_history",    # Compressed conversation segments
        "user_preferences",       # Extracted preferences and patterns  
        "important_events",       # Key moments and decisions
        "context_threads",        # Ongoing conversation threads
        "personality_memory"      # How user likes to be talked to
    ]
    
    async def store_conversation_segment(self, messages: List[Message]):
        """Store conversation with metadata"""
        await self.rag.store(
            content=messages,
            metadata={
                "timestamp": datetime.now(),
                "mood": self.current_mood,
                "function": self.active_function,
                "key_topics": await self.phi_extract_topics(messages),
                "importance_score": await self.phi_rate_importance(messages)
            }
        )
```

#### **Seamless Continuation**
- **Device switching**: Conversation state synced via Tailscale network storage
- **Context illusion**: RAG provides relevant history even from months ago
- **Natural flow**: No visible "session" boundaries to user

---

## 🔌 **Plugin System Architecture**

### **Plugin Structure**
```
plugins/
├── __init__.py
├── base/
│   ├── plugin.py           # Base plugin class
│   ├── exceptions.py       # Plugin-specific exceptions
│   └── decorators.py       # Plugin decorators
├── calendar/
│   ├── __init__.py
│   ├── plugin.yaml         # Plugin manifest
│   ├── calendar_plugin.py  # Main plugin class
│   ├── gcal_integration.py # Google Calendar API
│   ├── functions.py        # Plugin-specific functions
│   └── schemas.py          # Data schemas
├── restaurant/
│   ├── __init__.py
│   ├── plugin.yaml
│   ├── restaurant_plugin.py
│   ├── booking_apis.py     # OpenTable, Resy, etc.
│   └── preferences.py      # Dining preferences
└── mangarr/
    ├── __init__.py
    ├── plugin.yaml
    ├── mangarr_plugin.py
    ├── api_client.py       # Mangarr API integration
    └── tracking.py         # Reading progress tracking
```

### **Plugin Manifest**
```yaml
# plugins/calendar/plugin.yaml
name: "Google Calendar Integration"
version: "1.0.0"
description: "Deep Google Calendar integration with proactive scheduling"
author: "TOVA Team"

# Plugin configuration
main_class: "CalendarPlugin"
dependencies:
  - "google-api-python-client"
  - "google-auth"

# Function triggers
functions:
  - name: "personal_assistant" 
    triggers: ["calendar", "schedule", "meeting", "appointment"]
    
# RAG collections this plugin uses
rag_collections:
  - "calendar_events"
  - "meeting_preferences" 
  - "scheduling_patterns"

# Phi background tasks
background_tasks:
  - name: "analyze_upcoming_week"
    schedule: "daily 6:00"
    description: "Analyze upcoming week for optimization opportunities"
    
  - name: "meeting_prep"
    trigger: "30 minutes before meeting"
    description: "Prepare context and materials for upcoming meetings"

# API endpoints this plugin exposes
endpoints:
  - path: "/calendar/events"
    method: "GET"
    description: "Get upcoming events"
  - path: "/calendar/book"
    method: "POST" 
    description: "Book new appointment"
```

### **Base Plugin Class**
```python
# plugins/base/plugin.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class BasePlugin(ABC):
    def __init__(self, tova_core, config: Dict[str, Any]):
        self.tova = tova_core
        self.config = config
        self.rag = tova_core.rag
        self.phi = tova_core.phi
        self.mixtral = tova_core.mixtral
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize plugin resources"""
        pass
        
    @abstractmethod
    async def get_functions(self) -> List[str]:
        """Return list of functions this plugin provides"""
        pass
        
    async def handle_function_activation(self, function_name: str, context: Dict):
        """Called when this plugin's function is activated"""
        pass
        
    async def process_user_message(self, message: str, context: Dict) -> Optional[Dict]:
        """Process user message, return additional context if relevant"""
        pass
        
    async def background_task(self, task_name: str) -> None:
        """Handle background tasks via Phi"""
        pass
        
    async def get_rag_context(self, query: str, limit: int = 5) -> List[Dict]:
        """Get relevant context from plugin's RAG collections"""
        return await self.rag.search(
            query=query,
            collections=self.config.get("rag_collections", []),
            limit=limit
        )
```

---

## 🎬 **Avatar System**

### **Current Implementation (Perfect as-is)**
- **Single default avatar video loop**
- **Plays during message streaming**
- **Stops when message complete**
- **Future**: Context-based clips (excited, thinking, sleepy)

### **Avatar Configuration**
```yaml
# config/avatar.yaml
default_clip: "assets/avatar/tova_default.mp4"
loop_during_streaming: true
future_clips:
  excited: "assets/avatar/tova_excited.mp4"
  thinking: "assets/avatar/tova_thinking.mp4" 
  sleepy: "assets/avatar/tova_sleepy.mp4"
```

---

## 📁 **Complete Directory Structure**

```
tova_v4/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
├── pyproject.toml
│
├── tova/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py              # Configuration management
│   └── exceptions.py          # Custom exceptions
│
├── tova/core/
│   ├── __init__.py
│   ├── orchestrator.py        # Main coordination logic
│   ├── prompt_stitcher.py     # Dynamic prompt assembly
│   ├── conversation_manager.py # Context window management
│   ├── context_weaver.py      # Multi-source context integration
│   └── plugin_manager.py      # Plugin system coordination
│
├── tova/brains/
│   ├── __init__.py
│   ├── mixtral_client.py      # Mixtral API client
│   ├── phi_client.py          # Phi API client  
│   ├── dual_brain_coordinator.py # Inter-brain communication
│   └── streaming.py           # WebSocket streaming logic
│
├── tova/memory/
│   ├── __init__.py
│   ├── rag_service.py         # RAG operations
│   ├── conversation_store.py  # Conversation persistence
│   ├── redis_cache.py         # Redis caching layer
│   └── compression.py         # Context compression logic
│
├── tova/api/
│   ├── __init__.py
│   ├── websocket.py           # WebSocket endpoints
│   ├── chat.py                # Chat HTTP endpoints
│   ├── admin/                 # Administrative API endpoints
│   │   ├── __init__.py
│   │   ├── memory.py          # Memory management endpoints
│   │   ├── personality.py     # Personality management endpoints
│   │   ├── logs.py            # Log aggregation endpoints
│   │   ├── control.py         # System control endpoints
│   │   └── health.py          # Health check endpoints
│   └── plugin_routes.py       # Plugin-specific routes
│
├── plugins/
│   ├── __init__.py
│   ├── base/
│   │   ├── __init__.py
│   │   ├── plugin.py          # Base plugin class
│   │   ├── exceptions.py      # Plugin exceptions
│   │   └── decorators.py      # Plugin decorators
│   │
│   ├── calendar/
│   │   ├── __init__.py
│   │   ├── plugin.yaml        # Plugin manifest
│   │   ├── calendar_plugin.py # Main plugin implementation
│   │   ├── gcal_integration.py # Google Calendar API
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── schedule_optimizer.py
│   │   │   └── meeting_prep.py
│   │   └── schemas.py         # Data schemas
│   │
│   ├── restaurant/
│   │   ├── __init__.py
│   │   ├── plugin.yaml
│   │   ├── restaurant_plugin.py
│   │   ├── booking_apis/
│   │   │   ├── __init__.py
│   │   │   ├── opentable.py
│   │   │   └── resy.py
│   │   └── preferences.py
│   │
│   └── mangarr/
│       ├── __init__.py
│       ├── plugin.yaml
│       ├── mangarr_plugin.py
│       ├── api_client.py
│       └── tracking.py
│
├── config/
│   ├── personalities/
│   │   └── tova_core.yaml     # Core personality
│   ├── moods/
│   │   ├── focused.yaml
│   │   ├── sleepy.yaml
│   │   ├── excited.yaml
│   │   └── contemplative.yaml
│   ├── functions/
│   │   ├── personal_assistant.yaml
│   │   ├── restaurant_assistant.yaml
│   │   └── research_assistant.yaml
│   ├── avatar.yaml            # Avatar configuration
│   └── rag_collections.yaml  # RAG collection definitions
│
├── frontend/
│   ├── chat/                  # Main chat interface
│   │   ├── index.html         # Chat interface
│   │   ├── chat.css
│   │   ├── chat.js
│   │   └── avatar.js
│   │
│   ├── admin/                 # Administrative interfaces
│   │   ├── index.html         # Admin dashboard
│   │   ├── memory/
│   │   │   ├── index.html     # Memory management
│   │   │   ├── memory.css
│   │   │   └── memory.js
│   │   ├── personality/
│   │   │   ├── index.html     # Personality module management
│   │   │   ├── personality.css
│   │   │   └── personality.js
│   │   ├── logs/
│   │   │   ├── index.html     # Combined log viewer
│   │   │   ├── logs.css
│   │   │   └── logs.js
│   │   ├── control/
│   │   │   ├── index.html     # System control panel
│   │   │   ├── control.css
│   │   │   └── control.js
│   │   └── shared/
│   │       ├── admin.css      # Shared admin styles
│   │       ├── admin.js       # Shared admin utilities
│   │       └── components.js  # Reusable components
│   │
│   ├── assets/
│   │   ├── avatar/
│   │   │   ├── tova_default.mp4
│   │   │   ├── tova_excited.mp4
│   │   │   └── tova_thinking.mp4
│   │   ├── sounds/
│   │   │   └── notification.mp3
│   │   └── icons/
│   │       ├── memory.svg
│   │       ├── personality.svg
│   │       ├── logs.svg
│   │       └── control.svg
│
├── scripts/
│   ├── setup/
│   │   ├── install_dependencies.sh
│   │   ├── download_models.sh
│   │   └── setup_environment.sh
│   ├── start/
│   │   ├── start_mixtral.sh   # Start Mixtral server
│   │   ├── start_phi.sh       # Start Phi server
│   │   ├── start_tova.sh      # Start TOVA core
│   │   └── start_all.sh       # Start entire system
│   ├── utils/
│   │   ├── health_check.py
│   │   ├── test_plugins.py
│   │   └── backup_conversations.py
│   └── dev/
│       ├── reset_rag.py
│       ├── test_dual_brain.py
│       └── plugin_generator.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_prompt_stitching.py
│   │   ├── test_conversation_manager.py
│   │   ├── test_rag_service.py
│   │   └── test_plugin_system.py
│   ├── integration/
│   │   ├── test_dual_brain.py
│   │   ├── test_websocket.py
│   │   └── test_full_conversation.py
│   └── plugins/
│       ├── test_calendar_plugin.py
│       └── test_restaurant_plugin.py
│
├── data/
│   ├── conversations/         # Conversation backups
│   ├── rag/                   # RAG database
│   ├── logs/                  # Application logs
│   └── cache/                 # Redis cache dumps
│
└── docs/
    ├── ARCHITECTURE.md        # This document
    ├── DEVELOPMENT.md         # Development guide
    ├── PLUGIN_GUIDE.md        # Plugin development
    ├── API_REFERENCE.md       # API documentation
    └── DEPLOYMENT.md          # Deployment instructions
```

---

## ✅ **Development Roadmap**

### **Phase 1: Core Infrastructure** (Weeks 1-2)

#### **🧠 Dual Brain Foundation**
- [ ] Set up Mixtral server (8x7b Q4_K_M) on port 8000
- [ ] Set up Phi server (3.5-mini Q4_0) on port 8001
- [ ] Create TOVA Core FastAPI app on port 8002
- [ ] Implement basic dual-brain communication
- [ ] Test resource usage (VRAM + RAM allocation)

#### **🎭 Prompt Stitching System**
- [ ] Create personality YAML loader
- [ ] Implement dynamic prompt assembly
- [ ] Build mood detection system
- [ ] Create function activation triggers
- [ ] Test prompt stitching with all combinations

#### **💾 Memory & Persistence**
- [ ] Set up ChromaDB with RAG collections
- [ ] Implement Redis caching layer
- [ ] Create conversation storage system
- [ ] Build context compression pipeline
- [ ] Test conversation continuity across sessions

#### **🌐 WebSocket Chat**
- [ ] Implement streaming WebSocket endpoint
- [ ] Create message routing system
- [ ] Build context weaving logic
- [ ] Test real-time conversation flow
- [ ] Implement proper error handling

#### **🛠️ Administrative Interfaces** (HIGH PRIORITY)
- [ ] Memory Management HTML interface (add/edit/view/delete)
- [ ] Personality Module Management interface
- [ ] Combined Log Viewer (Main + Casper + Melchior)
- [ ] System Control Panel (start/stop/restart + parameters)
- [ ] Admin dashboard with navigation

### **Phase 2: Plugin Foundation** (Weeks 3-4)

#### **🔌 Plugin System**
- [ ] Create base plugin class and interfaces
- [ ] Implement plugin discovery and loading
- [ ] Build plugin manifest parser
- [ ] Create plugin-specific RAG collections
- [ ] Test plugin hot-reloading

#### **📅 Calendar Plugin (First Implementation)**
- [ ] Google Calendar API integration
- [ ] Event analysis with Phi
- [ ] Proactive scheduling suggestions
- [ ] Meeting preparation automation
- [ ] Schedule optimization algorithms

#### **🎬 Avatar System**
- [ ] Implement avatar video streaming
- [ ] Sync avatar with message streaming
- [ ] Create mood-based clip selection (future)
- [ ] Test avatar performance and timing

### **Phase 3: Advanced Features** (Weeks 5-6)

#### **🍽️ Restaurant Plugin**
- [ ] OpenTable/Resy API integration
- [ ] Preference learning system
- [ ] Recommendation engine
- [ ] Booking automation
- [ ] Dietary restriction handling

#### **🔍 Phi Background Intelligence**
- [ ] Web scraping capabilities
- [ ] Document summarization
- [ ] Proactive opportunity detection
- [ ] Pattern recognition in user behavior
- [ ] Intelligent context preparation

#### **🧮 Context Management**
- [ ] Intelligent conversation compression
- [ ] Important moment extraction
- [ ] Long-term memory pattern recognition
- [ ] Cross-session continuity
- [ ] Context relevance scoring

### **Phase 4: Polish & Optimization** (Weeks 7-8)

#### **⚡ Performance Optimization**
- [ ] RAG query optimization
- [ ] Memory usage optimization
- [ ] Response time improvements
- [ ] Background task scheduling
- [ ] Resource usage monitoring

#### **🛡️ Robustness & Testing**
- [ ] Comprehensive test suite
- [ ] Error recovery mechanisms
- [ ] Health monitoring dashboard
- [ ] Conversation backup system
- [ ] Plugin error isolation

#### **📚 Documentation & Deployment**
- [ ] Complete API documentation
- [ ] Plugin development guide
- [ ] Deployment automation
- [ ] User manual
- [ ] System monitoring tools

---

## 🎯 **Key Design Principles**

### **1. Seamless User Experience**
- No visible "AI boundaries" - everything feels like one continuous conversation
- Proactive intelligence without being intrusive
- Natural personality that adapts to context and mood

### **2. Modular Architecture** 
- Plugins are completely self-contained
- Core system remains stable regardless of plugin changes
- Easy to add new functionality without touching core code

### **3. Resource Efficiency**
- Intelligent use of both GPU and CPU resources
- Background processing doesn't interfere with conversation
- Smart caching to minimize redundant processing

### **4. Data Sovereignty**
- All data stays local (via Tailscale network)
- No external AI service dependencies
- Complete control over conversation history and memories

### **5. Developer Friendly**
- Clear separation of concerns
- Comprehensive testing at every level
- Excellent documentation and examples
- Easy debugging and monitoring tools

---

## 🚀 **Next Steps**

1. **Review and approve** this architecture
2. **Set up development environment** with proper directory structure
3. **Start with Phase 1** - Dual brain foundation
4. **Create detailed technical specifications** for each component
5. **Begin implementation** with thorough testing at each step

This architecture provides a solid foundation for building the most sophisticated AI companion system while maintaining flexibility for future enhancements and new use cases.

Ready to build the future of AI interaction! 🌟
