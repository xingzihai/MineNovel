# Phase 0 执行指令

> 执行者：Phase 0 Agent
> 角色：基础设施搭建专员
> 预计工时：1-2 小时

---

## 一、阶段目标

搭建 MineNovel 项目的基础结构，复制核心可复用代码，建立验证环境。

---

## 二、任务清单

### 任务 0.1：创建源代码目录结构

**指令**：

在 `MineNovel/` 下创建以下目录结构：

```
src/
├── core/                    # 第一层：基础设施
│   ├── __init__.py
│   ├── events.py            # 事件模型（从 Strategos 复制）
│   ├── event_store.py       # 事件存储（从 Strategos 复制）
│   └── llm_client.py        # LLM 调用层（预留）
│
├── world/                   # 第二层：世界观
│   ├── __init__.py
│   └── time_sandbox.py      # 时间沙箱（从 Strategos 复制）
│
├── agents/                  # 第三层：角色
│   ├── __init__.py
│   └── character.py         # 角色定义（从 ReplicantLife 复制）
│
├── story/                   # 第四层：故事
│   └── __init__.py
│
├── narrative/               # 第五层：叙事
│   └── __init__.py
│
└── review/                  # 第六层：审核
    └── __init__.py
```

**验证方式**：
- 所有目录存在
- 所有 `__init__.py` 文件存在

---

### 任务 0.2：复制 Strategos 核心代码

**指令**：

从 `strategos-reference/core/` 复制以下文件到 `src/core/` 和 `src/world/`：

| 源文件 | 目标文件 | 改动要求 |
|-------|---------|---------|
| `events.py` | `src/core/events.py` | 保持不变，添加中文注释 |
| `event_store.py` | `src/core/event_store.py` | 保持不变，添加中文注释 |
| `time.py` | `src/world/time_sandbox.py` | 重命名类 `SimulationClock` → `TimeSandboxClock` |

**验证方式**：
```python
# 在 src/ 目录下运行
python -c "from core.events import Event, EventType; print('events.py OK')"
python -c "from core.event_store import EventStore; print('event_store.py OK')"
python -c "from world.time_sandbox import TimeSandboxClock; print('time_sandbox.py OK')"
```

---

### 任务 0.3：复制 ReplicantLife Agent 代码

**指令**：

从 `replicantlife-reference/src/agents.py` 复制到 `src/agents/character.py`：

1. 复制 `Agent` 类
2. 重命名为 `Character`
3. 移除对 `matrix` 的依赖（改为可选参数）
4. 保留以下核心方法：
   - `__init__`
   - `getMemories`
   - `addMemory`
   - `update_goals`
   - `decide`
   - `meta_cognize`
   - `evaluate_progress`

**验证方式**：
```python
# 在 src/ 目录下运行
python -c "from agents.character import Character; c = Character({'name': 'Test'}); print('character.py OK')"
```

---

### 任务 0.4：创建测试骨架

**指令**：

创建 `tests/` 目录和以下测试文件：

```
tests/
├── __init__.py
├── test_events.py           # 测试事件模型
├── test_event_store.py      # 测试事件存储
├── test_time_sandbox.py     # 测试时间沙箱
└── test_character.py        # 测试角色类
```

每个测试文件至少包含一个基础测试用例：

```python
# test_events.py 示例
def test_event_creation():
    from src.core.events import Event, EventType
    event = Event(event_type=EventType.SIMULATION_STARTED, simulation_time=0.0, data={})
    assert event.event_type == EventType.SIMULATION_STARTED
```

**验证方式**：
```bash
# 在项目根目录运行
python -m pytest tests/ -v
```

---

### 任务 0.5：创建 requirements.txt

**指令**：

创建 `requirements.txt` 文件：

```txt
# 核心依赖
aiosqlite>=0.19.0
pydantic>=2.0.0

# 测试
pytest>=7.0.0
pytest-asyncio>=0.21.0

# 工具
python-dotenv>=1.0.0
rich>=13.0.0
```

**验证方式**：
```bash
pip install -r requirements.txt
```

---

## 三、验收标准

| 标准 | 验证命令 |
|-----|---------|
| 目录结构完整 | `ls src/core src/world src/agents src/story src/narrative src/review` |
| Strategos 代码可导入 | `python -c "from src.core.events import Event"` |
| ReplicantLife 代码可导入 | `python -c "from src.agents.character import Character"` |
| 测试通过 | `python -m pytest tests/ -v` |
| 依赖安装成功 | `pip list | grep aiosqlite` |

---

## 四、禁止事项

1. ❌ 不要修改 `*-reference/` 目录下的任何文件
2. ❌ 不要安装额外的未列出的依赖
3. ❌ 不要删除或移动 `memory-bank/` 下的文档
4. ❌ 不要创建超出任务范围的文件

---

## 五、遇到问题时的处理

### 如果 Strategos 代码有导入错误

1. 检查是否缺少依赖
2. 如果是内部导入问题，修改导入路径
3. 记录问题到汇报中

### 如果 ReplicantLife 代码依赖 `matrix`

1. 将 `matrix` 改为可选参数
2. 在方法中添加 `if self.matrix is None: return` 的保护

### 如果测试失败

1. 记录失败原因
2. 尝试修复（不要跳过测试）
3. 如果无法修复，在汇报中说明

---

## 六、汇报格式

完成后，请按以下格式汇报：

```markdown
# Phase 0 执行汇报

## 执行摘要

- 开始时间：YYYY-MM-DD HH:MM
- 结束时间：YYYY-MM-DD HH:MM
- 状态：成功 / 部分成功 / 失败

## 任务完成情况

| 任务 | 状态 | 备注 |
|-----|------|------|
| 0.1 创建目录结构 | ✅ | |
| 0.2 复制 Strategos 代码 | ✅ | |
| 0.3 复制 ReplicantLife 代码 | ✅ | |
| 0.4 创建测试骨架 | ✅ | |
| 0.5 创建 requirements.txt | ✅ | |

## 验收结果

| 标准 | 结果 |
|-----|------|
| 目录结构完整 | ✅ |
| Strategos 代码可导入 | ✅ |
| ReplicantLife 代码可导入 | ✅ |
| 测试通过 | ✅ |
| 依赖安装成功 | ✅ |

## 遇到的问题

1. 问题描述
   - 原因：
   - 解决方案：
   - 状态：已解决 / 待解决

## 修改记录

记录对参考代码的任何修改：

1. 文件：`src/world/time_sandbox.py`
   - 修改：类名 `SimulationClock` → `TimeSandboxClock`
   - 原因：命名更符合小说场景

## 下一步建议

[可选] 对 Phase 1 的建议或注意事项
```

---

## 七、联系参谋负责人

如果遇到无法解决的问题，请：

1. 记录问题描述
2. 列出已尝试的解决方案
3. 等待进一步指令

---

## 附录：参考文件位置

```
strategos-reference/
├── core/
│   ├── events.py          ← 复制到 src/core/events.py
│   ├── event_store.py     ← 复制到 src/core/event_store.py
│   └── time.py            ← 复制到 src/world/time_sandbox.py

replicantlife-reference/
└── src/
    └── agents.py          ← 复制到 src/agents/character.py
```

---

**开始执行！完成后请按汇报格式提交结果。**