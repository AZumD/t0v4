"""Phi API client stub."""
from __future__ import annotations

from typing import Dict


class PhiClient:
    """Lightweight stub for text generation."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or ""

    def generate(self, prompt: str) -> Dict[str, str]:
        return {"model": "phi", "prompt": prompt, "output": "stub"} 