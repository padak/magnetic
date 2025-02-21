"""Tests for configuration module."""

import os
import pytest
from magnetic.config.settings import Config

def test_config_loads_defaults():
    """Test that config loads with default values."""
    config = Config.load_from_env()
    
    assert config.environment == "development"
    assert isinstance(config.debug, bool)
    assert isinstance(config.model_settings["max_tokens"], int)
    assert isinstance(config.model_settings["temperature"], float)

def test_config_loads_custom_values(monkeypatch):
    """Test that config loads custom values from environment."""
    # Set test environment variables
    test_vars = {
        "OPENAI_API_KEY": "test-key",
        "MODEL_NAME": "test-model",
        "MAX_TOKENS": "1000",
        "TEMPERATURE": "0.5",
        "DEBUG": "true",
        "ENVIRONMENT": "testing",
    }
    
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)
    
    config = Config.load_from_env()
    
    assert config.api_keys["openai"] == "test-key"
    assert config.model_settings["model_name"] == "test-model"
    assert config.model_settings["max_tokens"] == 1000
    assert config.model_settings["temperature"] == 0.5
    assert config.debug is True
    assert config.environment == "testing"

def test_config_validation_with_missing_required_keys():
    """Test that config validation raises error for missing required keys."""
    # Create config with empty API key
    config = Config(
        api_keys={"openai": "", "amadeus": "", "maps": "", "weather": ""},
        model_settings={},
        storage_settings={"database_url": ""},
        agent_settings={},
        debug=False,
        environment="testing"
    )
    
    with pytest.raises(ValueError) as exc_info:
        config.validate()
    
    assert "Missing required environment variables" in str(exc_info.value)
    assert "OPENAI_API_KEY" in str(exc_info.value)
    assert "DATABASE_URL" in str(exc_info.value) 