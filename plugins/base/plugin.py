"""Base plugin class for TOVA v4."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePlugin(ABC):
    """All plugins should inherit from this base class."""

    name: str = "base"

    @abstractmethod
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin logic with the provided payload."""
        raise NotImplementedError 