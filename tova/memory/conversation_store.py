"""Conversation persistence utilities (placeholder)."""
from __future__ import annotations

from pathlib import Path
from typing import List


def save_conversation(conversation_id: str, messages: List[str], base_dir: str = "data/conversations") -> str:
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    path = Path(base_dir) / f"{conversation_id}.txt"
    path.write_text("\n".join(messages), encoding="utf-8")
    return str(path)


def load_conversation(conversation_id: str, base_dir: str = "data/conversations") -> List[str]:
    path = Path(base_dir) / f"{conversation_id}.txt"
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines() 