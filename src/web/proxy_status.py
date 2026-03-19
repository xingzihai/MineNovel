"""代理状态检查"""

import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ProxyStatus:
    """代理状态"""
    is_running: bool
    url: str
    error: Optional[str] = None
    models: list = field(default_factory=list)


def check_proxy_status(base_url: str = "http://localhost:4000", master_key: str = "sk-minenovel-proxy-2024") -> ProxyStatus:
    """检查代理状态"""
    headers = {"Authorization": f"Bearer {master_key}"}
    try:
        # 检查健康状态
        response = requests.get(f"{base_url}/health", headers=headers, timeout=5)
        if response.status_code == 200:
            # 获取可用模型
            models = []
            try:
                models_response = requests.get(f"{base_url}/v1/models", headers=headers, timeout=5)
                if models_response.status_code == 200:
                    data = models_response.json()
                    models = [m["id"] for m in data.get("data", [])]
            except Exception:
                pass
            
            return ProxyStatus(
                is_running=True,
                url=base_url,
                models=models
            )
        else:
            return ProxyStatus(
                is_running=False,
                url=base_url,
                error=f"HTTP {response.status_code}"
            )
    except requests.exceptions.ConnectionError:
        return ProxyStatus(
            is_running=False,
            url=base_url,
            error="无法连接到代理服务"
        )
    except requests.exceptions.Timeout:
        return ProxyStatus(
            is_running=False,
            url=base_url,
            error="连接超时"
        )
    except Exception as e:
        return ProxyStatus(
            is_running=False,
            url=base_url,
            error=str(e)
        )


def normalize_base_url(url: str) -> str:
    """规范化 base_url，移除多余的路径部分
    
    OpenAI 客户端会自动添加 /chat/completions，所以 base_url 应该只包含基础路径
    """
    if not url:
        return url
    
    # 移除末尾斜杠
    url = url.rstrip('/')
    
    # 移除 /chat/completions 路径
    if url.endswith('/chat/completions'):
        url = url[:-len('/chat/completions')]
    
    # 移除 /completions 路径
    if url.endswith('/completions'):
        url = url[:-len('/completions')]
    
    # 确保 /v1 存在（大多数 API 需要）
    if not url.endswith('/v1') and '/v1' not in url:
        # 检查是否是本地代理或其他特殊 URL
        if not url.startswith('http://localhost') and not url.startswith('http://127.0.0.1'):
            url = url + '/v1'
    
    return url


def test_model_connection(
    model: str,
    base_url: str = "http://localhost:4000",
    api_key: str = "sk-minenovel-proxy-2024",
    test_message: str = "Hello, this is a test."
) -> Dict[str, Any]:
    """通过代理测试模型连接
    
    所有 LLM 调用必须通过代理，不允许直连 API
    """
    try:
        from openai import OpenAI
        
        # 强制使用代理地址，忽略传入的 base_url
        # 代理地址固定为 localhost:4000
        proxy_url = "http://localhost:4000"
        
        client = OpenAI(
            base_url=proxy_url,
            api_key=api_key  # 使用代理的 master key
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": test_message}],
            max_tokens=50
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "model": model,
            "proxy_url": proxy_url
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": model
        }