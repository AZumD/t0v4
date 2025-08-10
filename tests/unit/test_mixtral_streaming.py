import asyncio
import json
import types
import pytest

from tova.brains.mixtral_client import MixtralClient


class _FakeStreamCM:
    def __init__(self, status_code: int, lines: list[str]):
        self.status_code = status_code
        self._lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def aiter_lines(self):
        for line in self._lines:
            # Simulate network delay slightly
            await asyncio.sleep(0)
            yield line

    async def aread(self):
        return "".encode()


class _FakeClient:
    def __init__(self, stream_lines: list[str] | None = None, json_obj: dict | None = None, status_code: int = 200):
        self._stream_lines = stream_lines
        self._json_obj = json_obj
        self._status_code = status_code

    def stream(self, method: str, url: str, json: dict, headers: dict, timeout: float):
        assert method == "POST"
        assert "/completion" in url
        return _FakeStreamCM(self._status_code, self._stream_lines or [])

    async def post(self, url: str, json: dict, headers: dict, timeout: float):
        class _Resp:
            def __init__(self, status: int, obj: dict | None):
                self.status_code = status
                self._obj = obj
                import json as _json
                self.text = _json.dumps(obj) if obj is not None else ""

            def json(self):
                return self._obj
        return _Resp(self._status_code, self._json_obj)


@pytest.mark.asyncio
async def test_streaming_yields_only_content_field(monkeypatch):
    # Simulate llama.cpp SSE with data: prefix and content field
    lines = [
        "data: {\"content\": \"Hel\", \"stop\": false}",
        "data: {\"content\": \"lo \", \"stop\": false}",
        "data: {\"content\": \"world\", \"stop\": false}",
        "data: {\"stop\": true}",
    ]
    client = MixtralClient(base_url="http://localhost:8000")
    client.client = _FakeClient(stream_lines=lines)

    chunks = []
    async for c in client.generate_response("hi", stream=True):
        chunks.append(c)

    assert chunks == ["Hel", "lo ", "world"]


@pytest.mark.asyncio
async def test_streaming_ollama_response_key(monkeypatch):
    # Simulate Ollama-like streaming with response/done fields
    lines = [
        json.dumps({"response": "He", "done": False}),
        json.dumps({"response": "llo", "done": False}),
        json.dumps({"response": "!", "done": True}),
    ]
    client = MixtralClient(base_url="http://localhost:8000")
    client.client = _FakeClient(stream_lines=lines)

    chunks = []
    async for c in client.generate_response("hi", stream=True):
        chunks.append(c)

    assert chunks == ["He", "llo", "!"]


@pytest.mark.asyncio
async def test_non_streaming_single_json(monkeypatch):
    # Non-streaming full JSON response with content
    json_obj = {"content": "Hello from JSON", "stop": True}
    client = MixtralClient(base_url="http://localhost:8000")
    client.client = _FakeClient(json_obj=json_obj)

    chunks = []
    async for c in client.generate_response("hi", stream=False):
        chunks.append(c)

    assert chunks == ["Hello from JSON"] 