"""配置管理模块 - 用于 Web UI"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    model: str
    api_key: str
    api_base: Optional[str] = None


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "."):
        self.config_dir = Path(config_dir)
        self.env_path = self.config_dir / ".env"
        self.litellm_path = self.config_dir / "litellm_config.yaml"
    
    def load_env(self) -> Dict[str, str]:
        """加载 .env 文件"""
        env_vars = {}
        if self.env_path.exists():
            with open(self.env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars
    
    def save_env(self, env_vars: Dict[str, str]) -> None:
        """保存 .env 文件"""
        # 读取原有内容，保留注释
        lines = []
        if self.env_path.exists():
            with open(self.env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # 更新变量
        updated_keys = set()
        for i, line in enumerate(lines):
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in env_vars:
                    lines[i] = f"{key}={env_vars[key]}\n"
                    updated_keys.add(key)
        
        # 添加新变量
        for key, value in env_vars.items():
            if key not in updated_keys:
                lines.append(f"{key}={value}\n")
        
        with open(self.env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def load_litellm_config(self) -> Dict[str, Any]:
        """加载 LiteLLM 配置"""
        if self.litellm_path.exists():
            with open(self.litellm_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {"model_list": [], "general_settings": {}}
    
    def save_litellm_config(self, config: Dict[str, Any]) -> None:
        """保存 LiteLLM 配置"""
        with open(self.litellm_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    def get_model_configs(self) -> Dict[str, ModelConfig]:
        """获取所有模型配置"""
        env_vars = self.load_env()
        litellm_config = self.load_litellm_config()
        
        models = {}
        for item in litellm_config.get("model_list", []):
            model_name = item.get("model_name", "")
            params = item.get("litellm_params", {})
            
            # 从环境变量获取 API Key
            api_key_env = params.get("api_key", "")
            if api_key_env.startswith("os.environ/"):
                env_key = api_key_env.replace("os.environ/", "")
                api_key = env_vars.get(env_key, "")
            else:
                api_key = api_key_env
            
            models[model_name] = ModelConfig(
                name=model_name,
                model=params.get("model", ""),
                api_key=api_key,
                api_base=params.get("api_base")
            )
        
        return models
    
    def update_model_config(self, model_name: str, api_key: str) -> None:
        """更新模型配置"""
        env_vars = self.load_env()
        
        # 确定环境变量名
        env_key_map = {
            "writer": "ANTHROPIC_API_KEY",
            "character": "ANTHROPIC_API_KEY",
            "auditor": "OPENAI_API_KEY",
            "planner": "OPENAI_API_KEY",
            "local": None
        }
        
        env_key = env_key_map.get(model_name)
        if env_key:
            env_vars[env_key] = api_key
        
        # 保存
        self.save_env(env_vars)
    
    def get_config_status(self) -> Dict[str, bool]:
        """获取配置状态"""
        env_vars = self.load_env()
        return {
            "anthropic": bool(env_vars.get("ANTHROPIC_API_KEY")),
            "openai": bool(env_vars.get("OPENAI_API_KEY")),
        }