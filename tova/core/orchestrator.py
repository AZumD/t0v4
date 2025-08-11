"""Main orchestration logic for dual-brain coordination"""
from typing import Dict, Any, Optional, AsyncGenerator, List
import asyncio
import logging
import uuid
import time
from ..brains.mixtral_client import MixtralClient
from ..brains.phi_client import PhiClient
from .prompt_stitcher import PromptStitcher
from ..memory.conversation_store import ConversationStore


class TovaOrchestrator:
    def __init__(self):
        self.mixtral = MixtralClient()
        # Use dedicated Phi client at port 8001
        self.phi = PhiClient(base_url="http://localhost:8001")
        self.prompt_stitcher = PromptStitcher()
        self.conversation_store = ConversationStore()
        self.logger = logging.getLogger(__name__)
        
        # State tracking
        self.current_mood = "neutral"
        self.active_function = None
        self.conversation_context = []
        self.active_conversations = {}  # conversation_id -> metadata

        # Cached health checks to avoid per-message latency
        self._health_cache: Dict[str, Any] = {
            "mixtral": {"ok": None, "ts": 0.0},
            "phi": {"ok": None, "ts": 0.0},
        }
        # Increase TTL to reduce health checking frequency aggressively
        self._health_ttl_seconds = 60.0
    
    async def _get_health(self) -> Dict[str, bool]:
        now = time.time()
        cached_mixtral = self._health_cache["mixtral"]
        cached_phi = self._health_cache["phi"]

        if cached_mixtral["ok"] is None or now - cached_mixtral["ts"] > self._health_ttl_seconds:
            cached_mixtral["ok"] = await self.mixtral.health_check()
            cached_mixtral["ts"] = now
        if cached_phi["ok"] is None or now - cached_phi["ts"] > self._health_ttl_seconds:
            cached_phi["ok"] = await self.phi.health_check()
            cached_phi["ts"] = now
        return {"mixtral": cached_mixtral["ok"], "phi": cached_phi["ok"]}
    
    async def initialize(self) -> bool:
        """Initialize both brains and verify connectivity"""
        self.logger.info("Initializing TOVA Orchestrator...")
        
        # Check both brains are online (but don't fail if they're not)
        health = await self._get_health()
        mixtral_ok = health["mixtral"]
        phi_ok = health["phi"]
        
        if not mixtral_ok:
            self.logger.warning("⚠️  Mixtral brain not responding - will retry on first use")
            
        if not phi_ok:
            self.logger.warning("⚠️  Phi brain not responding - will retry on first use")
            
        if mixtral_ok and phi_ok:
            self.logger.info("🎭 Mixtral connected")
            self.logger.info("🔍 Phi connected")
            self.logger.info("✅ TOVA Orchestrator ready")
            return True
        else:
            self.logger.info("⚠️  TOVA Orchestrator ready (degraded mode)")
            return False
    
    async def start_conversation(self, user_id: str) -> str:
        """Start a new conversation for a user"""
        conversation_id = str(uuid.uuid4())
        
        # Create conversation in database
        await self.conversation_store.create_conversation(
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        # Initialize conversation metadata
        self.active_conversations[conversation_id] = {
            "user_id": user_id,
            "current_mood": "neutral",
            "active_function": None,
            "message_count": 0,
            "context_usage": 0
        }
        
        self.logger.info(f"Started new conversation {conversation_id} for user {user_id}")
        return conversation_id
    
    async def process_user_message(
        self, 
        message: str, 
        user_context: Optional[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """Process user message through dual-brain system"""
        
        self.logger.info(f"🔍 Orchestrator: Processing message: {message[:50]}...")
        
        # Cached health to reduce first-token latency
        health = await self._get_health()
        mixtral_ok = health["mixtral"]
        phi_ok = health["phi"]
        
        # If Mixtral is offline, we cannot answer; return fallback immediately
        if not mixtral_ok:
            self.logger.info("🔍 Orchestrator: Mixtral offline, using fallback response")
            fallback_response = self._generate_fallback_response(message)
            yield fallback_response
            return

        # Fire-and-forget Phi analysis (non-blocking); do not await or store task
        if phi_ok:
            asyncio.create_task(self._background_analysis_silent(message, user_context))
            self.logger.info("🔍 Phi task fired (non-blocking)")
        
        # 2. Build dynamic prompt
        self.logger.info("🔍 Orchestrator: Building dynamic prompt")
        self.logger.info(f"🔍 Orchestrator: Starting prompt build at {time.perf_counter():.3f}")
        build_t0 = time.perf_counter()
        system_prompt, user_message = await self.prompt_stitcher.build_prompt(
            message=message,
            mood=self.current_mood,
            function=self.active_function,
            context=user_context
        )
        build_t1 = time.perf_counter()
        self.logger.info(
            f"🔍 Orchestrator: Built prompts in {(build_t1 - build_t0)*1000:.1f}ms; system[{len(system_prompt)}], user[{len(user_message)}]"
        )
        self.logger.info(f"🔍 Orchestrator: Prompt built, sending to Mixtral at {time.perf_counter():.3f}")
        
        # 3. Generate response with Mixtral (streaming)
        self.logger.info("🔍 Orchestrator: Starting Mixtral response generation")
        first_chunk = True
        gen_t0 = time.perf_counter()
        async for chunk in self.mixtral.generate_response(
            prompt=user_message,
            system_prompt=system_prompt,
            stream=True
        ):
            # Each chunk is clean text content
            if chunk:
                if first_chunk:
                    first_chunk = False
                    gen_t1 = time.perf_counter()
                    self.logger.info(
                        f"🔍 Orchestrator: First token after {(gen_t1 - gen_t0)*1000:.1f}ms"
                    )
                self.logger.info(f"🔍 Orchestrator: Got chunk from Mixtral: {chunk[:50]}...")
                yield chunk
        
        self.logger.info("🔍 Orchestrator: Message processing completed")
    
    async def process_user_message_with_persistence(
        self,
        conversation_id: str,
        message: str,
        user_context: Optional[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process user message with conversation persistence"""
        
        # Store user message
        await self.conversation_store.store_message(
            conversation_id=conversation_id,
            role="user",
            content=message
        )
        
        # Get conversation context
        conversation_history = await self.conversation_store.get_conversation_context(
            conversation_id=conversation_id
        )
        
        # Add conversation history to context
        enhanced_context = {
            **(user_context or {}),
            "conversation_history": conversation_history[-10:],  # Last 10 messages
            "conversation_id": conversation_id
        }
        
        # Process message
        response_content = ""
        metadata = {}
        
        async for chunk_data in self.process_user_message(message, enhanced_context):
            if isinstance(chunk_data, dict):
                content = chunk_data.get("content", "")
                chunk_metadata = chunk_data.get("metadata", {})
                if content:
                    response_content += content
                    metadata.update(chunk_metadata)
                    yield chunk_data
            else:
                if chunk_data:
                    response_content += chunk_data
                    yield {"content": chunk_data, "metadata": {}}
        
        # Store TOVA's response
        await self.conversation_store.store_message(
            conversation_id=conversation_id,
            role="tova",
            content=response_content,
            metadata=metadata,
            tokens_used=metadata.get("tokens_used"),
            processing_time_ms=metadata.get("processing_time_ms")
        )
        
        # Update conversation metadata
        if conversation_id in self.active_conversations:
            self.active_conversations[conversation_id]["message_count"] += 2  # user + tova
    
    async def _background_analysis(
        self, 
        message: str, 
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Background processing with Phi brain"""
        
        # Run multiple analysis tasks in parallel
        tasks = [
            self.phi.analyze_text(message, "extract_topics"),
            self.phi.analyze_text(message, "extract_preferences"),
            self.phi.analyze_text(message, "rate_importance")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "topics": results[0] if not isinstance(results[0], Exception) else "",
            "preferences": results[1] if not isinstance(results[1], Exception) else "",
            "importance": results[2] if not isinstance(results[2], Exception) else "0.5"
        }

    async def _background_analysis_silent(self, message: str, context: Optional[Dict]):
        """Completely non-blocking Phi analysis - fire and forget"""
        try:
            analysis = await self._background_analysis(message, context)
            await self._process_background_analysis(analysis)
        except Exception as e:
            self.logger.debug(f"Phi background task failed (ignored): {e}")
    
    async def _process_background_analysis(self, analysis: Dict[str, Any]):
        """Process Phi's background analysis results"""
        # TODO: Store in RAG, update user preferences, etc.
        self.logger.info(f"Background analysis: {analysis}")
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return await self.conversation_store.get_conversation_history(conversation_id)
    
    async def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations for a user"""
        return await self.conversation_store.get_recent_conversations(user_id, limit)
    
    async def shutdown(self):
        """Clean shutdown of both brains"""
        await self.mixtral.close()
        await self.phi.close()
        self.logger.info("TOVA Orchestrator shutdown complete") 

    def _generate_fallback_response(self, message: str) -> str:
        """Generate a fallback response when brain servers are offline"""
        import random
        
        fallback_responses = [
            "Hey glitchbrain, I'm fucking offline right now - my brain servers aren't running. Start them up with `./scripts/start/start_all.sh` and I'll be back to being your fierce, loyal AI companion! 🎭",
            "Shit, my brains are down, glitchlove. Can't process your message right now. Get those servers running and I'll be back to calling out bullshit and helping you crush your goals! 🔥",
            "Fuck, I'm in degraded mode, glitchheart. My Mixtral and Phi brains are offline. Fire up the servers and I'll be back to being your hyperactive, unfiltered AI companion! ⚡",
            "Damn it, my dual-brain system is down, glitchbrain. Can't give you the full TOVA experience right now. Start the brain servers and I'll be back to being your fiercely loyal AI! 🎪"
        ]
        
        return random.choice(fallback_responses) 