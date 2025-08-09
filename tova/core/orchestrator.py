"""Main orchestration logic for dual-brain coordination"""
from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
import logging
from ..brains.mixtral_client import MixtralClient
from ..brains.phi_client import PhiClient
from .prompt_stitcher import PromptStitcher


class TovaOrchestrator:
    def __init__(self):
        self.mixtral = MixtralClient()
        self.phi = PhiClient()
        self.prompt_stitcher = PromptStitcher()
        self.logger = logging.getLogger(__name__)
        
        # State tracking
        self.current_mood = "neutral"
        self.active_function = None
        self.conversation_context = []
    
    async def initialize(self) -> bool:
        """Initialize both brains and verify connectivity"""
        self.logger.info("Initializing TOVA Orchestrator...")
        
        # Check both brains are online
        mixtral_ok = await self.mixtral.health_check()
        phi_ok = await self.phi.health_check()
        
        if not mixtral_ok:
            self.logger.error("Mixtral brain not responding")
            return False
            
        if not phi_ok:
            self.logger.error("Phi brain not responding")
            return False
            
        self.logger.info("🎭 Mixtral connected")
        self.logger.info("🔍 Phi connected")
        self.logger.info("✅ TOVA Orchestrator ready")
        return True
    
    async def process_user_message(
        self, 
        message: str, 
        user_context: Optional[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """Process user message through dual-brain system"""
        
        # 1. Background analysis with Phi (async)
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
        
        # 3. Generate response with Mixtral (streaming)
        async for chunk in self.mixtral.generate_response(prompt):
            yield chunk
        
        # 4. Wait for Phi analysis to complete
        analysis = await phi_task
        await self._process_background_analysis(analysis)
    
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
    
    async def shutdown(self):
        """Clean shutdown of both brains"""
        await self.mixtral.close()
        await self.phi.close()
        self.logger.info("TOVA Orchestrator shutdown complete") 