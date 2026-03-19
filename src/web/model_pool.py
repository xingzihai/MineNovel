"""模型池管理模块

支持：
- 添加/删除/编辑模型
- 启用/禁用模型
- 模型分组
- 设置默认模型
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class ModelProvider(Enum):
    """模型提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    DEEPSEEK = "deepseek"
    MOONSHOT = "moonshot"
    ZHIPU = "zhipu"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class ModelGroup(Enum):
    """模型分组"""
    CREATIVE = "creative"      # 创意写作
    ANALYSIS = "analysis"       # 分析审计
    PLANNING = "planning"       # 规划推理
    CHARACTER = "character"     # 角色扮演
    LOCAL = "local"            # 本地模型
    OTHER = "other"            # 其他


@dataclass
class ModelInstance:
    """模型实例"""
    id: str                           # 唯一标识
    name: str                         # 显示名称
    model: str                        # 实际模型名（如 gpt-4o, claude-3-opus）
    provider: str                     # 提供商
    api_key: str = ""                 # API Key
    base_url: Optional[str] = None    # 自定义 API 端点
    group: str = "other"              # 分组
    enabled: bool = True              # 是否启用
    is_default: bool = False          # 是否为默认模型
    description: str = ""             # 描述
    max_tokens: int = 4096            # 最大 tokens
    supports_stream: bool = True      # 是否支持流式
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelInstance":
        return cls(**data)


@dataclass 
class ModelRoute:
    """模型路由配置"""
    task_type: str          # 任务类型（writer, auditor, planner, character）
    model_id: str           # 关联的模型 ID
    description: str = ""   # 任务描述


class ModelPool:
    """模型池管理器"""
    
    def __init__(self, config_dir: str = "."):
        self.config_dir = Path(config_dir)
        self.config_path = self.config_dir / "model_pool.json"
        self._models: Dict[str, ModelInstance] = {}
        self._routes: Dict[str, ModelRoute] = {}
        self._load()
    
    def _load(self) -> None:
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载模型
            for model_data in data.get("models", []):
                model = ModelInstance.from_dict(model_data)
                self._models[model.id] = model
            
            # 加载路由
            for route_data in data.get("routes", []):
                route = ModelRoute(**route_data)
                self._routes[route.task_type] = route
    
    def _save(self) -> None:
        """保存配置"""
        data = {
            "models": [m.to_dict() for m in self._models.values()],
            "routes": [asdict(r) for r in self._routes.values()]
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ==================== 模型管理 ====================
    
    def add_model(self, model: ModelInstance) -> None:
        """添加模型"""
        self._models[model.id] = model
        if model.is_default:
            self._set_default_internal(model.id)
        self._save()
    
    def remove_model(self, model_id: str) -> bool:
        """删除模型"""
        if model_id in self._models:
            del self._models[model_id]
            # 清理关联的路由
            for task_type, route in list(self._routes.items()):
                if route.model_id == model_id:
                    del self._routes[task_type]
            self._save()
            return True
        return False
    
    def update_model(self, model: ModelInstance) -> None:
        """更新模型"""
        if model.id in self._models:
            self._models[model.id] = model
            if model.is_default:
                self._set_default_internal(model.id)
            self._save()
    
    def get_model(self, model_id: str) -> Optional[ModelInstance]:
        """获取模型"""
        return self._models.get(model_id)
    
    def list_models(self, enabled_only: bool = False, group: Optional[str] = None) -> List[ModelInstance]:
        """列出模型"""
        models = list(self._models.values())
        if enabled_only:
            models = [m for m in models if m.enabled]
        if group:
            models = [m for m in models if m.group == group]
        return models
    
    def get_default_model(self) -> Optional[ModelInstance]:
        """获取默认模型"""
        for model in self._models.values():
            if model.is_default and model.enabled:
                return model
        # 如果没有默认模型，返回第一个启用的模型
        for model in self._models.values():
            if model.enabled:
                return model
        return None
    
    def set_default_model(self, model_id: str) -> bool:
        """设置默认模型"""
        return self._set_default_internal(model_id)
    
    def _set_default_internal(self, model_id: str) -> bool:
        """内部设置默认模型"""
        if model_id not in self._models:
            return False
        # 取消其他模型的默认状态
        for model in self._models.values():
            model.is_default = (model.id == model_id)
        self._save()
        return True
    
    def enable_model(self, model_id: str) -> bool:
        """启用模型"""
        if model_id in self._models:
            self._models[model_id].enabled = True
            self._save()
            return True
        return False
    
    def disable_model(self, model_id: str) -> bool:
        """禁用模型"""
        if model_id in self._models:
            self._models[model_id].enabled = False
            self._save()
            return True
        return False
    
    # ==================== 路由管理 ====================
    
    def set_route(self, task_type: str, model_id: str, description: str = "") -> bool:
        """设置路由"""
        if model_id not in self._models:
            return False
        self._routes[task_type] = ModelRoute(
            task_type=task_type,
            model_id=model_id,
            description=description
        )
        self._save()
        return True
    
    def get_route(self, task_type: str) -> Optional[ModelRoute]:
        """获取路由"""
        return self._routes.get(task_type)
    
    def get_model_for_task(self, task_type: str) -> Optional[ModelInstance]:
        """获取任务对应的模型"""
        route = self._routes.get(task_type)
        if route:
            model = self._models.get(route.model_id)
            if model and model.enabled:
                return model
        # 返回默认模型
        return self.get_default_model()
    
    def list_routes(self) -> List[ModelRoute]:
        """列出所有路由"""
        return list(self._routes.values())
    
    def remove_route(self, task_type: str) -> bool:
        """删除路由"""
        if task_type in self._routes:
            del self._routes[task_type]
            self._save()
            return True
        return False
    
    # ==================== 分组管理 ====================
    
    def get_models_by_group(self, group: str) -> List[ModelInstance]:
        """按分组获取模型"""
        return [m for m in self._models.values() if m.group == group]
    
    def get_groups(self) -> Dict[str, List[ModelInstance]]:
        """获取所有分组及其模型"""
        groups: Dict[str, List[ModelInstance]] = {}
        for model in self._models.values():
            if model.group not in groups:
                groups[model.group] = []
            groups[model.group].append(model)
        return groups
    
    # ==================== 统计 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._models)
        enabled = sum(1 for m in self._models.values() if m.enabled)
        groups = len(set(m.group for m in self._models.values()))
        
        return {
            "total": total,
            "enabled": enabled,
            "disabled": total - enabled,
            "groups": groups,
            "routes": len(self._routes)
        }
    
    # ==================== 导入导出 ====================
    
    def export_to_litellm_config(self) -> Dict[str, Any]:
        """导出为 LiteLLM 配置格式"""
        model_list = []
        
        for model in self._models.values():
            if not model.enabled:
                continue
            
            # 清理 base_url（移除末尾的 /chat/completions 等）
            base_url = model.base_url
            if base_url:
                base_url = base_url.rstrip('/')
                if base_url.endswith('/chat/completions'):
                    base_url = base_url[:-len('/chat/completions')]
                if base_url.endswith('/completions'):
                    base_url = base_url[:-len('/completions')]
            
            # 对于自定义/第三方 OpenAI 兼容 API，使用 openai/ 前缀
            if model.provider in ("custom", "deepseek", "moonshot", "zhipu"):
                litellm_model = f"openai/{model.model}"
            elif model.provider == "ollama":
                litellm_model = f"ollama/{model.model}"
            else:
                litellm_model = f"{model.provider}/{model.model}"
            
            config = {
                "model_name": model.id,
                "litellm_params": {
                    "model": litellm_model,
                }
            }
            
            if model.api_key:
                config["litellm_params"]["api_key"] = model.api_key
            if base_url:
                config["litellm_params"]["api_base"] = base_url
            
            model_list.append(config)
        
        return {
            "model_list": model_list,
            "general_settings": {
                "master_key": "sk-minenovel-proxy-2024",
                "drop_params": True
            }
        }