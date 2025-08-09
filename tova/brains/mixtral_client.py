"""Mixtral brain client for primary conversation handling"""
from typing import AsyncGenerator, Dict, Any
import json
import logging
import httpx
from .base_client import BaseBrainClient


class MixtralClient(BaseBrainClient):
    def __init__(self, base_url: str = "http://localhost:8000"):
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
            self.logger.info(f"🎭 Formatted prompt length: {len(formatted_prompt)}")
            
            payload = {
                "prompt": formatted_prompt,
                "n_predict": kwargs.get("max_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7),
                "stream": False,
                "stop": ["</s>"]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            self.logger.info(f"🎭 About to make POST request to {self.base_url}/completion")
            self.logger.info(f"🎭 Payload keys: {list(payload.keys())}")
            self.logger.info(f"🎭 Headers: {headers}")
            
            response = await self.client.post(
                f"{self.base_url}/completion",
                json=payload,
                headers=headers,
                timeout=60.0
            )
            
            self.logger.info(f"🎭 Response received - Status: {response.status_code}")
            self.logger.info(f"🎭 Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                error_text = response.text
                self.logger.error(f"🎭 HTTP {response.status_code} error: {error_text}")
                yield f"HTTP {response.status_code}: {error_text}"
                return
                
            # Log the raw response
            response_text = response.text
            self.logger.info(f"🎭 Raw response (first 500 chars): {response_text[:500]}")
            
            # Parse the response content (for now, yield as-is for debugging)
            if response_text:
                self.logger.info("🎭 Processing response text...")
                yield response_text
            else:
                self.logger.warning("🎭 Empty response received")
                yield "Empty response from server"
                
        except httpx.TimeoutException as e:
            self.logger.error(f"🎭 Timeout error: {str(e)}")
            yield f"Timeout error: {str(e)}"
        except httpx.HTTPStatusError as e:
            self.logger.error(f"🎭 HTTP status error: {str(e)}")
            yield f"HTTP error: {str(e)}"
        except Exception as e:
            self.logger.error(f"🎭 Unexpected error: {type(e).__name__}: {str(e)}")
            self.logger.error(f"🎭 Error details: {repr(e)}")
            yield f"Error: {type(e).__name__}: {str(e)}"

    async def analyze_text(self, text: str, task: str = "summarize") -> str:
        """Analyze text for specific task"""
        self.logger.info(f"🎭 analyze_text called with task: {task}, text length: {len(text)}")
        
        try:
            prompts = {
                "summarize": f"Summarize this briefly:\n\n{text}\n\nSummary:",
                "extract_topics": f"Extract key topics from this text:\n\n{text}\n\nTopics:",
                "extract_preferences": f"Extract user preferences:\n\n{text}\n\nPreferences:",
                "rate_importance": f"Rate importance (0-1):\n\n{text}\n\nImportance:"
            }
            
            prompt = prompts.get(task, f"Analyze:\n\n{text}\n\nAnalysis:")
            self.logger.info(f"🎭 Using prompt for {task}: {prompt[:100]}...")
            
            async for chunk in self.generate_response(prompt, stream=False, max_tokens=200):
                self.logger.info(f"🎭 analyze_text received chunk: {chunk[:100]}...")
                return chunk
            
            self.logger.warning(f"🎭 No chunks received for analyze_text task: {task}")
            return f"No analysis available for {task}"
            
        except Exception as e:
            self.logger.error(f"🎭 analyze_text error: {type(e).__name__}: {str(e)}")
            return f"Analysis error: {str(e)}"

    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/v1/models", timeout=30.0)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Mixtral health check failed: {e}")
            return False 