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
    
    async def generate_response(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 1000,
        top_p: float = 0.9,
        stream: bool = True,
        system_prompt: str = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from Mixtral"""
        
        # Format prompt using ChatML for Dolphin Mixtral
        formatted_prompt = self._format_prompt_chatml(prompt, system_prompt)
        
        payload = {
            "prompt": formatted_prompt,
            "n_predict": max_tokens,  # Use n_predict instead of max_tokens for llama.cpp
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
            "stop": ["<|im_end|>", "<|im_start|>", "Human:", "User:", "\n\nHuman:", "\n\nUser:"]
        }
        
        try:
            if stream:
                # Handle streaming response
                self.logger.debug(f"Sending streaming request to {self.base_url}/completion")
                async with self.client.stream(
                    "POST", 
                    f"{self.base_url}/completion",
                    json=payload,
                    timeout=self.stream_timeout_seconds
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.strip():
                            self.logger.debug(f"Received line: {line[:200]}...")
                            # Handle SSE format (data: prefix)
                            if line.startswith("data: "):
                                data = line[6:]
                                if data == "[DONE]":
                                    break
                                
                                try:
                                    chunk = json.loads(data)
                                    if "content" in chunk:
                                        content = chunk["content"]
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    continue
                            else:
                                # Try to parse as regular JSON (non-SSE format)
                                try:
                                    chunk = json.loads(line)
                                    if "content" in chunk:
                                        content = chunk["content"]
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    if line.strip():
                                        yield line.strip()
            else:
                # Handle non-streaming response
                self.logger.debug(f"Sending non-streaming request to {self.base_url}/completion")
                response = await self.client.post(
                    f"{self.base_url}/completion",
                    json={**payload, "stream": False},
                    timeout=self.request_timeout_seconds
                )
                response.raise_for_status()
                result = response.json()
                content = result.get("content", "")
                if content:
                    yield content
                            
        except httpx.ReadTimeout as e:
            self.logger.warning(f"Mixtral streaming timeout: {e}. Falling back to non-stream request")
            try:
                response = await self.client.post(
                    f"{self.base_url}/completion",
                    json={**payload, "stream": False},
                    timeout=self.request_timeout_seconds
                )
                response.raise_for_status()
                result = response.json()
                content = result.get("content", "")
                if content:
                    yield content
            except Exception as e2:
                self.logger.error(f"Mixtral fallback error: {e2}")
                yield f"Error: {type(e2).__name__}: {e2}"
        except Exception as e:
            self.logger.error(f"Mixtral generation error: {e}")
            import traceback
            self.logger.error(f"Mixtral generation traceback: {traceback.format_exc()}")
            yield f"Error: {type(e).__name__}: {e}"
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Mixtral health check failed: {e}")
            return False 