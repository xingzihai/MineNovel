# Phase 1.5 执行指令

> 执行者：Phase 1.5 Agent
> 角色：基础设施运维专员
> 预计工时：30-45 分钟
> 前置条件：Phase 1 已完成

---

## 一、阶段目标

搭建本地 LLM API 代理（LiteLLM），实现：
- 统一管理所有 LLM API Key
- 多模型路由（Writer 用 Claude，Auditor 用 GPT-4o）
- 请求缓存和日志追踪
- 代码无需硬编码 API Key

---

## 二、前置验证

```bash
cd MineNovel
python -m pytest tests/ -v
```

**预期结果**：所有测试通过

---

## 三、任务清单

### 任务 1.5.1：创建 LiteLLM 配置文件

**指令**：

在项目根目录创建 `litellm_config.yaml`：

```yaml
model_list:
  # 小说写作 - 使用 Claude（创意能力强）
  - model_name: writer
    litellm_params:
      model: claude-3-opus-20240229
      api_key: os.environ/ANTHROPIC_API_KEY
  
  # 审计校验 - 使用 GPT-4o（便宜快速）
  - model_name: auditor
    litellm_params:
      model: gpt-4o
      api_key: os.environ/OPENAI_API_KEY
  
  # 规划 - 使用 GPT-4 Turbo
  - model_name: planner
    litellm_params:
      model: gpt-4-turbo
      api_key: os.environ/OPENAI_API_KEY
  
  # 角色内驱力 - 使用 Claude Sonnet（平衡）
  - model_name: character
    litellm_params:
      model: claude-3-sonnet-20240229
      api_key: os.environ/ANTHROPIC_API_KEY
  
  # 本地模型（可选，需要 Ollama）
  - model_name: local
    litellm_params:
      model: ollama/llama3
      api_base: http://localhost:11434

general_settings:
  master_key: sk-minenovel-proxy-2024
  database_url: sqlite:///./data/litellm.db
  drop_params: True  # 自动删除不支持的参数

router_settings:
  routing_strategy: simple-shuffle  # 简单轮询
```

---

### 任务 1.5.2：创建 Docker Compose 配置

**指令**：

创建 `docker-compose.litellm.yml`：

```yaml
version: '3.8'

services:
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    container_name: minenovel-litellm
    ports:
      - "4000:4000"
    volumes:
      - ./litellm_config.yaml:/app/config.yaml
      - ./data/litellm:/app/data
    environment:
      - LITELLM_MASTER_KEY=sk-minenovel-proxy-2024
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    command: ["--config", "/app/config.yaml", "--port", "4000"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

### 任务 1.5.3：创建启动脚本

**指令**：

创建 `scripts/start_proxy.sh`（Linux/Mac）：

```bash
#!/bin/bash
# 启动 LiteLLM 代理

echo "Starting LiteLLM proxy..."

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and fill in your API keys"
    exit 1
fi

# 加载环境变量
export $(cat .env | grep -v '^#' | xargs)

# 启动代理
litellm --config litellm_config.yaml --port 4000
```

创建 `scripts/start_proxy.ps1`（Windows）：

```powershell
# 启动 LiteLLM 代理

Write-Host "Starting LiteLLM proxy..."

# 检查 .env 文件
if (-not (Test-Path .env)) {
    Write-Host "Error: .env file not found"
    Write-Host "Please copy .env.example to .env and fill in your API keys"
    exit 1
}

# 加载环境变量
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}

# 启动代理
litellm --config litellm_config.yaml --port 4000
```

---

### 任务 1.5.4：更新环境变量模板

**指令**：

更新 `.env.example`：

```env
# ============================================
# MineNovel 环境变量配置
# ============================================

# LLM API Keys（用于 LiteLLM 代理）
ANTHROPIC_API_KEY=your-anthropic-key-here
OPENAI_API_KEY=your-openai-key-here

# 本地代理配置（使用代理后只需配置这些）
LLM_BASE_URL=http://localhost:4000
LLM_API_KEY=sk-minenovel-proxy-2024

# 可选：直接调用（不使用代理时）
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4

# 存储路径
STORAGE_PATH=./data

# 日志级别
LOG_LEVEL=INFO
```

---

### 任务 1.5.5：更新项目配置

**指令**：

更新 `src/core/config.py`，添加代理支持：

```python
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

class LLMConfig(BaseModel):
    # 代理模式（推荐）
    base_url: str = "http://localhost:4000"
    api_key: str = "sk-minenovel-proxy-2024"
    
    # 直接模式（备用）
    provider: str = "openai"
    model: str = "gpt-4"
    
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # 模型别名（通过代理路由）
    writer_model: str = "writer"        # Claude Opus
    auditor_model: str = "auditor"      # GPT-4o
    planner_model: str = "planner"      # GPT-4 Turbo
    character_model: str = "character"  # Claude Sonnet

class AppConfig(BaseModel):
    llm: LLMConfig
    storage_path: str = "./data"
    log_level: str = "INFO"

def load_config() -> AppConfig:
    """加载配置"""
    load_dotenv()
    
    return AppConfig(
        llm=LLMConfig(
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:4000"),
            api_key=os.getenv("LLM_API_KEY", "sk-minenovel-proxy-2024"),
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-4"),
        ),
        storage_path=os.getenv("STORAGE_PATH", "./data"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
```

---

### 任务 1.5.6：创建代理客户端工具

**指令**：

创建 `src/core/proxy_client.py`：

```python
"""LiteLLM 代理客户端工具"""

from openai import OpenAI
from typing import List, Dict, Any, Optional
from .config import load_config

class ProxyClient:
    """LiteLLM 代理客户端"""
    
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
        """同步调用"""
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
        """使用预设模型调用"""
        model_map = {
            "writer": self.config.llm.writer_model,
            "auditor": self.config.llm.auditor_model,
            "planner": self.config.llm.planner_model,
            "character": self.config.llm.character_model,
        }
        model = model_map.get(model_type, self.config.llm.model)
        return self.chat(model, messages, **kwargs)

# 全局实例
proxy_client = ProxyClient()
```

---

### 任务 1.5.7：更新依赖

**指令**：

更新 `requirements.txt`：

```txt
# 核心依赖
aiosqlite>=0.19.0
pydantic>=2.0.0
openai>=1.0.0
anthropic>=0.18.0
python-dotenv>=1.0.0

# LiteLLM 代理
litellm>=1.0.0

# 测试
pytest>=7.0.0
pytest-asyncio>=0.21.0

# 工具
rich>=13.0.0
```

---

### 任务 1.5.8：创建测试

**指令**：

创建 `tests/test_proxy_client.py`：

```python
"""代理客户端测试"""

import pytest
from unittest.mock import Mock, patch
from src.core.proxy_client import ProxyClient

def test_proxy_client_singleton():
    """测试单例模式"""
    client1 = ProxyClient()
    client2 = ProxyClient()
    assert client1 is client2

def test_proxy_client_model_mapping():
    """测试模型映射"""
    client = ProxyClient()
    assert client.config.llm.writer_model == "writer"
    assert client.config.llm.auditor_model == "auditor"

@patch('src.core.proxy_client.ProxyClient.chat')
def test_chat_with_model(mock_chat):
    """测试带模型类型的调用"""
    mock_chat.return_value = "测试响应"
    
    client = ProxyClient()
    result = client.chat_with_model("writer", [{"role": "user", "content": "test"}])
    
    assert result == "测试响应"
    mock_chat.assert_called_once()
```

---

## 四、验收标准

| 标准 | 验证命令 |
|-----|---------|
| 配置文件存在 | `ls litellm_config.yaml docker-compose.litellm.yml` |
| 脚本可执行 | `cat scripts/start_proxy.sh` |
| 代理客户端可导入 | `python -c "from src.core.proxy_client import proxy_client"` |
| 测试通过 | `python -m pytest tests/test_proxy_client.py -v` |

---

## 五、使用说明（完成后）

### 启动代理

```bash
# 方式1：直接启动（需要先 pip install litellm）
./scripts/start_proxy.sh

# 方式2：Docker 启动
docker-compose -f docker-compose.litellm.yml up -d
```

### 验证代理运行

```bash
curl http://localhost:4000/health
```

### 在代码中使用

```python
from src.core.proxy_client import proxy_client

# 使用 writer 模型（自动路由到 Claude）
response = proxy_client.chat_with_model(
    "writer",
    [{"role": "user", "content": "写一段小说开头"}]
)

# 使用 auditor 模型（自动路由到 GPT-4o）
response = proxy_client.chat_with_model(
    "auditor",
    [{"role": "user", "content": "检查这段文字的连续性问题"}]
)
```

---

## 六、禁止事项

1. ❌ 不要在代码中硬编码 API Key
2. ❌ 不要提交 `.env` 文件
3. ❌ 不要提交真实的 API Key

---

## 七、汇报格式

完成后，请按以下格式汇报：

```markdown
# Phase 1.5 执行汇报

## 执行摘要

- 开始时间：YYYY-MM-DD HH:MM
- 结束时间：YYYY-MM-DD HH:MM
- 状态：成功 / 部分成功 / 失败

## 任务完成情况

| 任务 | 状态 | 备注 |
|-----|------|------|
| 1.5.1 创建 LiteLLM 配置文件 | ✅ | |
| 1.5.2 创建 Docker Compose 配置 | ✅ | |
| 1.5.3 创建启动脚本 | ✅ | |
| 1.5.4 更新环境变量模板 | ✅ | |
| 1.5.5 更新项目配置 | ✅ | |
| 1.5.6 创建代理客户端工具 | ✅ | |
| 1.5.7 更新依赖 | ✅ | |
| 1.5.8 创建测试 | ✅ | |

## 新增文件

- litellm_config.yaml
- docker-compose.litellm.yml
- scripts/start_proxy.sh
- scripts/start_proxy.ps1
- src/core/proxy_client.py
- tests/test_proxy_client.py

## 验收结果

| 标准 | 结果 |
|-----|------|
| 配置文件存在 | ✅ |
| 脚本可执行 | ✅ |
| 代理客户端可导入 | ✅ |
| 测试通过 | ✅ |

## 下一步建议

[可选] 对后续阶段的建议
```

---

**开始执行！完成后请按汇报格式提交结果。**