# MineNovel 技术吸收路线图

> 基于 InkOS、PlotLine、Morpheus 三个项目的深入分析
> 目标：明确哪些代码可以直接复用，哪些需要改造，哪些必须自建

---

## 一、直接复制即可的代码（节省 ~40% 工作量）

### 1.1 LLM 调用层（InkOS）

**文件**：`packages/core/src/llm/provider.ts`

**可复用功能**：
```typescript
// 多 Provider 支持
- OpenAI / Anthropic / 自定义 endpoint
- Stream 自动降级（中转站不支持 SSE 时回退 sync）
- 部分响应挽救（流中断但有足够内容时返回 PartialResponseError）
- 错误友好化（400/401/403/429 的中文提示）
- 流监控（统计字数、耗时）
- Tool-calling 支持
```

**迁移方式**：直接复制，改为 Python 版本

---

### 1.2 状态快照机制（InkOS）

**文件**：`packages/core/src/state/manager.ts`

**可复用功能**：
```typescript
- 文件锁（acquireBookLock）— 防止并发写入
- 状态快照（snapshotState / restoreState）— 回滚到任意章节
- 配置读写
```

**迁移方式**：直接复制逻辑

---

### 1.3 硬规则校验（InkOS）

**文件**：`packages/core/src/agents/post-write-validator.ts`

**11 条硬规则**：
```
1. 禁止"不是…而是…"句式
2. 禁止破折号
3. 转折词密度 ≤ 1次/3000字
4. 高疲劳词检查
5. 元叙事/编剧旁白检查
6. 分析报告术语检查
7. 作者说教词检查
8. 全场震惊类套话检查
9. 连续"了"字检查
10. 段落长度检查
11. 本书禁忌内容检查
```

**迁移方式**：直接复制

---

### 1.4 风格指纹提取（InkOS）

**文件**：`packages/core/src/agents/style-analyzer.ts`

**纯文本分析（无 LLM 调用）**：
```typescript
- 句长统计（平均值、标准差）
- 段落长度统计
- 词汇多样性（TTR）
- 句首模式
- 修辞特征检测（比喻、排比、反问、夸张、拟人、短句节奏）
```

**迁移方式**：直接复制

---

### 1.5 LogicGraph 数据结构（PlotLine）

**文件**：`backend/models/schemas.py`

```python
class NarrativeNode:
    id: str
    action: str              # 核心动作动词
    actors: List[str]        # 参与实体
    preconditions: List[str] # 前置条件
    postconditions: List[str]# 后置条件
    reasoning: str           # 透明推理

class NarrativeEdge:
    source: str
    target: str
    relation: str            # causes, then, enables...

class LogicGraph:
    nodes: List[NarrativeNode]
    edges: List[NarrativeEdge]
```

**迁移方式**：扩展为你的时间沙箱事件模型

---

### 1.6 符号验证逻辑（PlotLine）

**文件**：`backend/agents/oracle.py`

```python
async def validate_symbolic(self, logic_graph, world_state):
    violations = []
    satisfied_conditions = set()
    
    for node in logic_graph.nodes:
        for precondition in node.preconditions:
            if precondition not in satisfied_conditions:
                violations.append(...)
        satisfied_conditions.update(node.postconditions)
    
    return ValidationResult(...)
```

**迁移方式**：作为你审计系统的基础

---

### 1.7 三层记忆结构（Morpheus）

**文件**：`backend/memory/__init__.py`

```
L1/
├── IDENTITY.md          # 世界规则、角色硬设定、风格契约、禁忌
└── RUNTIME_STATE.md     # 新角色、状态变化、主线状态

L2/
├── MEMORY.md            # 滚动窗口、未决主线、关键决策
└── OPEN_THREADS.md      # 开放伏笔

L3/
└── *.md                 # 章节摘要、大纲
```

**迁移方式**：直接使用目录结构，扩展你的新文件

---

### 1.8 Context Pack 组装（Morpheus）

**文件**：`backend/services/memory_context.py`

```python
class MemoryContextService:
    _BUDGET_RATIOS = {
        "identity_core": 0.15,
        "runtime_state": 0.10,
        "memory_compact": 0.15,
        "previous_synopsis": 0.10,
        "open_threads": 0.10,
        "previous_chapters": 0.35,
    }
    
    def build_generation_context_pack(self, chapter_number):
        return {
            "identity_core": truncate(...),
            "runtime_state": truncate(...),
            "memory_compact": truncate(...),
            "previous_chapter_synopsis": ...,
            "open_threads": select_top_k_threads(...),
            "previous_chapters_compact": ...,
            "budget_stats": {...}
        }
```

**迁移方式**：直接复制，扩展你的字段

---

### 1.9 开放线程管理（Morpheus）

**文件**：`backend/services/memory_context.py`

```python
def recompute_open_threads(self, project_chapters):
    """扫描所有章节的 foreshadowing 字段，追踪回收状态"""
    threads = []
    for ch in project_chapters:
        for fs_text in ch.plan.foreshadowing:
            thread = {
                "source_chapter": chapter_number,
                "text": cleaned,
                "status": "open" | "resolved",
                "resolved_by_chapter": ...,
                "evidence": ...
            }
            # 检查是否被 callback_targets 回收
            ...
    return threads

def _score_thread_confidence(self, thread, current_chapter):
    """置信度评分：时近性 + 证据 + 长度"""
    recency = 1.0 / distance
    evidence_score = 1.0 if evidence else 0.3
    length_score = min(len(text) / 200, 1.0)
    return 0.5 * recency + 0.3 * evidence + 0.2 * length
```

**迁移方式**：直接复制用于你的伏笔系统

---

### 1.10 MemoryStore Schema（Morpheus）

**文件**：`backend/memory/__init__.py`

```sql
-- 直接可用的表结构
CREATE TABLE memory_items (
    id TEXT PRIMARY KEY,
    layer TEXT NOT NULL,
    source_path TEXT NOT NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,
    entities TEXT,
    importance INTEGER DEFAULT 5,
    recency INTEGER DEFAULT 1
);

CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL,
    attrs TEXT,
    first_seen_chapter INTEGER,
    last_seen_chapter INTEGER
);

CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    relation TEXT NOT NULL,
    object TEXT,
    chapter INTEGER NOT NULL
);

-- FTS5 全文搜索
CREATE VIRTUAL TABLE memory_fts USING fts5(...);
```

**迁移方式**：直接复制，添加你的新表

---

## 二、改造后复用的代码（需要适配）

### 2.1 审计维度（InkOS → 你的第六层）

**InkOS 的 33 维度**：
- OOC检查、时间线检查、设定冲突、战力崩坏、数值检查、伏笔检查、节奏检查、文风检查、信息越界、词汇疲劳...

**你需要扩展**：
```python
# 你的新增维度
- 时间沙箱一致性检查
- 情报边界违反检查
- 世界敌意系数合理性
- 读者耐心指数预警
- 角色内驱力一致性
```

---

### 2.2 LogicGraph → 时间沙箱事件模型

**PlotLine 的 LogicGraph**：
- 只有事件顺序，无绝对时间
- 无地点信息
- 无情报边界

**你的扩展**：
```python
class TimeSandboxEvent(NarrativeNode):
    """扩展 PlotLine 的 NarrativeNode"""
    timestamp: datetime          # 绝对时间戳
    location: str                # 地点
    duration: timedelta          # 持续时间
    information_boundary: Dict[str, bool]  # 谁知道这个事件
    
class TimeSandboxGraph(LogicGraph):
    """扩展 PlotLine 的 LogicGraph"""
    current_time: datetime       # 全局时间
    time_scale: str              # 时间尺度
    parallel_threads: Dict[str, List[Event]]  # 并发线索
```

---

### 2.3 三层记忆 → 六层架构

**Morpheus 的三层**：
- L1: 身份 + 运行态
- L2: 记忆 + 开放线程
- L3: 日志

**你的六层映射**：
```
你的层级                    Morpheus 对应
────────────────────────────────────────────
第一层：基础设施          →  MemoryStore + 状态机
第二层：世界观            →  L1/IDENTITY.md + 时间沙箱
第三层：角色智能体        →  entities 表 + 内驱力引擎
第四层：故事编织          →  L2/OPEN_THREADS.md + 大纲系统
第五层：叙事渲染          →  Agent Studio 的文风/节奏控制
第六层：审核校验          →  OracleAgent + 审计系统
```

---

### 2.4 Agent 工作流 → 双层任务队列

**Morpheus 的单层流程**：
```
导演 → 设定官 → 文风 → 裁决器 → 输出
```

**你的双层设计**：
```
后台推演队列（持续运行）：
  角色A 的内驱力 → 行动决策 → 状态更新
  角色B 的内驱力 → 行动决策 → 状态更新
  时间沙箱推进 → 事件触发 → 状态更新

前台生成队列（按需执行）：
  大纲系统 → 叙事渲染 → 审计校验 → 输出
```

---

## 三、完全自建的模块（你的核心创新）

### 3.1 时间沙箱系统

**功能**：
- 全局时间轴
- 时间戳对齐（多线索并发）
- 时间流速控制
- 时间回溯

**数据结构**：
```python
class TimeSandbox:
    current_time: datetime
    time_scale: str  # second/minute/hour/day
    timeline: Dict[str, List[TimeSandboxEvent]]  # 线索 -> 事件列表
    checkpoints: Dict[int, TimeSandboxState]     # 章节快照
    
    def advance(self, duration: timedelta):
        """推进时间，触发时间相关事件"""
        
    def align_threads(self):
        """对齐所有线索的时间戳"""
        
    def rollback(self, chapter: int):
        """回溯到指定章节的时间状态"""
```

---

### 3.2 角色内驱力引擎

**功能**：
- 角色作为独立 Agent
- 内驱力驱动的自发行动
- 目标管理
- 动机追踪

**数据结构**：
```python
class CharacterDrive:
    character_id: str
    core_motivation: str        # 核心动机
    current_goals: List[Goal]   # 当前目标
    completed_goals: List[Goal] # 已完成目标
    motivation_history: List[MotivationEvent]
    
class Goal:
    description: str
    priority: float
    deadline: Optional[datetime]
    status: str  # active/completed/abandoned
    sub_goals: List[Goal]
    
class DriveEngine:
    def evaluate_goals(self, character: Character, world_state: WorldState):
        """根据世界状态重新评估目标优先级"""
        
    def generate_actions(self, character: Character) -> List[Action]:
        """生成角色会采取的行动"""
```

---

### 3.3 情报隔离系统

**功能**：
- 战争迷雾
- 信息边界管理
- 角色只能基于已知信息行动

**数据结构**：
```python
class InformationBoundary:
    """每个角色的已知信息"""
    character_id: str
    known_facts: Set[str]           # 已知事实
    known_characters: Set[str]      # 已知角色
    known_locations: Set[str]       # 已知地点
    last_update_chapter: int
    
class InformationSystem:
    boundaries: Dict[str, InformationBoundary]
    
    def can_know(self, character_id: str, fact: str) -> bool:
        """检查角色是否可以知道某事实"""
        
    def propagate_information(self, event: Event):
        """事件发生后，更新相关角色的信息边界"""
        
    def filter_perspective(self, character_id: str, world_state: WorldState):
        """从角色视角过滤世界状态"""
```

---

### 3.4 世界敌意系数

**功能**：
- 宏观动态变量
- 给主角制造麻烦
- 厄运系统

**数据结构**：
```python
class WorldHostility:
    base_level: float              # 基础敌意值
    current_level: float           # 当前敌意值
    modifiers: List[HostilityModifier]
    
    def adjust(self, event: Event):
        """根据事件调整敌意值"""
        
    def generate_complication(self) -> Optional[Complication]:
        """根据敌意值生成麻烦"""
        
class HostilityModifier:
    trigger: str                   # 触发条件
    delta: float                   # 变化量
    duration: Optional[int]        # 持续章节
```

---

### 3.5 读者耐心指数

**功能**：
- 元层面控制
- 预警平淡剧情
- 建议切入冲突

**数据结构**：
```python
class ReaderPatience:
    current_level: float           # 当前耐心值 (0-100)
    decay_rate: float              # 衰减速率
    recovery_events: List[str]     # 恢复耐心的事件类型
    
    def update(self, chapter: Chapter):
        """根据章节内容更新耐心值"""
        
    def should_intervene(self) -> bool:
        """是否需要介入"""
        
    def suggest_intervention(self) -> str:
        """建议的介入方式"""
```

---

### 3.6 双层任务队列

**功能**：
- 后台持续推演
- 前台按需生成
- 状态同步

**数据结构**：
```python
class TaskQueue:
    def __init__(self):
        self.background_queue = asyncio.Queue()  # 后台推演
        self.foreground_queue = asyncio.Queue()  # 前台生成
        
    async def run_background_loop(self):
        """后台推演循环"""
        while True:
            task = await self.background_queue.get()
            await self.execute_background_task(task)
            
    async def submit_foreground_task(self, task):
        """提交前台生成任务"""
        await self.foreground_queue.put(task)
        
    def sync_state(self):
        """同步后台推演状态到前台生成"""
```

---

## 四、技术栈建议

### 4.1 语言和框架

| 层级 | 推荐技术 | 原因 |
|-----|---------|------|
| 后端核心 | Python 3.11+ | 复用 Morpheus/PlotLine 代码 |
| 工作流 | LangGraph | PlotLine 已验证 |
| 数据库 | SQLite + LanceDB | Morpheus 已验证 |
| 向量检索 | LanceDB | Morpheus 已验证 |
| 全文搜索 | SQLite FTS5 | Morpheus 已验证 |
| LLM 调用 | 自建 client | 复用 InkOS 逻辑 |
| 前端 | React + Zustand | Morpheus 已验证 |
| 流式传输 | SSE | Morpheus/PlotLine 已验证 |

### 4.2 项目结构建议

```
MineNovel/
├── backend/
│   ├── core/
│   │   ├── llm/                 # LLM 调用层（复用 InkOS）
│   │   ├── state/               # 状态管理（复用 InkOS）
│   │   └── queue/               # 双层任务队列（自建）
│   │
│   ├── memory/                  # 记忆系统（复用 Morpheus）
│   │   ├── three_layer.py
│   │   ├── store.py
│   │   └── context_pack.py
│   │
│   ├── world/                   # 世界观层（自建）
│   │   ├── time_sandbox.py      # 时间沙箱
│   │   ├── rules.py             # 世界法则
│   │   ├── ceiling.py           # 战力天花板
│   │   └── hostility.py         # 世界敌意系数
│   │
│   ├── agents/                  # 角色层（自建 + 复用）
│   │   ├── character.py         # 角色定义
│   │   ├── drive_engine.py      # 内驱力引擎（自建）
│   │   ├── information.py       # 情报隔离（自建）
│   │   └── relationship.py      # 关系矩阵（复用 Morpheus）
│   │
│   ├── story/                   # 故事层（复用 Morpheus）
│   │   ├── outline.py
│   │   ├── hooks.py             # 伏笔系统
│   │   └── resolution.py
│   │
│   ├── narrative/               # 叙事层（复用 Morpheus/InkOS）
│   │   ├── style.py             # 文风控制
│   │   ├── flow.py              # 叙事流速
│   │   └── tension.py           # 情绪张力
│   │
│   ├── review/                  # 审核层（复用 InkOS/PlotLine）
│   │   ├── audit.py             # 审计系统
│   │   ├── patience.py          # 读者耐心（自建）
│   │   └── feedback.py          # 反馈闭环（自建）
│   │
│   └── models/                  # 数据模型（复用 PlotLine）
│       ├── schemas.py
│       └── events.py
│
├── frontend/                    # 前端（参考 Morpheus）
│   └── ...
│
└── tests/
```

---

## 五、开发优先级

### Phase 1：基础设施（2周）
- [ ] LLM 调用层（复用 InkOS）
- [ ] 状态管理器（复用 InkOS）
- [ ] 三层记忆系统（复用 Morpheus）
- [ ] MemoryStore（复用 Morpheus）

### Phase 2：世界观层（2周）
- [ ] 时间沙箱系统（自建，扩展 PlotLine）
- [ ] 世界法则定义
- [ ] 战力天花板系统
- [ ] 世界敌意系数

### Phase 3：角色层（3周）
- [ ] 角色定义结构
- [ ] 内驱力引擎（自建）
- [ ] 情报隔离系统（自建）
- [ ] 关系矩阵（复用 Morpheus）

### Phase 4：故事层（2周）
- [ ] 大纲系统（复用 Morpheus）
- [ ] 伏笔系统（复用 Morpheus）
- [ ] 填坑系统

### Phase 5：叙事层（2周）
- [ ] 文风控制（复用 InkOS）
- [ ] 叙事流速
- [ ] 情绪张力

### Phase 6：审核层（2周）
- [ ] 审计系统（复用 InkOS + PlotLine）
- [ ] 读者耐心指数（自建）
- [ ] 反馈闭环

### Phase 7：双层队列（2周）
- [ ] 后台推演循环
- [ ] 前台生成流程
- [ ] 状态同步

---

## 六、总结

### 可复用代码量估算

| 来源 | 可复用程度 | 估算代码量 |
|-----|----------|-----------|
| InkOS | 高 | ~3000 行 |
| PlotLine | 高 | ~2000 行 |
| Morpheus | 高 | ~5000 行 |
| **总计** | | **~10000 行** |

### 自建代码量估算

| 模块 | 估算代码量 |
|-----|-----------|
| 时间沙箱 | ~1500 行 |
| 角色内驱力 | ~2000 行 |
| 情报隔离 | ~1000 行 |
| 世界敌意系数 | ~500 行 |
| 读者耐心指数 | ~500 行 |
| 双层任务队列 | ~1500 行 |
| **总计** | **~7000 行** |

### 项目总规模

- **可复用代码**：~10000 行
- **自建代码**：~7000 行
- **预计总代码量**：~17000 行

### 时间估算

- **Phase 1-2**：4 周（基础设施 + 世界观）
- **Phase 3-4**：5 周（角色 + 故事）
- **Phase 5-7**：6 周（叙事 + 审核 + 双层队列）
- **总计**：**~15 周**（约 4 个月）