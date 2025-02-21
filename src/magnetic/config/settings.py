"""Configuration settings for the Magnetic application."""

from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Database settings
DATABASE_URL = "sqlite:///./magnetic.db"

@dataclass
class Config:
    """Application configuration."""
    
    # API configurations
    api_keys: Dict[str, str]
    
    # Model configurations
    model_settings: Dict[str, Any]
    
    # Storage configurations
    storage_settings: Dict[str, Any]
    
    # Agent configurations
    agent_settings: Dict[str, Any]

    @classmethod
    def load_from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        # TODO: Implement environment variable loading
        return cls(
            api_keys={},
            model_settings={},
            storage_settings={},
            agent_settings={}
        ) 