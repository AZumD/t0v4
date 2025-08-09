"""Mixtral brain client for primary conversation handling"""
from typing import AsyncGenerator, Dict, Any
import json
import logging
from .base_client import BaseBrainClient


class MixtralClient(BaseBrainClient):
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        self.model_name = "mixtral"
        self.logger = logging.getLogger(__name__)
    
    async def generate_response(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 1000,
        top_p: float = 0.9,
        stream: bool = True,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from Mixtral"""
        
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": stream,
            "stop": ["Human:", "User:", "\n\nHuman:", "\n\nUser:"]
        }
        
        try:
            if stream:
                # Handle streaming response
                self.logger.debug(f"Sending streaming request to {self.base_url}/completion")
                async with self.client.stream(
                    "POST", 
                    f"{self.base_url}/completion",
                    json=payload,
                    timeout=60.0
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            self.logger.debug(f"Received line: {line[:100]}...")
                            # Handle SSE format (data: prefix)
                            if line.startswith("data: "):
                                data = line[6:]  # Remove "data: " prefix
                                if data == "[DONE]":
                                    break
                                
                                try:
                                    chunk = json.loads(data)
                                    if "content" in chunk:
                                        content = chunk["content"]
                                        if content:
                                            self.logger.debug(f"Yielding content: {content}")
                                            yield content
                                except json.JSONDecodeError as e:
                                    self.logger.debug(f"JSON decode error: {e}")
                                    continue
                            else:
                                # Try to parse as regular JSON (non-SSE format)
                                try:
                                    chunk = json.loads(line)
                                    if "content" in chunk:
                                        content = chunk["content"]
                                        if content:
                                            self.logger.debug(f"Yielding content: {content}")
                                            yield content
                                except json.JSONDecodeError:
                                    # Raw text response
                                    if line.strip():
                                        self.logger.debug(f"Yielding raw content: {line.strip()}")
                                        yield line.strip()
            else:
                # Handle non-streaming response
                self.logger.debug(f"Sending non-streaming request to {self.base_url}/completion")
                response = await self.client.post(
                    f"{self.base_url}/completion",
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                content = result.get("content", "")
                if content:
                    self.logger.debug(f"Yielding non-streaming content: {content}")
                    yield content
                            
        except Exception as e:
            self.logger.error(f"Mixtral generation error: {str(e)}")
            import traceback
            self.logger.error(f"Mixtral generation traceback: {traceback.format_exc()}")
            yield f"Error: {str(e)}"
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Mixtral health check failed: {e}")
            return False 