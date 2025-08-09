"""Configuration management for TOVA v4"""
import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class Settings:
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8002
    debug: bool = False
    
    # Brain endpoints
    mixtral_url: str = "http://localhost:8000"
    phi_url: str = "http://localhost:8001"
    
    # Model parameters
    mixtral_temperature: float = 0.7
    mixtral_max_tokens: int = 1000
    mixtral_top_p: float = 0.9
    
    phi_temperature: float = 0.3
    phi_max_tokens: int = 500
    
    # Paths
    config_path: str = "config"
    data_path: str = "data"
    log_path: str = "data/logs"
    
    def __post_init__(self):
        # Load from environment variables if available
        self.host = os.getenv("TOVA_HOST", self.host)
        self.port = int(os.getenv("TOVA_PORT", self.port))
        self.debug = os.getenv("TOVA_DEBUG", "false").lower() == "true"
        self.mixtral_url = os.getenv("TOVA_MIXTRAL_URL", self.mixtral_url)
        self.phi_url = os.getenv("TOVA_PHI_URL", self.phi_url)

_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 