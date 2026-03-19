"""LiteLLM 代理客户端工具

提供统一的 LLM 调用接口，支持：
- 单例模式
- 模型别名路由（writer -> Claude, auditor -> GPT-4o）
- 同步和异步调用
"""

from openai import OpenAI
from typing import List, Dict, Any, Optional
from .config import load_config, get_config


class ProxyClient:
    """LiteLLM 代理客户端
    
    使用方式：
        from src.core.proxy_client import proxy_client
        
        # 使用 writer 模型（自动路由到 Claude）
        response = proxy_client.chat_with_model(
            "writer",
            [{"role": "user", "content": "写一段小说开头"}]
        )
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            config = load_config()
            cls._instance.client = OpenAI(
                base_url=config.llm.base_url,
                api_key=config.llm.api_key,
            )
            cls._instance.config = config
        return cls._instance
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """同步调用 LLM
        
        Args:
            model: 模型名称（可以是别名或实际模型名）
            messages: 消息列表
            **kwargs: 其他参数（temperature, max_tokens 等）
            
        Returns:
            模型响应文本
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content
    
    def chat_with_model(
        self,
        model_type: str,  # "writer", "auditor", "planner", "character"
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """使用预设模型调用
        
        Args:
            model_type: 模型类型别名
                - "writer": Claude Opus（创意写作）
                - "auditor": GPT-4o（审计校验）
                - "planner": GPT-4 Turbo（规划）
                - "character": Claude Sonnet（角色内驱力）
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            模型响应文本
        """
        model_map = {
            "writer": self.config.llm.writer_model,
            "auditor": self.config.llm.auditor_model,
            "planner": self.config.llm.planner_model,
            "character": self.config.llm.character_model,
        }
        model = model_map.get(model_type, self.config.llm.model)
        return self.chat(model, messages, **kwargs)
    
    def get_model_name(self, model_type: str) -> str:
        """获取模型别名对应的实际名称"""
        model_map = {
            "writer": self.config.llm.writer_model,
            "auditor": self.config.llm.auditor_model,
            "planner": self.config.llm.planner_model,
            "character": self.config.llm.character_model,
        }
        return model_map.get(model_type, self.config.llm.model)


# 全局实例
proxy_client = ProxyClient()