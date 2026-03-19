# 核心创新模块源码分析报告

> 基于 Strategos、ReplicantLife、Stanford GA 等项目的深入源码分析
> 目标：识别可直接复用的代码模块

---

## 一、时间沙箱系统（Strategos）

### 1.1 核心类：SimulationClock

**文件**：`strategos-reference/core/time.py`

```python
class SimulationClock:
    """管理连续模拟时间，支持变速"""
    
    def __init__(self, time_scale: float = 1.0):
        self._time_state = TimeState(
            current_time=0.0,
            time_scale=time_scale,
            is_running=False
        )
    
    async def start(self) -> None:        # 开始时间流逝
    async def pause(self) -> None:        # 暂停
    async def resume(self) -> None:       # 恢复
    async def stop(self) -> None:         # 停止
    async def seek(self, target_time: float) -> None:  # 跳转到特定时间
    async def set_time_scale(self, scale: float) -> None:  # 改变时间流速
    
    def get_time(self) -> float:          # 获取当前模拟时间
    def format_time(self) -> str:         # 格式化输出
```

**关键特性**：
- ✅ 连续时间流逝（asyncio 驱动）
- ✅ 可变时间流速（time_scale）
- ✅ 暂停/恢复/停止
- ✅ 时间跳转（seek）
- ✅ 时间格式化

**可直接复用于你的时间沙箱！**

---

### 1.2 核心类：EventStore

**文件**：`strategos-reference/core/event_store.py`

```python
class EventStore:
    """仅追加的事件日志，支持回放"""
    
    async def initialize(self) -> None:   # 初始化数据库
    async def append(self, event: Event) -> None:  # 追加事件
    async def append_batch(self, events: list[Event]) -> None:  # 批量追加
    async def get_events(self, from_time, to_time, event_types) -> list[Event]:  # 查询
    async def stream_events(self, from_time, to_time, event_types) -> AsyncIterator[Event]:  # 流式
    async def get_latest_time(self) -> Optional[float]:  # 获取最新时间
    async def clear(self) -> None:        # 清空（测试用）
```

**数据库 Schema**：
```sql
CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    simulation_time REAL NOT NULL,      -- 模拟时间
    event_type TEXT NOT NULL,           -- 事件类型
    data TEXT NOT NULL,                 -- 事件数据（JSON）
    metadata TEXT NOT NULL,             -- 元数据（JSON）
    causation_id TEXT,                  -- 因果链
    correlation_id TEXT,                -- 关联组
    created_at TEXT NOT NULL            -- 真实时间戳
)
```

**关键特性**：
- ✅ 仅追加（不可修改历史）
- ✅ 时间范围查询
- ✅ 事件类型过滤
- ✅ 因果链追踪（causation_id）
- ✅ 关联事件分组（correlation_id）

**可直接复用于你的事件存储！**

---

### 1.3 核心类：Event

**文件**：`strategos-reference/core/events.py`

```python
@dataclass(frozen=True)
class Event:
    """不可变事件，代表状态变化"""
    
    event_type: EventType | str         # 事件类型
    simulation_time: float = 0.0        # 模拟时间
    data: dict[str, Any]                # 事件数据
    metadata: dict[str, Any]            # 元数据
    event_id: UUID                      # 唯一ID
    causation_id: Optional[UUID]        # 因果链
    correlation_id: Optional[UUID]      # 关联组
    created_at: Optional[datetime]      # 真实时间戳

class EventType(str, Enum):
    SIMULATION_STARTED = "simulation.started"
    SIMULATION_PAUSED = "simulation.paused"
    SIMULATION_RESUMED = "simulation.resumed"
    SIMULATION_STOPPED = "simulation.stopped"
    TIME_SCALED = "time.scaled"
    ENTITY_CREATED = "entity.created"
    ENTITY_MOVED = "entity.moved"
    ENTITY_DESTROYED = "entity.destroyed"
    CHECKPOINT_CREATED = "checkpoint.created"
    CHECKPOINT_RESTORED = "checkpoint.restored"
```

**你需要扩展的事件类型**：
```python
class NovelEventType(str, Enum):
    # 角色事件
    CHARACTER_SPAWNED = "character.spawned"
    CHARACTER_ACTED = "character.acted"
    CHARACTER_GOAL_CHANGED = "character.goal_changed"
    
    # 时间沙箱事件
    TIME_ADVANCED = "time.advanced"
    TIMELINE_BRANCH_CREATED = "timeline.branch_created"
    
    # 情报事件
    INFORMATION_GAINED = "information.gained"
    INFORMATION_LOST = "information.lost"
    
    # 故事事件
    PLOT_HOOK_CREATED = "plot.hook_created"
    PLOT_HOOK_RESOLVED = "plot.hook_resolved"
```

---

### 1.4 核心类：Simulation

**文件**：`strategos-reference/core/simulation.py`

```python
class Simulation:
    """主模拟编排器"""
    
    def __init__(self, db_path, checkpoint_dir, checkpoint_interval, time_scale, simulation_id):
        self.event_store = EventStore(db_path)
        self.checkpoint_store = CheckpointStore(checkpoint_dir, checkpoint_interval)
        self.clock = SimulationClock(time_scale)
        self.state = WorldState()
        self._event_handlers = EventHandlerRegistry()
    
    async def initialize(self) -> None:  # 初始化
    async def shutdown(self) -> None:    # 关闭
    async def start(self, time_scale) -> None:  # 开始
    async def stop(self) -> None:        # 停止
    async def pause(self) -> None:       # 暂停
    async def resume(self) -> None:      # 恢复
    async def seek(self, target_time: float) -> None:  # 时间跳转
    async def emit_event(self, event_type, data) -> Event:  # 发送事件
```

**关键方法：seek（时间回溯）**：
```python
async def seek(self, target_time: float) -> None:
    """回溯或快进到特定时间"""
    # 1. 找到目标时间之前的最近检查点
    checkpoint = await self.checkpoint_store.get_nearest_before(target_time)
    
    if checkpoint:
        # 2. 恢复检查点状态
        self.state = checkpoint.deserialize_state()
        replay_from = checkpoint.simulation_time
    else:
        # 3. 从头开始
        self.state = WorldState()
        replay_from = 0.0
    
    # 4. 回放事件
    events = await self.event_store.get_events(from_time=replay_from, to_time=target_time)
    for event in events:
        self.state.apply_event(event)
    
    # 5. 设置时钟
    await self.clock.seek(target_time)
```

**这正是你的时间沙箱需要的核心逻辑！**

---

## 二、角色内驱力引擎（ReplicantLife）

### 2.1 核心类：Agent

**文件**：`replicantlife-reference/src/agents.py`

```python
class Agent:
    def __init__(self, agent_data={}):
        self.mid = agent_data.get("agent_id", str(uuid.uuid4()))
        self.name = agent_data.get('name', random.choice(DEFAULT_NAMES))
        self.description = agent_data.get('description', ...)
        self.goal = agent_data.get('goal', random.choice(DEFAULT_GOALS))  # 目标！
        self.memory = agent_data.get("memory", [])         # 长期记忆
        self.short_memory = agent_data.get("short_memory", [])  # 短期记忆
        self.plan = agent_data.get("plan", None)           # 计划！
        self.connections = agent_data.get("connections", [])  # 社交连接
        self.meta_questions = agent_data.get("meta_questions", [])  # 元认知问题
        self.meta_rate = agent_data.get("meta_rate", random.randint(0, 100))
```

**关键方法**：

```python
def update_goals(self):
    """根据记忆更新目标"""
    relevant_memories = self.getMemories(None, timestamp)
    prompt = f'''
    {self.getSelfContext()}
    And {self}'s recent memories:
    {relevant_memories_string}
    Write out what my new goal should be...
    '''
    msg = llm.generate(prompt)
    self.goal = msg

def decide(self):
    """决策行动"""
    self.matrix.llm_action(self, self.matrix.unix_time)

def meta_cognize(self, timestamp, force=False):
    """元认知：思考自己的思考"""
    question = random.choice(self.meta_questions)
    # ... 回答元认知问题
    self.addMemory("meta", f"{question}:{msg}", timestamp, 10)

def evaluate_progress(self, opts={}):
    """评估目标进度"""
    relevant_memories = self.getMemories(self.goal, timestamp)
    msg = llm.prompt("evaluate_progress", variables)
    # 解析分数和解释
    if score and int(score) < 3:
        # 如果分数太低，触发元认知
        pass

def make_plans(self, timestamp):
    """制定计划"""
    msg = llm.prompt("make_plans", variables)
```

**这正是你的角色内驱力引擎需要的核心逻辑！**

---

### 2.2 记忆系统

**关键方法**：
```python
def getMemories(self, query, timestamp):
    """检索相关记忆"""
    # 基于查询和时间检索记忆

def addMemory(self, type, content, timestamp, importance):
    """添加记忆"""
    self.memory.append({
        "type": type,
        "content": content,
        "timestamp": timestamp,
        "importance": importance
    })
```

---

## 三、综合对比

### 3.1 你的需求 vs 现成实现

| 你的需求 | Strategos | ReplicantLife | Stanford GA |
|---------|-----------|---------------|-------------|
| 时间沙箱 | ✅ 完整实现 | ❌ | ❌ |
| 事件溯源 | ✅ 完整实现 | ❌ | ❌ |
| 时间回溯 | ✅ seek() | ❌ | ❌ |
| 角色内驱力 | ❌ | ✅ 完整实现 | ✅ 经典实现 |
| 目标管理 | ❌ | ✅ goal + update_goals() | ✅ Planning |
| 元认知 | ❌ | ✅ meta_cognize() | ✅ Reflection |
| 记忆系统 | ❌ | ✅ memory + getMemories() | ✅ Memory Stream |
| 情报隔离 | ⚠️ Fog of War（未找到代码） | ❌ | ❌ |

### 3.2 代码复用清单

| 文件 | 行数 | 功能 | 复用程度 |
|-----|-----|------|---------|
| `strategos/core/time.py` | ~150 | 时间沙箱 | ⭐⭐⭐ 直接用 |
| `strategos/core/events.py` | ~200 | 事件模型 | ⭐⭐⭐ 直接用 |
| `strategos/core/event_store.py` | ~250 | 事件存储 | ⭐⭐⭐ 直接用 |
| `strategos/core/simulation.py` | ~400 | 模拟编排 | ⭐⭐ 改造用 |
| `replicantlife/src/agents.py` | ~600 | Agent + 内驱力 | ⭐⭐⭐ 直接用 |

**总计可复用：~1600 行核心代码**

---

## 四、整合方案

### 4.1 时间沙箱适配

```python
# 你的时间沙箱 = Strategos 的 Simulation + 你的扩展

class NovelTimeSandbox(Simulation):
    """小说时间沙箱"""
    
    def __init__(self, db_path, checkpoint_dir):
        super().__init__(db_path, checkpoint_dir)
        self.characters: Dict[str, CharacterAgent] = {}  # 角色
        self.plot_hooks: List[PlotHook] = []             # 伏笔
        self.information_boundaries: Dict[str, Set[str]] = {}  # 情报边界
    
    async def advance_plot(self, duration: timedelta):
        """推进剧情"""
        # 1. 推进时间
        await self.clock.tick()
        
        # 2. 让所有角色根据内驱力行动
        for character in self.characters.values():
            action = await character.decide(self.state)
            await self.emit_event("character.acted", action)
        
        # 3. 检查伏笔触发
        for hook in self.plot_hooks:
            if hook.should_trigger(self.clock.get_time()):
                await self.emit_event("plot.hook_triggered", hook)
    
    async def get_character_view(self, character_id: str) -> WorldView:
        """从角色视角获取世界状态（情报隔离）"""
        known_facts = self.information_boundaries.get(character_id, set())
        return self.state.filter(known_facts)
```

### 4.2 角色内驱力适配

```python
# 你的角色 = ReplicantLife 的 Agent + 你的扩展

class NovelCharacter(Agent):
    """小说角色"""
    
    def __init__(self, character_data, time_sandbox):
        super().__init__(character_data)
        self.time_sandbox = time_sandbox
        self.drive_engine = DriveEngine(character_data.get("drives", []))
    
    async def decide(self, world_state) -> CharacterAction:
        """基于内驱力决策行动"""
        # 1. 评估当前目标进度
        progress = await self.evaluate_progress()
        
        # 2. 如果进度太低，触发元认知调整策略
        if progress.score < 3:
            new_goal = await self.drive_engine.suggest_new_goal(self.memory)
            self.goal = new_goal
        
        # 3. 生成行动
        action = await self.time_sandbox.llm_action(self)
        
        return action
```

---

## 五、下一步行动

### 5.1 立即可做

1. **复制 Strategos 核心文件到你的项目**
   - `core/time.py` → `src/world/time_sandbox.py`
   - `core/events.py` → `src/core/events.py`
   - `core/event_store.py` → `src/core/event_store.py`

2. **复制 ReplicantLife Agent 文件**
   - `src/agents.py` → `src/agents/character.py`

3. **创建适配层**
   - 将 `Simulation` 扩展为 `NovelTimeSandbox`
   - 将 `Agent` 扩展为 `NovelCharacter`

### 5.2 仍需自建

| 模块 | 工作量 | 说明 |
|-----|-------|------|
| 情报隔离系统 | ~500 行 | Strategos 有概念但未找到代码 |
| 世界敌意系数 | ~300 行 | 无现成方案 |
| 读者耐心指数 | ~300 行 | 无现成方案 |
| 小说特定适配 | ~500 行 | 事件类型、状态模型等 |

---

## 六、结论

### 核心创新模块的可复用性

| 模块 | 原计划 | 现可复用 | 节省 |
|-----|-------|---------|------|
| 时间沙箱 | 1500 行 | 800 行 | 47% |
| 角色内驱力 | 2000 行 | 600 行 | 30% |
| 事件溯源 | - | 450 行 | 100% |
| **总计** | **3500 行** | **1850 行** | **53%** |

### 关键发现

1. **Strategos 完美匹配时间沙箱需求**
   - `SimulationClock` 提供了连续时间流逝
   - `EventStore` 提供了事件溯源
   - `seek()` 提供了时间回溯

2. **ReplicantLife 完美匹配角色内驱力需求**
   - `Agent` 提供了目标管理
   - `update_goals()` 提供了目标调整
   - `meta_cognize()` 提供了元认知

3. **Stanford GA 是经典参考**
   - 论文和架构设计是最佳实践来源
   - 但源码结构较复杂，建议参考 ReplicantLife 的简化实现

### 推荐路径

```
Phase 1（1周）：
├── 复制 Strategos 核心代码
├── 复制 ReplicantLife Agent 代码
└── 运行测试验证

Phase 2（1周）：
├── 创建小说特定的事件类型
├── 扩展 Simulation 为 NovelTimeSandbox
└── 扩展 Agent 为 NovelCharacter

Phase 3（1周）：
├── 实现情报隔离系统
├── 实现世界敌意系数
└── 实现读者耐心指数
```