"""Mixtral brain client for primary conversation handling"""
from typing import AsyncGenerator, Dict, Any
import os
import logging
import httpx
from .base_client import BaseBrainClient


class MixtralClient(BaseBrainClient):
    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = os.getenv("MIXTRAL_BASE_URL", "http://localhost:8000")
        super().__init__(base_url)
        self.model_name = "mixtral"
        self.logger = logging.getLogger(__name__)
        self.stream_timeout_seconds = 300
        self.request_timeout_seconds = 300
    
    def _format_prompt_chatml(self, prompt: str, system_prompt: str = None) -> str:
        """Format prompt using ChatML format for Dolphin Mixtral"""
        if system_prompt:
            return f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant"
        else:
            return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant"
    
    async def generate_response(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        try:
            formatted_prompt = self._format_prompt_chatml(prompt, kwargs.get('system_prompt'))
            payload = {
                "prompt": formatted_prompt,
                "n_predict": kwargs.get("max_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7),
                "stream": False,
                "stop": ["</s>"]
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(
                f"{self.base_url}/completion",
                json=payload,
                headers=headers,
                timeout=60.0
            )
            if response.status_code != 200:
                yield f"HTTP {response.status_code}: {response.text}"
                return
            response_text = response.text
            if response_text:
                yield response_text
            else:
                yield "Empty response from server"
        except Exception as e:
            self.logger.error(f"🎭 Unexpected error: {type(e).__name__}: {str(e)}")
            yield f"Error: {type(e).__name__}: {str(e)}"

    async def health_check(self) -> bool:
        try:
            # POST a tiny prompt to /completion
            response = await self.client.post(
                f"{self.base_url}/completion",
                json={"prompt": "ping", "n_predict": 1, "stream": False},
                timeout=10.0
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Mixtral health check failed: {e}")
            return False 