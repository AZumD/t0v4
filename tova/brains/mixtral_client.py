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
            async with self.client.stream(
                "POST", 
                f"{self.base_url}/completion",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if "content" in chunk:
                                yield chunk["content"]
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            self.logger.error(f"Mixtral generation error: {e}")
            yield f"Error: {str(e)}"
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Mixtral health check failed: {e}")
            return False 