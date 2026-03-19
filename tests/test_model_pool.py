"""模型池测试"""

import pytest
import json
import tempfile
from pathlib import Path
import sys

# 添加项目根目录到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.web.model_pool import (
    ModelPool,
    ModelInstance,
    ModelProvider,
    ModelGroup,
    ModelRoute
)


class TestModelInstance:
    """测试模型实例"""
    
    def test_model_instance_creation(self):
        """测试创建模型实例"""
        model = ModelInstance(
            id="test-gpt4",
            name="GPT-4 测试",
            model="gpt-4",
            provider="openai",
            api_key="sk-test",
            group="creative"
        )
        
        assert model.id == "test-gpt4"
        assert model.name == "GPT-4 测试"
        assert model.model == "gpt-4"
        assert model.provider == "openai"
        assert model.enabled is True
        assert model.is_default is False
    
    def test_model_instance_to_dict(self):
        """测试转换为字典"""
        model = ModelInstance(
            id="test",
            name="Test",
            model="test-model",
            provider="custom"
        )
        
        data = model.to_dict()
        assert data["id"] == "test"
        assert data["name"] == "Test"
    
    def test_model_instance_from_dict(self):
        """测试从字典创建"""
        data = {
            "id": "test",
            "name": "Test Model",
            "model": "test-model",
            "provider": "openai",
            "api_key": "sk-test",
            "base_url": None,
            "group": "other",
            "enabled": True,
            "is_default": False,
            "description": "Test description",
            "max_tokens": 4096,
            "supports_stream": True
        }
        
        model = ModelInstance.from_dict(data)
        assert model.id == "test"
        assert model.name == "Test Model"
        assert model.description == "Test description"


class TestModelPool:
    """测试模型池"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as d:
            yield d
    
    @pytest.fixture
    def model_pool(self, temp_dir):
        """创建模型池实例"""
        return ModelPool(temp_dir)
    
    def test_model_pool_init(self, model_pool):
        """测试初始化"""
        assert model_pool._models == {}
        assert model_pool._routes == {}
    
    def test_add_model(self, model_pool):
        """测试添加模型"""
        model = ModelInstance(
            id="gpt4",
            name="GPT-4",
            model="gpt-4-turbo",
            provider="openai",
            api_key="sk-test"
        )
        
        model_pool.add_model(model)
        
        assert "gpt4" in model_pool._models
        assert model_pool.get_model("gpt4").name == "GPT-4"
    
    def test_remove_model(self, model_pool):
        """测试删除模型"""
        model = ModelInstance(id="test", name="Test", model="test", provider="custom")
        model_pool.add_model(model)
        
        result = model_pool.remove_model("test")
        
        assert result is True
        assert "test" not in model_pool._models
    
    def test_remove_nonexistent_model(self, model_pool):
        """测试删除不存在的模型"""
        result = model_pool.remove_model("nonexistent")
        assert result is False
    
    def test_list_models(self, model_pool):
        """测试列出模型"""
        model1 = ModelInstance(id="m1", name="Model 1", model="m1", provider="openai", enabled=True)
        model2 = ModelInstance(id="m2", name="Model 2", model="m2", provider="anthropic", enabled=False)
        
        model_pool.add_model(model1)
        model_pool.add_model(model2)
        
        all_models = model_pool.list_models()
        assert len(all_models) == 2
        
        enabled_models = model_pool.list_models(enabled_only=True)
        assert len(enabled_models) == 1
        assert enabled_models[0].id == "m1"
    
    def test_set_default_model(self, model_pool):
        """测试设置默认模型"""
        model1 = ModelInstance(id="m1", name="M1", model="m1", provider="openai")
        model2 = ModelInstance(id="m2", name="M2", model="m2", provider="anthropic")
        
        model_pool.add_model(model1)
        model_pool.add_model(model2)
        model_pool.set_default_model("m2")
        
        assert model_pool.get_model("m1").is_default is False
        assert model_pool.get_model("m2").is_default is True
    
    def test_get_default_model(self, model_pool):
        """测试获取默认模型"""
        model = ModelInstance(id="default", name="Default", model="default", provider="openai", is_default=True)
        model_pool.add_model(model)
        
        default = model_pool.get_default_model()
        assert default.id == "default"
    
    def test_enable_disable_model(self, model_pool):
        """测试启用/禁用模型"""
        model = ModelInstance(id="test", name="Test", model="test", provider="custom")
        model_pool.add_model(model)
        
        model_pool.disable_model("test")
        assert model_pool.get_model("test").enabled is False
        
        model_pool.enable_model("test")
        assert model_pool.get_model("test").enabled is True
    
    def test_set_route(self, model_pool):
        """测试设置路由"""
        model = ModelInstance(id="gpt4", name="GPT-4", model="gpt-4", provider="openai")
        model_pool.add_model(model)
        
        result = model_pool.set_route("writer", "gpt4", "创意写作")
        
        assert result is True
        route = model_pool.get_route("writer")
        assert route.model_id == "gpt4"
    
    def test_get_model_for_task(self, model_pool):
        """测试获取任务对应的模型"""
        model = ModelInstance(id="claude", name="Claude", model="claude-3", provider="anthropic", enabled=True)
        model_pool.add_model(model)
        model_pool.set_route("writer", "claude")
        
        task_model = model_pool.get_model_for_task("writer")
        assert task_model.id == "claude"
    
    def test_get_model_for_task_fallback_to_default(self, model_pool):
        """测试任务模型回退到默认模型"""
        model = ModelInstance(id="default", name="Default", model="default", provider="openai", 
                              enabled=True, is_default=True)
        model_pool.add_model(model)
        
        task_model = model_pool.get_model_for_task("unknown_task")
        assert task_model.id == "default"
    
    def test_get_groups(self, model_pool):
        """测试获取分组"""
        m1 = ModelInstance(id="m1", name="M1", model="m1", provider="openai", group="creative")
        m2 = ModelInstance(id="m2", name="M2", model="m2", provider="anthropic", group="creative")
        m3 = ModelInstance(id="m3", name="M3", model="m3", provider="custom", group="analysis")
        
        model_pool.add_model(m1)
        model_pool.add_model(m2)
        model_pool.add_model(m3)
        
        groups = model_pool.get_groups()
        
        assert "creative" in groups
        assert "analysis" in groups
        assert len(groups["creative"]) == 2
        assert len(groups["analysis"]) == 1
    
    def test_get_stats(self, model_pool):
        """测试获取统计信息"""
        m1 = ModelInstance(id="m1", name="M1", model="m1", provider="openai", enabled=True)
        m2 = ModelInstance(id="m2", name="M2", model="m2", provider="anthropic", enabled=False)
        
        model_pool.add_model(m1)
        model_pool.add_model(m2)
        model_pool.set_route("writer", "m1")
        
        stats = model_pool.get_stats()
        
        assert stats["total"] == 2
        assert stats["enabled"] == 1
        assert stats["disabled"] == 1
        assert stats["routes"] == 1
    
    def test_persistence(self, temp_dir):
        """测试持久化"""
        # 创建并保存
        pool1 = ModelPool(temp_dir)
        model = ModelInstance(id="persist", name="Persist", model="persist", provider="openai")
        pool1.add_model(model)
        
        # 重新加载
        pool2 = ModelPool(temp_dir)
        assert "persist" in pool2._models
        assert pool2.get_model("persist").name == "Persist"
    
    def test_export_to_litellm_config(self, model_pool):
        """测试导出 LiteLLM 配置"""
        model = ModelInstance(
            id="gpt4",
            name="GPT-4",
            model="gpt-4-turbo",
            provider="openai",
            api_key="sk-test",
            enabled=True
        )
        model_pool.add_model(model)
        
        config = model_pool.export_to_litellm_config()
        
        assert "model_list" in config
        assert len(config["model_list"]) == 1
        assert config["model_list"][0]["model_name"] == "gpt4"
    
    def test_remove_model_clears_routes(self, model_pool):
        """测试删除模型时清理路由"""
        model = ModelInstance(id="m1", name="M1", model="m1", provider="openai")
        model_pool.add_model(model)
        model_pool.set_route("writer", "m1")
        
        model_pool.remove_model("m1")
        
        assert model_pool.get_route("writer") is None


class TestModelRoute:
    """测试模型路由"""
    
    def test_model_route_creation(self):
        """测试创建路由"""
        route = ModelRoute(
            task_type="writer",
            model_id="claude-3",
            description="创意写作任务"
        )
        
        assert route.task_type == "writer"
        assert route.model_id == "claude-3"
        assert route.description == "创意写作任务"


class TestEnums:
    """测试枚举"""
    
    def test_model_provider_values(self):
        """测试提供商枚举值"""
        assert ModelProvider.OPENAI.value == "openai"
        assert ModelProvider.ANTHROPIC.value == "anthropic"
        assert ModelProvider.OLLAMA.value == "ollama"
        assert ModelProvider.CUSTOM.value == "custom"
    
    def test_model_group_values(self):
        """测试分组枚举值"""
        assert ModelGroup.CREATIVE.value == "creative"
        assert ModelGroup.ANALYSIS.value == "analysis"
        assert ModelGroup.LOCAL.value == "local"