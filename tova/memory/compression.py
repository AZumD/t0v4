"""Context compression logic (placeholder)."""
from __future__ import annotations

from typing import List


def compress_context(messages: List[str], max_messages: int = 10) -> List[str]:
    """Return the last N messages as a naive compression strategy."""
    return messages[-max_messages:] 