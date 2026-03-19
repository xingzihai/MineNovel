"""Web 模块测试"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestConfigManager:
    """测试配置管理器"""
    
    def test_config_manager_init(self, tmp_path):
        """测试初始化"""
        from src.web.config_manager import ConfigManager
        
        cm = ConfigManager(str(tmp_path))
        assert cm.config_dir == tmp_path
        assert cm.env_path == tmp_path / ".env"
        assert cm.litellm_path == tmp_path / "litellm_config.yaml"
    
    def test_load_env_empty(self, tmp_path):
        """测试加载空的 .env 文件"""
        from src.web.config_manager import ConfigManager
        
        cm = ConfigManager(str(tmp_path))
        env_vars = cm.load_env()
        assert env_vars == {}
    
    def test_load_env_with_content(self, tmp_path):
        """测试加载有内容的 .env 文件"""
        from src.web.config_manager import ConfigManager
        
        # 创建测试 .env 文件
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_KEY=test_value\nANTHROPIC_API_KEY=sk-test-123\n")
        
        cm = ConfigManager(str(tmp_path))
        env_vars = cm.load_env()
        
        assert env_vars["TEST_KEY"] == "test_value"
        assert env_vars["ANTHROPIC_API_KEY"] == "sk-test-123"
    
    def test_save_env(self, tmp_path):
        """测试保存 .env 文件"""
        from src.web.config_manager import ConfigManager
        
        cm = ConfigManager(str(tmp_path))
        cm.save_env({"NEW_KEY": "new_value"})
        
        env_vars = cm.load_env()
        assert env_vars["NEW_KEY"] == "new_value"
    
    def test_load_litellm_config_empty(self, tmp_path):
        """测试加载空的 litellm 配置"""
        from src.web.config_manager import ConfigManager
        
        cm = ConfigManager(str(tmp_path))
        config = cm.load_litellm_config()
        
        assert "model_list" in config
        assert config["model_list"] == []
    
    def test_get_model_configs(self, tmp_path):
        """测试获取模型配置"""
        from src.web.config_manager import ConfigManager
        
        # 创建测试文件
        env_file = tmp_path / ".env"
        env_file.write_text("ANTHROPIC_API_KEY=sk-ant-test\n")
        
        litellm_file = tmp_path / "litellm_config.yaml"
        litellm_file.write_text("""
model_list:
  - model_name: writer
    litellm_params:
      model: claude-3-opus
      api_key: os.environ/ANTHROPIC_API_KEY
""")
        
        cm = ConfigManager(str(tmp_path))
        models = cm.get_model_configs()
        
        assert "writer" in models
        assert models["writer"].model == "claude-3-opus"
        assert models["writer"].api_key == "sk-ant-test"


class TestProxyStatus:
    """测试代理状态检查"""
    
    def test_proxy_status_dataclass(self):
        """测试 ProxyStatus 数据类"""
        from src.web.proxy_status import ProxyStatus
        
        status = ProxyStatus(is_running=True, url="http://localhost:4000")
        assert status.is_running is True
        assert status.url == "http://localhost:4000"
        assert status.error is None
    
    def test_check_proxy_status_not_running(self):
        """测试检查未运行的代理"""
        from src.web.proxy_status import check_proxy_status
        
        status = check_proxy_status("http://localhost:9999")
        assert status.is_running is False
        assert status.error is not None
    
    @patch('src.web.proxy_status.requests.get')
    def test_check_proxy_status_running(self, mock_get):
        """测试检查运行中的代理"""
        from src.web.proxy_status import check_proxy_status
        
        # Mock 健康检查响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        status = check_proxy_status()
        
        assert status.is_running is True
    
    def test_test_model_connection_error(self):
        """测试模型连接错误"""
        from src.web.proxy_status import test_model_connection
        
        # 测试不存在的模型
        result = test_model_connection(
            "nonexistent_model",
            base_url="http://localhost:9999"
        )
        
        assert result["success"] is False
        assert "error" in result


class TestModelConfig:
    """测试模型配置数据类"""
    
    def test_model_config_creation(self):
        """测试创建模型配置"""
        from src.web.config_manager import ModelConfig
        
        config = ModelConfig(
            name="writer",
            model="claude-3-opus",
            api_key="sk-test"
        )
        
        assert config.name == "writer"
        assert config.model == "claude-3-opus"
        assert config.api_key == "sk-test"
        assert config.api_base is None
    
    def test_model_config_with_api_base(self):
        """测试带 API base 的模型配置"""
        from src.web.config_manager import ModelConfig
        
        config = ModelConfig(
            name="local",
            model="ollama/llama3",
            api_key="",
            api_base="http://localhost:11434"
        )
        
        assert config.api_base == "http://localhost:11434"


class TestWebModuleInit:
    """测试 Web 模块初始化"""
    
    def test_web_module_imports(self):
        """测试 Web 模块导入"""
        from src.web import (
            ConfigManager,
            ModelConfig,
            check_proxy_status,
            test_model_connection,
            ProxyStatus
        )
        
        assert ConfigManager is not None
        assert ModelConfig is not None
        assert check_proxy_status is not None
        assert test_model_connection is not None
        assert ProxyStatus is not None