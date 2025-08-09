"""Dynamic prompt assembly utilities."""
from __future__ import annotations

from typing import List


def stitch_prompt(segments: List[str]) -> str:
    """Join prompt segments into a single prompt string."""
    return "\n\n".join(s.strip() for s in segments if s and s.strip()) 