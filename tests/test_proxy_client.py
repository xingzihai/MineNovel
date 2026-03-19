"""代理客户端测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestProxyClientSingleton:
    """测试单例模式"""
    
    def setup_method(self):
        """每个测试前重置单例"""
        from src.core import proxy_client
        proxy_client.ProxyClient._instance = None
    
    def test_proxy_client_singleton(self):
        """测试单例模式"""
        from src.core.proxy_client import ProxyClient
        
        client1 = ProxyClient()
        client2 = ProxyClient()
        assert client1 is client2
    
    def test_proxy_client_initialization(self):
        """测试初始化"""
        from src.core.proxy_client import ProxyClient
        
        client = ProxyClient()
        assert client.client is not None
        assert client.config is not None


class TestProxyClientModelMapping:
    """测试模型映射"""
    
    def setup_method(self):
        """每个测试前重置单例"""
        from src.core import proxy_client
        proxy_client.ProxyClient._instance = None
    
    def test_proxy_client_model_mapping(self):
        """测试模型映射"""
        from src.core.proxy_client import ProxyClient
        
        client = ProxyClient()
        assert client.config.llm.writer_model == "writer"
        assert client.config.llm.auditor_model == "auditor"
        assert client.config.llm.planner_model == "planner"
        assert client.config.llm.character_model == "character"
    
    def test_get_model_name(self):
        """测试获取模型名称"""
        from src.core.proxy_client import ProxyClient
        
        client = ProxyClient()
        
        assert client.get_model_name("writer") == "writer"
        assert client.get_model_name("auditor") == "auditor"
        assert client.get_model_name("planner") == "planner"
        assert client.get_model_name("character") == "character"
        assert client.get_model_name("unknown") == "gpt-4"  # 默认模型


class TestProxyClientChat:
    """测试聊天功能"""
    
    def setup_method(self):
        """每个测试前重置单例"""
        from src.core import proxy_client
        proxy_client.ProxyClient._instance = None
    
    @patch('src.core.proxy_client.OpenAI')
    def test_chat_with_model(self, mock_openai_class):
        """测试带模型类型的调用"""
        # 设置 mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "测试响应"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # 重新导入以使用 mock
        from src.core import proxy_client
        proxy_client.ProxyClient._instance = None
        
        from src.core.proxy_client import ProxyClient
        client = ProxyClient()
        
        result = client.chat_with_model(
            "writer",
            [{"role": "user", "content": "test"}]
        )
        
        assert result == "测试响应"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.core.proxy_client.OpenAI')
    def test_chat_with_different_models(self, mock_openai_class):
        """测试不同模型的调用"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "响应"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        from src.core import proxy_client
        proxy_client.ProxyClient._instance = None
        
        from src.core.proxy_client import ProxyClient
        client = ProxyClient()
        
        # 测试不同模型类型
        for model_type in ["writer", "auditor", "planner", "character"]:
            result = client.chat_with_model(
                model_type,
                [{"role": "user", "content": "test"}]
            )
            assert result == "响应"


class TestProxyClientConfig:
    """测试配置集成"""
    
    def setup_method(self):
        """每个测试前重置单例"""
        from src.core import proxy_client
        proxy_client.ProxyClient._instance = None
    
    def test_config_default_values(self):
        """测试默认配置值"""
        from src.core.proxy_client import ProxyClient
        
        client = ProxyClient()
        
        assert client.config.llm.base_url == "http://localhost:4000"
        assert client.config.llm.api_key == "sk-minenovel-proxy-2024"
        assert client.config.llm.model == "gpt-4"
        assert client.config.llm.max_tokens == 4096
        assert client.config.llm.temperature == 0.7


class TestGlobalProxyClient:
    """测试全局实例"""
    
    def setup_method(self):
        """每个测试前重置单例"""
        from src.core import proxy_client
        proxy_client.ProxyClient._instance = None
    
    def test_global_proxy_client_exists(self):
        """测试全局实例存在"""
        from src.core.proxy_client import proxy_client
        
        assert proxy_client is not None
        assert hasattr(proxy_client, 'chat')
        assert hasattr(proxy_client, 'chat_with_model')
        assert hasattr(proxy_client, 'get_model_name')