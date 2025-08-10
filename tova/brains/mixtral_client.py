"""Mixtral brain client for primary conversation handling"""
from typing import AsyncGenerator, Dict, Any
import os
import logging
import httpx
import json
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
        """Generate response from llama.cpp and yield clean text chunks.

        Behavior:
        - If stream=True (default), use streaming endpoint and parse SSE-like JSON lines.
        - If stream=False, parse full JSON and yield only the "content" field.
        """
        try:
            formatted_prompt = self._format_prompt_chatml(prompt, kwargs.get('system_prompt'))
            use_streaming = kwargs.get("stream", True)

            payload: Dict[str, Any] = {
                "prompt": formatted_prompt,
                "n_predict": kwargs.get("max_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7),
                "stream": use_streaming,
                # Be permissive about stop tokens for chatml
                "stop": kwargs.get("stop", ["<|im_end|>", "</s>"])
            }
            common_headers = {"Content-Type": "application/json"}

            if use_streaming:
                # Encourage immediate flush with SSE headers
                headers = {
                    **common_headers,
                    "Accept": "text/event-stream",
                    "Connection": "keep-alive",
                    "Cache-Control": "no-cache",
                }
                # Stream response as JSON lines (llama.cpp sends SSE: lines prefixed with 'data: ')
                async with self.client.stream(
                    "POST",
                    f"{self.base_url}/completion",
                    json=payload,
                    headers=headers,
                    timeout=self.stream_timeout_seconds,
                ) as response:
                    if response.status_code != 200:
                        yield f"HTTP {response.status_code}: {await response.aread()}"
                        return

                    first_line = True
                    start_t = None
                    try:
                        import time as _time
                        start_t = _time.perf_counter()
                    except Exception:
                        start_t = None

                    async for raw_line in response.aiter_lines():
                        if not raw_line:
                            continue
                        if first_line and start_t is not None:
                            first_line = False
                            try:
                                import time as _time
                                dt_ms = (_time.perf_counter() - start_t) * 1000
                                self.logger.info(f"🎭 MixtralClient: first stream line in {dt_ms:.1f}ms")
                            except Exception:
                                pass
                        line = raw_line.strip()
                        # Handle SSE prefix if present
                        if line.startswith("data: "):
                            line = line[len("data: ") :].strip()
                        # Stop signals
                        if line == "[DONE]" or line == "\n" or line == "":
                            continue
                        if line.upper() == "[DONE]" or line == "{\"stop\": true}":
                            break
                        # Parse JSON chunk
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            # Some builds may wrap JSON in 'data: ' again or send raw content; try best-effort
                            # If it looks like a JSON object is embedded, try to find the first '{'
                            try:
                                brace_index = line.find("{")
                                if brace_index != -1:
                                    obj = json.loads(line[brace_index:])
                                else:
                                    # Treat as plain text token
                                    yield line
                                    continue
                            except Exception:
                                yield line
                                continue

                        if obj.get("stop") is True or obj.get("done") is True:
                            # Final event; do not emit any content if empty
                            chunk = obj.get("content") or obj.get("response") or ""
                            if chunk:
                                yield chunk
                            break

                        chunk = obj.get("content") or obj.get("response") or ""
                        if chunk:
                            yield chunk
            else:
                # Non-streaming: single JSON response
                headers = common_headers
                response = await self.client.post(
                    f"{self.base_url}/completion",
                    json=payload,
                    headers=headers,
                    timeout=self.request_timeout_seconds,
                )
                if response.status_code != 200:
                    yield f"HTTP {response.status_code}: {response.text}"
                    return
                try:
                    data = response.json()
                    content = data.get("content") or data.get("response") or response.text
                except Exception:
                    # Fallback to raw text if json parse fails
                    content = response.text
                if content:
                    yield content
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