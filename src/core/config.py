# core/config.py
"""
Configuration Management Module

Features:
- Environment variable loading
- Pydantic validation
- .env file support
- LiteLLM proxy support
"""

from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
load_dotenv()


class LLMConfig(BaseModel):
    """LLM configuration"""
    # 代理模式（推荐）
    base_url: str = Field(default="http://localhost:4000", description="LiteLLM proxy endpoint")
    api_key: str = Field(default="sk-minenovel-proxy-2024", description="Proxy API key")
    
    # 直接模式（备用）
    provider: str = Field(default="openai", description="LLM provider")
    model: str = Field(default="gpt-4", description="Model name")
    
    max_tokens: int = Field(default=4096, description="Maximum output tokens")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    stream: bool = Field(default=True, description="Use streaming by default")
    
    # 模型别名（通过代理路由）
    writer_model: str = Field(default="writer", description="Claude Opus for creative writing")
    auditor_model: str = Field(default="auditor", description="GPT-4o for review/audit")
    planner_model: str = Field(default="planner", description="GPT-4 Turbo for planning")
    character_model: str = Field(default="character", description="Claude Sonnet for character")


class StorageConfig(BaseModel):
    """Storage configuration"""
    data_path: str = Field(default="./data", description="Data storage path")
    state_path: str = Field(default="./data/state", description="State storage path")
    memory_path: str = Field(default="./data/memory", description="Memory storage path")


class AppConfig(BaseModel):
    """Application configuration"""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")


def load_config(env_file: Optional[str] = None) -> AppConfig:
    """
    Load configuration from environment
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        AppConfig instance
    """
    if env_file:
        load_dotenv(env_file)
    
    # Build LLM config with proxy support
    llm_config = LLMConfig(
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:4000"),
        api_key=os.getenv("LLM_API_KEY", "sk-minenovel-proxy-2024"),
        provider=os.getenv("LLM_PROVIDER", "openai"),
        model=os.getenv("LLM_MODEL", "gpt-4"),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        stream=os.getenv("LLM_STREAM", "true").lower() in ("true", "1", "yes"),
        writer_model=os.getenv("LLM_WRITER_MODEL", "writer"),
        auditor_model=os.getenv("LLM_AUDITOR_MODEL", "auditor"),
        planner_model=os.getenv("LLM_PLANNER_MODEL", "planner"),
        character_model=os.getenv("LLM_CHARACTER_MODEL", "character"),
    )
    
    # Build storage config
    storage_config = StorageConfig(
        data_path=os.getenv("STORAGE_DATA_PATH", "./data"),
        state_path=os.getenv("STORAGE_STATE_PATH", "./data/state"),
        memory_path=os.getenv("STORAGE_MEMORY_PATH", "./data/memory"),
    )
    
    # Build app config
    config = AppConfig(
        llm=llm_config,
        storage=storage_config,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        debug=os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
    )
    
    return config


# Global config instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get global config instance"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_config(config: AppConfig) -> None:
    """Set global config instance"""
    global _config
    _config = config


def reset_config() -> None:
    """Reset global config"""
    global _config
    _config = None