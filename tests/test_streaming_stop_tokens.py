import asyncio
import json
import pytest

from tova.brains.mixtral_client import MixtralClient


class _FakeStreamCM:
    def __init__(self, status_code: int, lines):
        self.status_code = status_code
        self._lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def aiter_lines(self):
        for line in self._lines:
            await asyncio.sleep(0)
            yield line

    async def aread(self):
        return b""


class _FakeClient:
    def __init__(self, stream_lines=None, json_obj=None, status_code: int = 200):
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
async def test_streaming_blank_line_and_stop_true():
    lines = [
        "\n",  # keep-alive blank
        "data: {\"content\": \"Hello\", \"stop\": false}",
        "data: {\"content\": \" there\", \"stop\": false}",
        "data: {\"stop\": true}",
    ]
    client = MixtralClient(base_url="http://localhost:8000")
    client.client = _FakeClient(stream_lines=lines)

    chunks = []
    async for c in client.generate_response("hi", stream=True):
        chunks.append(c)

    assert chunks == ["Hello", " there"]


@pytest.mark.asyncio
async def test_streaming_malformed_then_json_object_late():
    late_obj = "xxx{\"content\":\"Hi\"}yyy"
    lines = [late_obj, json.dumps({"done": True})]
    client = MixtralClient(base_url="http://localhost:8000")
    client.client = _FakeClient(stream_lines=lines)

    chunks = []
    async for c in client.generate_response("hi", stream=True):
        chunks.append(c)

    # Should parse inner JSON and emit "Hi" before done
    assert chunks == ["Hi"]


@pytest.mark.asyncio
async def test_non_streaming_response_content():
    json_obj = {"content": "Full text", "stop": True}
    client = MixtralClient(base_url="http://localhost:8000")
    client.client = _FakeClient(json_obj=json_obj)

    chunks = []
    async for c in client.generate_response("hi", stream=False):
        chunks.append(c)

    assert chunks == ["Full text"] 