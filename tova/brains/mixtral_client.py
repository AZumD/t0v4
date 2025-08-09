"""Mixtral API client stub.

Replace with real HTTP calls and streaming as needed.
"""
from __future__ import annotations

from typing import Dict


class MixtralClient:
    """Lightweight stub for text generation."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or ""

    def generate(self, prompt: str) -> Dict[str, str]:
        return {"model": "mixtral", "prompt": prompt, "output": "stub"} 