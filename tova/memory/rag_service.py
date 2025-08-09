"""RAG operations against a vector store (placeholder)."""
from __future__ import annotations

from typing import List


def retrieve(query: str, top_k: int = 4) -> List[str]:
    """Return placeholder documents for a query."""
    return [f"doc_{i}:{query}" for i in range(top_k)] 