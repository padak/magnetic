"""Configuration for LLM providers and settings."""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMConfig:
    """Configuration for LLM providers and settings."""
    
    # Default provider
    DEFAULT_PROVIDER = "openai"
    
    # Provider-specific defaults
    PROVIDER_DEFAULTS = {
        "openai": {
            "model": "gpt-3.5-turbo-0125",
            "temperature": 0.7,
            "max_tokens": 4000
        },
        "anthropic": {
            "model": "claude-3-sonnet-20240229",
            "temperature": 0.7,
            "max_tokens": 4000
        },
        "azure": {
            "deployment_name": "gpt-35-turbo",
            "api_version": "2023-05-15",
            "temperature": 0.7,
            "max_tokens": 4000
        }
    }
    
    @classmethod
    def get_provider(cls) -> str:
        """Get the LLM provider from environment or default."""
        return os.getenv("LLM_PROVIDER", cls.DEFAULT_PROVIDER)
    
    @classmethod
    def get_config(cls, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a specific provider.
        
        Args:
            provider: The LLM provider (openai, anthropic, azure)
            
        Returns:
            Configuration dictionary for the provider
        """
        provider = provider or cls.get_provider()
        
        if provider not in cls.PROVIDER_DEFAULTS:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        config = cls.PROVIDER_DEFAULTS[provider].copy()
        
        # Override with environment variables
        if provider == "openai":
            if os.getenv("OPENAI_MODEL"):
                config["model"] = os.getenv("OPENAI_MODEL")
        elif provider == "anthropic":
            if os.getenv("ANTHROPIC_MODEL"):
                config["model"] = os.getenv("ANTHROPIC_MODEL")
        elif provider == "azure":
            if os.getenv("AZURE_DEPLOYMENT_NAME"):
                config["deployment_name"] = os.getenv("AZURE_DEPLOYMENT_NAME")
            if os.getenv("AZURE_API_VERSION"):
                config["api_version"] = os.getenv("AZURE_API_VERSION")
        
        # Common overrides
        if os.getenv("LLM_TEMPERATURE"):
            config["temperature"] = float(os.getenv("LLM_TEMPERATURE"))
        if os.getenv("LLM_MAX_TOKENS"):
            config["max_tokens"] = int(os.getenv("LLM_MAX_TOKENS"))
        
        return config
    
    @classmethod
    def get_agent_config(cls) -> Dict[str, Any]:
        """Get configuration for agents.
        
        Returns:
            Configuration dictionary for agents
        """
        provider = cls.get_provider()
        llm_config = cls.get_config(provider)
        
        return {
            "llm_provider": provider,
            "llm_config": llm_config,
            "cache_ttl": int(os.getenv("CACHE_TTL", "3600")),
            "calls_per_minute": int(os.getenv("CALLS_PER_MINUTE", "1")),
            "max_retries": int(os.getenv("MAX_RETRIES", "3")),
            "max_concurrent_tasks": int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
        } 