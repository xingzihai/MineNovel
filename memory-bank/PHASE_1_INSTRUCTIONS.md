# Phase 1 执行指令

> 执行者：Phase 1 Agent
> 角色：第一层基础设施专员
> 预计工时：2-3 小时
> 前置条件：Phase 0 已完成

---

## 一、阶段目标

完善第一层基础设施，实现 LLM 调用层、状态管理器和记忆系统基础。

---

## 二、前置验证

在开始前，请验证 Phase 0 的成果：

```bash
cd MineNovel
python -m pytest tests/ -v
```

**预期结果**：所有测试通过

如果测试失败，请先修复再继续。

---

## 三、任务清单

### 任务 1.1：实现 LLM 客户端

**背景**：

Phase 0 创建了 `src/core/llm_client.py` 预留接口，现在需要实现具体功能。

**参考**：

InkOS 的 LLM 调用逻辑（`inkos-reference/packages/core/src/llm/provider.ts`），但用 Python 实现。

**指令**：

在 `src/core/llm_client.py` 中实现以下功能：

```python
class LLMClient:
    """LLM 调用客户端，支持多 Provider"""
    
    def __init__(self, provider: str, api_key: str, base_url: str = None, model: str = None):
        """
        初始化 LLM 客户端
        
        Args:
            provider: "openai" | "anthropic" | "custom"
            api_key: API 密钥
            base_url: 自定义 endpoint（可选）
            model: 模型名称
        """
        pass
    
    async def chat(self, messages: list, **kwargs) -> str:
        """同步调用"""
        pass
    
    async def chat_stream(self, messages: list, on_chunk: Callable, **kwargs) -> str:
        """流式调用，支持降级"""
        pass
```

**功能要求**：

1. **多 Provider 支持**
   - OpenAI（通过 openai 库）
   - Anthropic（通过 anthropic 库）
   - 自定义 endpoint

2. **Stream 自动降级**
   - 优先使用流式调用
   - 如果流式失败，自动回退到同步调用

3. **错误友好化**
   - 400/401/403/429 错误返回中文提示
   - 记录错误日志

4. **配置管理**
   - 支持从环境变量读取配置
   - 支持 `.env` 文件

**验证方式**：

```python
# tests/test_llm_client.py
import pytest
from src.core.llm_client import LLMClient

def test_llm_client_init():
    client = LLMClient(provider="openai", api_key="test-key", model="gpt-4")
    assert client.provider == "openai"

@pytest.mark.asyncio
async def test_llm_client_chat_mock():
    # 使用 mock 测试，不需要真实 API
    pass
```

**更新 requirements.txt**：

```txt
openai>=1.0.0
anthropic>=0.18.0
```

---

### 任务 1.2：实现状态管理器

**背景**：

需要管理项目的状态快照和回滚能力，支持角色状态、时间状态等的持久化。

**参考**：

InkOS 的状态管理逻辑（`inkos-reference/packages/core/src/state/manager.ts`）。

**指令**：

创建 `src/core/state_manager.py`：

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
import json
import asyncio

@dataclass
class StateSnapshot:
    """状态快照"""
    snapshot_id: str
    timestamp: datetime
    chapter: int
    data: Dict[str, Any]

class StateManager:
    """状态管理器"""
    
    def __init__(self, storage_path: str):
        """
        初始化状态管理器
        
        Args:
            storage_path: 状态存储路径
        """
        pass
    
    async def save_snapshot(self, chapter: int, data: Dict[str, Any]) -> StateSnapshot:
        """保存状态快照"""
        pass
    
    async def load_snapshot(self, chapter: int) -> Optional[StateSnapshot]:
        """加载指定章节的快照"""
        pass
    
    async def list_snapshots(self) -> list[StateSnapshot]:
        """列出所有快照"""
        pass
    
    async def rollback(self, chapter: int) -> bool:
        """回滚到指定章节"""
        pass
    
    async def get_current_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        pass
```

**功能要求**：

1. **快照存储**
   - 以 JSON 格式存储
   - 按章节号命名文件

2. **文件锁**
   - 防止并发写入冲突
   - 使用 `asyncio.Lock`

3. **状态结构**
   ```json
   {
     "chapter": 5,
     "timestamp": "2024-01-15T10:30:00",
     "world_state": {
       "current_time": "2024-01-15T10:30:00",
       "weather": "晴天"
     },
     "characters": {
       "char_001": {
         "location": "城镇广场",
         "hp": 100
       }
     },
     "plot_state": {
       "active_hooks": ["hook_001"],
       "resolved_hooks": []
     }
   }
   ```

**验证方式**：

```python
# tests/test_state_manager.py
import pytest
from src.core.state_manager import StateManager
import tempfile
import os

@pytest.mark.asyncio
async def test_state_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = StateManager(tmpdir)
        
        # 保存快照
        snapshot = await manager.save_snapshot(1, {"test": "data"})
        assert snapshot.chapter == 1
        
        # 加载快照
        loaded = await manager.load_snapshot(1)
        assert loaded.data["test"] == "data"
```

---

### 任务 1.3：创建三层记忆结构

**背景**：

参考 Morpheus 的三层记忆系统，创建小说项目的记忆管理结构。

**参考**：

`memory-bank/EXISTING_SOLUTIONS_ANALYSIS.md` 和 `memory-bank/CORE_CODE_ANALYSIS.md` 中关于 Morpheus 的分析。

**指令**：

创建 `src/core/memory/` 目录结构：

```
src/core/memory/
├── __init__.py
├── memory_store.py       # 记忆存储基类
├── three_layer.py        # 三层记忆管理
└── memory_item.py        # 记忆项定义
```

**数据模型**：

```python
# memory_item.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any
from enum import Enum

class MemoryLayer(str, Enum):
    L1_IDENTITY = "L1"      # 身份层：世界规则、角色硬设定
    L2_RUNTIME = "L2"       # 运行态：状态变化、未决事项
    L3_LOG = "L3"           # 日志层：章节摘要

@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    layer: MemoryLayer
    category: str           # 分类：character, world, plot, etc.
    content: str
    importance: int         # 1-10
    source_chapter: int     # 来源章节
    created_at: datetime
    metadata: Dict[str, Any] = None
```

**三层记忆管理**：

```python
# three_layer.py
from typing import List, Optional
from .memory_item import MemoryItem, MemoryLayer
from .memory_store import MemoryStore

class ThreeLayerMemory:
    """三层记忆管理器"""
    
    def __init__(self, store: MemoryStore):
        self.store = store
        self._l1_cache: List[MemoryItem] = []
        self._l2_cache: List[MemoryItem] = []
        self._l3_cache: List[MemoryItem] = []
    
    async def initialize(self):
        """初始化，加载已有记忆"""
        pass
    
    async def add_memory(self, item: MemoryItem) -> None:
        """添加记忆"""
        pass
    
    async def get_identity(self) -> List[MemoryItem]:
        """获取身份层记忆（L1）"""
        return self._l1_cache
    
    async def get_runtime_state(self) -> List[MemoryItem]:
        """获取运行态记忆（L2）"""
        return self._l2_cache
    
    async def get_recent_logs(self, limit: int = 10) -> List[MemoryItem]:
        """获取最近的日志记忆（L3）"""
        return self._l3_cache[-limit:]
    
    async def search(self, query: str, layer: MemoryLayer = None) -> List[MemoryItem]:
        """搜索记忆"""
        pass
    
    async def build_context_pack(self, chapter: int, token_budget: int = 4000) -> Dict:
        """构建上下文包，用于注入生成"""
        pass
```

**Token 预算分配**（参考 Morpheus）：

```python
_BUDGET_RATIOS = {
    "identity_core": 0.15,      # 15%
    "runtime_state": 0.10,      # 10%
    "memory_compact": 0.15,     # 15%
    "previous_synopsis": 0.10,  # 10%
    "open_threads": 0.10,       # 10%
    "previous_chapters": 0.35,  # 35%
}
```

**验证方式**：

```python
# tests/test_memory.py
import pytest
from src.core.memory import ThreeLayerMemory, MemoryItem, MemoryLayer

@pytest.mark.asyncio
async def test_three_layer_memory():
    memory = ThreeLayerMemory(store=None)
    await memory.initialize()
    
    # 添加记忆
    item = MemoryItem(
        id="mem_001",
        layer=MemoryLayer.L1_IDENTITY,
        category="world",
        content="世界规则：魔法系统消耗精神力",
        importance=10,
        source_chapter=0,
        created_at=datetime.now()
    )
    await memory.add_memory(item)
    
    # 获取身份层
    identity = await memory.get_identity()
    assert len(identity) == 1
```

---

### 任务 1.4：创建配置管理

**指令**：

创建 `src/core/config.py`：

```python
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

class LLMConfig(BaseModel):
    provider: str = "openai"
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-4"
    max_tokens: int = 4000
    temperature: float = 0.7

class AppConfig(BaseModel):
    llm: LLMConfig
    storage_path: str = "./data"
    log_level: str = "INFO"

def load_config() -> AppConfig:
    """加载配置"""
    load_dotenv()
    
    return AppConfig(
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            api_key=os.getenv("LLM_API_KEY", ""),
            base_url=os.getenv("LLM_BASE_URL"),
            model=os.getenv("LLM_MODEL", "gpt-4"),
        ),
        storage_path=os.getenv("STORAGE_PATH", "./data"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
```

创建 `.env.example`：

```env
LLM_PROVIDER=openai
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=
LLM_MODEL=gpt-4
STORAGE_PATH=./data
LOG_LEVEL=INFO
```

---

## 四、验收标准

| 标准 | 验证命令 |
|-----|---------|
| LLM 客户端可初始化 | `python -c "from src.core.llm_client import LLMClient; c = LLMClient('openai', 'test', model='gpt-4')"` |
| 状态管理器可用 | `python -m pytest tests/test_state_manager.py -v` |
| 三层记忆可用 | `python -m pytest tests/test_memory.py -v` |
| 配置可加载 | `python -c "from src.core.config import load_config; c = load_config()"` |
| 所有测试通过 | `python -m pytest tests/ -v` |

---

## 五、禁止事项

1. ❌ 不要调用真实的 LLM API（测试时使用 mock）
2. ❌ 不要提交 `.env` 文件（只提交 `.env.example`）
3. ❌ 不要修改 Phase 0 已完成的文件结构
4. ❌ 不要添加超出任务范围的功能

---

## 六、汇报格式

完成后，请按以下格式汇报：

```markdown
# Phase 1 执行汇报

## 执行摘要

- 开始时间：YYYY-MM-DD HH:MM
- 结束时间：YYYY-MM-DD HH:MM
- 状态：成功 / 部分成功 / 失败

## 任务完成情况

| 任务 | 状态 | 备注 |
|-----|------|------|
| 1.1 实现 LLM 客户端 | ✅ | |
| 1.2 实现状态管理器 | ✅ | |
| 1.3 创建三层记忆结构 | ✅ | |
| 1.4 创建配置管理 | ✅ | |

## 验收结果

| 标准 | 结果 |
|-----|------|
| LLM 客户端可初始化 | ✅ |
| 状态管理器可用 | ✅ |
| 三层记忆可用 | ✅ |
| 配置可加载 | ✅ |
| 所有测试通过 | ✅ |

## 新增文件

列出新增的文件：

- src/core/llm_client.py
- src/core/state_manager.py
- src/core/memory/__init__.py
- src/core/memory/memory_item.py
- src/core/memory/memory_store.py
- src/core/memory/three_layer.py
- src/core/config.py
- tests/test_llm_client.py
- tests/test_state_manager.py
- tests/test_memory.py
- .env.example

## 遇到的问题

[如有问题，按格式记录]

## 下一步建议

[可选] 对 Phase 2 的建议或注意事项
```

---

## 七、参考文件

```
inkos-reference/
└── packages/core/src/llm/provider.ts    # LLM 调用逻辑参考

morpheus-reference/
└── backend/memory/                       # 三层记忆参考
└── backend/services/memory_context.py   # Context Pack 参考
```

---

**开始执行！完成后请按汇报格式提交结果。**