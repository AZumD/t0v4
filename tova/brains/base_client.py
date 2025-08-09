"""Base class for LLM client implementations"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
import httpx
import asyncio
import logging


class BaseBrainClient(ABC):
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def health_check(self) -> bool:
        """Check if the brain server is responding"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming response from the brain"""
        pass
    
    async def close(self):
        """Clean up resources"""
        await self.client.aclose() 