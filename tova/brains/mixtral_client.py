"""Mixtral brain client for primary conversation handling"""
from typing import AsyncGenerator, Dict, Any, List
import os
import logging
import httpx
import json
from .base_client import BaseBrainClient


class MixtralClient(BaseBrainClient):
    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = os.getenv("MIXTRAL_BASE_URL", "http://100.75.248.22:8000")
        super().__init__(base_url)
        self.model_name = "mixtral"
        self.logger = logging.getLogger(__name__)
        self.stream_timeout_seconds = 300
        self.request_timeout_seconds = 300
        # Streaming metrics toggle
        self._stream_log = os.getenv("MIXTRAL_STREAM_LOG", "0") == "1"
    
    def _format_prompt_chatml(self, prompt: str, system_prompt: str = None) -> str:
        """Format prompt using ChatML format for Dolphin Mixtral"""
        if system_prompt:
            return f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant"
        else:
            return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant"
    
    def _resolve_stop_tokens(self, overrides: Dict[str, Any]) -> List[str]:
        # Default stop tokens, ensure no empty strings
        default = ["<|im_end|>", "</s>"]
        env_csv = os.getenv("MIXTRAL_STOP_TOKENS", "")
        env_list = [t.strip() for t in env_csv.split(",") if t.strip()] if env_csv else []
        arg_list = [t for t in overrides.get("stop", []) if isinstance(t, str) and t]
        final = arg_list or env_list or default
        # De-duplicate while preserving order
        seen = set()
        result = []
        for t in final:
            if t not in seen and t:
                seen.add(t)
                result.append(t)
        return result
    
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
                # Hint llama.cpp to cache the prompt prefix to speed up subsequent calls
                "cache_prompt": True,
                # Keep a portion of the prompt cached between requests (system + assistant prefix)
                "n_keep": kwargs.get("n_keep", 1024),
                # Stop tokens, sanitized and from env if provided
                "stop": self._resolve_stop_tokens(kwargs),
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

                    # Optional light metrics
                    first_line = True
                    start_t = None
                    first_token_t = None
                    emitted_chars = 0
                    if self._stream_log:
                        try:
                            import time as _time
                            start_t = _time.perf_counter()
                            self.logger.info("[TOVA] ▶ request sent")
                        except Exception:
                            start_t = None

                    async for raw_line in response.aiter_lines():
                        if raw_line is None:
                            continue
                        line = raw_line.strip()
                        if line == "" or line == "\n":
                            # keep-alive
                            continue
                        if first_line and start_t is not None:
                            first_line = False
                        # Handle SSE prefix if present
                        if line.startswith("data: "):
                            line = line[len("data: ") :].strip()
                        # Allow terminal tokens
                        if line.upper() == "[DONE]":
                            break
                        # Parse JSON chunk (robust)
                        obj = None
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            try:
                                brace_index = line.find("{")
                                last_brace = line.rfind("}")
                                if brace_index != -1 and last_brace != -1 and last_brace > brace_index:
                                    candidate = line[brace_index:last_brace+1]
                                    obj = json.loads(candidate)
                                else:
                                    obj = None
                            except Exception:
                                obj = None
                        if obj is None:
                            # Emit raw text if we failed to decode JSON
                            if line:
                                if self._stream_log and first_token_t is None and start_t is not None:
                                    import time as _time
                                    first_token_t = _time.perf_counter()
                                    self.logger.info(f"[TOVA] ⏱ first token: {(first_token_t - start_t)*1000:.1f} ms")
                                emitted_chars += len(line)
                                yield line
                            continue

                        # Respect terminal signals
                        if obj.get("stop") is True or obj.get("done") is True:
                            final_chunk = obj.get("content") or obj.get("response") or ""
                            if final_chunk:
                                if self._stream_log and first_token_t is None and start_t is not None:
                                    import time as _time
                                    first_token_t = _time.perf_counter()
                                    self.logger.info(f"[TOVA] ⏱ first token: {(first_token_t - start_t)*1000:.1f} ms")
                                emitted_chars += len(final_chunk)
                                yield final_chunk
                            # Log summary metrics
                            if self._stream_log and start_t is not None:
                                import time as _time
                                end_t = _time.perf_counter()
                                elapsed = (end_t - (first_token_t or start_t))
                                toks = max(1, round(emitted_chars / 4))
                                tps = toks / max(elapsed, 1e-3)
                                self.logger.info(f"[TOVA] ✅ stream complete | est tokens={toks} | elapsed={elapsed:.2f}s | ~{tps:.2f} t/s")
                            break

                        chunk = obj.get("content") or obj.get("response") or ""
                        if chunk:
                            if self._stream_log and first_token_t is None and start_t is not None:
                                import time as _time
                                first_token_t = _time.perf_counter()
                                self.logger.info(f"[TOVA] ⏱ first token: {(first_token_t - start_t)*1000:.1f} ms")
                            emitted_chars += len(chunk)
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
            # Try /v1/models first (OpenAI-compatible endpoint)
            try:
                response = await self.client.get(
                    f"{self.base_url}/v1/models",
                    timeout=10.0
                )
                if response.status_code == 200:
                    return True
            except Exception:
                pass
            
            # Fallback to /completion endpoint
            response = await self.client.post(
                f"{self.base_url}/completion",
                json={"prompt": "ping", "n_predict": 1, "stream": False},
                timeout=10.0
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Mixtral health check failed: {e}")
            return False 