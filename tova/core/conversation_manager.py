"""Conversation context window management."""
from __future__ import annotations

from typing import Deque, Tuple
from collections import deque


class ConversationManager:
    """Maintains a limited history of (role, content) tuples."""

    def __init__(self, max_messages: int = 20) -> None:
        self.max_messages = max_messages
        self.messages: Deque[Tuple[str, str]] = deque(maxlen=max_messages)

    def add(self, role: str, content: str) -> None:
        self.messages.append((role, content))

    def get_window(self) -> Deque[Tuple[str, str]]:
        return self.messages 