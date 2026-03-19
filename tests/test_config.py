# tests/test_config.py
"""
Tests for Configuration Management
"""

import pytest
import os
from unittest.mock import patch
from src.core.config import (
    LLMConfig,
    StorageConfig,
    AppConfig,
    load_config,
    get_config,
    set_config,
    reset_config,
)


class TestLLMConfig:
    """Test LLMConfig"""
    
    def test_default_values(self):
        """Test default configuration"""
        config = LLMConfig()
        
        # 代理模式默认值
        assert config.base_url == "http://localhost:4000"
        assert config.api_key == "sk-minenovel-proxy-2024"
        # 直接模式默认值
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.stream is True
        # 模型别名
        assert config.writer_model == "writer"
        assert config.auditor_model == "auditor"
        assert config.planner_model == "planner"
        assert config.character_model == "character"
    
    def test_custom_values(self):
        """Test custom configuration"""
        config = LLMConfig(
            provider="anthropic",
            api_key="sk-test",
            model="claude-3-opus",
            max_tokens=8192,
            temperature=0.5,
            stream=False
        )
        
        assert config.provider == "anthropic"
        assert config.api_key == "sk-test"
        assert config.model == "claude-3-opus"
        assert config.max_tokens == 8192
        assert config.temperature == 0.5
        assert config.stream is False
    
    def test_temperature_validation(self):
        """Test temperature range validation"""
        # Valid values
        config = LLMConfig(temperature=0.0)
        assert config.temperature == 0.0
        
        config = LLMConfig(temperature=2.0)
        assert config.temperature == 2.0
        
        # Invalid values should raise
        with pytest.raises(Exception):
            LLMConfig(temperature=-0.1)
        
        with pytest.raises(Exception):
            LLMConfig(temperature=2.1)


class TestStorageConfig:
    """Test StorageConfig"""
    
    def test_default_values(self):
        """Test default storage configuration"""
        config = StorageConfig()
        
        assert config.data_path == "./data"
        assert config.state_path == "./data/state"
        assert config.memory_path == "./data/memory"
    
    def test_custom_values(self):
        """Test custom storage configuration"""
        config = StorageConfig(
            data_path="/custom/data",
            state_path="/custom/state",
            memory_path="/custom/memory"
        )
        
        assert config.data_path == "/custom/data"
        assert config.state_path == "/custom/state"


class TestAppConfig:
    """Test AppConfig"""
    
    def test_default_values(self):
        """Test default app configuration"""
        config = AppConfig()
        
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.storage, StorageConfig)
        assert config.log_level == "INFO"
        assert config.debug is False
    
    def test_nested_config(self):
        """Test nested configuration"""
        config = AppConfig(
            llm=LLMConfig(provider="anthropic", model="claude-3"),
            storage=StorageConfig(data_path="/test"),
            log_level="DEBUG",
            debug=True
        )
        
        assert config.llm.provider == "anthropic"
        assert config.storage.data_path == "/test"
        assert config.log_level == "DEBUG"
        assert config.debug is True


class TestLoadConfig:
    """Test load_config function"""
    
    def test_load_defaults(self):
        """Test loading with default values"""
        # Clear any existing env vars
        env_vars = [
            "LLM_PROVIDER", "LLM_API_KEY", "LLM_BASE_URL",
            "LLM_MODEL", "LLM_MAX_TOKENS", "LLM_TEMPERATURE",
            "STORAGE_DATA_PATH", "LOG_LEVEL", "DEBUG"
        ]
        
        # Use patch to temporarily clear env vars
        with patch.dict(os.environ, {}, clear=False):
            # Remove our env vars
            for var in env_vars:
                os.environ.pop(var, None)
            
            config = load_config()
            
            assert config.llm.provider == "openai"
            assert config.llm.model == "gpt-4"
    
    def test_load_from_env(self):
        """Test loading from environment variables"""
        env = {
            "LLM_PROVIDER": "anthropic",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "claude-3-opus",
            "LLM_MAX_TOKENS": "8192",
            "LLM_TEMPERATURE": "0.5",
            "LLM_STREAM": "false",
            "LOG_LEVEL": "DEBUG",
            "DEBUG": "true",
        }
        
        with patch.dict(os.environ, env, clear=False):
            config = load_config()
            
            assert config.llm.provider == "anthropic"
            assert config.llm.api_key == "sk-test-key"
            assert config.llm.model == "claude-3-opus"
            assert config.llm.max_tokens == 8192
            assert config.llm.temperature == 0.5
            assert config.llm.stream is False
            assert config.log_level == "DEBUG"
            assert config.debug is True


class TestGlobalConfig:
    """Test global config functions"""
    
    def test_get_config(self):
        """Test get_config"""
        reset_config()
        config = get_config()
        
        assert isinstance(config, AppConfig)
    
    def test_set_config(self):
        """Test set_config"""
        reset_config()
        
        custom = AppConfig(
            llm=LLMConfig(provider="custom"),
            debug=True
        )
        
        set_config(custom)
        
        config = get_config()
        assert config.llm.provider == "custom"
        assert config.debug is True
    
    def test_reset_config(self):
        """Test reset_config"""
        set_config(AppConfig(debug=True))
        reset_config()
        
        config = get_config()
        # Should be fresh from env (defaults)
        assert isinstance(config, AppConfig)