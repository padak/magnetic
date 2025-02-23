"""Configuration settings for the Magnetic application."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///magnetic.db")

@dataclass
class Config:
    """Application configuration."""
    
    # Singleton instance
    _instance = None
    
    # API configurations
    api_keys: Dict[str, str]
    
    # Model configurations
    model_settings: Dict[str, Any]
    
    # Storage configurations
    storage_settings: Dict[str, Any]
    
    # Agent configurations
    agent_settings: Dict[str, Any]
    
    # Environment
    debug: bool
    environment: str
    
    @property
    def DATABASE_URL(self) -> str:
        """Get the database URL."""
        return self.storage_settings["database_url"]

    @classmethod
    def get_instance(cls) -> 'Config':
        """Get the singleton instance of Config."""
        if cls._instance is None:
            cls._instance = cls.load_from_env()
        return cls._instance

    @classmethod
    def load_from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        api_keys = {
            "openai": os.getenv("OPENAI_API_KEY", ""),
            "amadeus_key": os.getenv("AMADEUS_API_KEY", ""),
            "amadeus_secret": os.getenv("AMADEUS_API_SECRET", ""),
            "maps": os.getenv("MAPS_API_KEY", ""),
            "weather": os.getenv("WEATHER_API_KEY", ""),
        }
        
        model_settings = {
            "model_name": os.getenv("MODEL_NAME", "gpt-3.5-turbo-0125"),
            "max_tokens": int(os.getenv("MAX_TOKENS", "4000")),
            "temperature": float(os.getenv("TEMPERATURE", "0.7")),
        }
        
        storage_settings = {
            "database_url": DATABASE_URL,
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        }
        
        agent_settings = {
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "log_format": os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            "log_file": os.getenv("LOG_FILE", "magnetic.log"),
        }
        
        return cls(
            api_keys=api_keys,
            model_settings=model_settings,
            storage_settings=storage_settings,
            agent_settings=agent_settings,
            debug=os.getenv("DEBUG", "False").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "development"),
        )

    def validate(self) -> None:
        """Validate the configuration."""
        required_keys = {
            "OPENAI_API_KEY": self.api_keys["openai"],
            "DATABASE_URL": self.storage_settings["database_url"],
            "AMADEUS_API_KEY": self.api_keys["amadeus_key"],
            "AMADEUS_API_SECRET": self.api_keys["amadeus_secret"],
        }
        
        missing_keys = [key for key, value in required_keys.items() if not value]
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")

# Create global config instance
config = Config.get_instance() 