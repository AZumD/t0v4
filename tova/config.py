"""Configuration utilities for TOVA v4.

Loads environment variables and YAML-based personalities/moods/functions.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class Settings:
    env: str = os.getenv("ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "info")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    chromadb_path: str = os.getenv("CHROMADB_PATH", "./data/rag")
    mixtral_api_key: str = os.getenv("MIXTRAL_API_KEY", "")
    phi_api_key: str = os.getenv("PHI_API_KEY", "")


def load_yaml(path: str | Path) -> Dict[str, Any]:
    """Load a YAML file and return a dictionary. Returns empty dict if missing."""
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


settings = Settings() 