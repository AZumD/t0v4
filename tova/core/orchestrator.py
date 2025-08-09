"""Main orchestration logic for dual-brain coordination"""
from typing import Dict, Any, Optional, AsyncGenerator, List
import asyncio
import logging
import uuid
from ..brains.mixtral_client import MixtralClient
from ..brains.phi_client import PhiClient
from .prompt_stitcher import PromptStitcher
from ..memory.conversation_store import ConversationStore


class TovaOrchestrator:
    def __init__(self):
        self.mixtral = MixtralClient()
        self.phi = PhiClient()
        self.prompt_stitcher = PromptStitcher()
        self.conversation_store = ConversationStore()
        self.logger = logging.getLogger(__name__)
        
        # State tracking
        self.current_mood = "neutral"
        self.active_function = None
        self.conversation_context = []
        self.active_conversations = {}  # conversation_id -> metadata
    
    async def initialize(self) -> bool:
        """Initialize both brains and verify connectivity"""
        self.logger.info("Initializing TOVA Orchestrator...")
        
        # Check both brains are online (but don't fail if they're not)
        mixtral_ok = await self.mixtral.health_check()
        phi_ok = await self.phi.health_check()
        
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
        
        # Check if brains are available
        mixtral_ok = await self.mixtral.health_check()
        phi_ok = await self.phi.health_check()
        
        if not mixtral_ok and not phi_ok:
            # Both brains offline - provide fallback response
            fallback_response = self._generate_fallback_response(message)
            yield fallback_response
            return
        
        # 1. Background analysis with Phi (async) - only if available
        phi_task = None
        if phi_ok:
            phi_task = asyncio.create_task(
                self._background_analysis(message, user_context)
            )
        
        # 2. Build dynamic prompt
        prompt = await self.prompt_stitcher.build_prompt(
            message=message,
            mood=self.current_mood,
            function=self.active_function,
            context=user_context
        )
        
        # 3. Generate response with Mixtral (streaming) - only if available
        if mixtral_ok:
            async for chunk in self.mixtral.generate_response(prompt):
                yield chunk
        else:
            # Mixtral offline - provide fallback response
            fallback_response = self._generate_fallback_response(message)
            yield fallback_response
        
        # 4. Wait for Phi analysis to complete (if it was started)
        if phi_task:
            try:
                analysis = await phi_task
                await self._process_background_analysis(analysis)
            except Exception as e:
                self.logger.warning(f"Phi analysis failed: {e}")
    
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