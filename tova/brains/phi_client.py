"""Phi brain client for background analysis and processing"""
from typing import Dict, Any, Optional, AsyncGenerator
import logging
import os
from .base_client import BaseBrainClient


class PhiClient(BaseBrainClient):
    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = os.getenv("PHI_BASE_URL", "http://localhost:8001")
        super().__init__(base_url)
        self.model_name = "phi"
        self.logger = logging.getLogger(__name__)
    
    async def analyze_text(self, text: str, task: str = "summarize") -> str:
        """Analyze text for specific task (summarize, extract_topics, etc.)"""
        prompts = {
            "summarize": f"Summarize this conversation concisely:\n\n{text}\n\nSummary:",
            "extract_topics": f"Extract key topics from this text:\n\n{text}\n\nTopics:",
            "extract_preferences": f"Extract user preferences from this text:\n\n{text}\n\nPreferences:",
            "rate_importance": f"Rate the importance of this conversation (0-1):\n\n{text}\n\nImportance:"
        }
        prompt = prompts.get(task, f"Analyze this text:\n\n{text}\n\nAnalysis:")
        payload = {
            "prompt": prompt,
            "temperature": 0.3,
            "max_tokens": 500,
            "stream": False
        }
        try:
            response = await self.client.post(
                f"{self.base_url}/completion",
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return result.get("content", "").strip()
        except Exception as e:
            self.logger.error(f"Phi analysis error: {str(e)}")
            return ""
    
    async def generate_response(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """For compatibility - Phi doesn't typically do streaming responses"""
        try:
            payload = {
                "prompt": prompt,
                "temperature": kwargs.get("temperature", 0.3),
                "max_tokens": kwargs.get("max_tokens", 500),
                "stream": False
            }
            response = await self.client.post(
                f"{self.base_url}/completion",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            content = result.get("content", "")
            for chunk in content.split():
                yield chunk + " "
        except Exception as e:
            self.logger.error(f"Phi generation error: {e}")
            yield f"Error: {str(e)}"
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.post(
                f"{self.base_url}/completion",
                json={"prompt": "ping", "n_predict": 1, "stream": False},
                timeout=10.0
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Phi health check failed: {e}")
            return False 