# MineNovel 技术选型

> 基于竞品分析和复用策略确定的技术栈

---

## 核心语言与框架

| 层级 | 选择 | 理由 |
|-----|------|------|
| 语言 | Python 3.11+ | 复用 Morpheus/PlotLine/Strategos/ReplicantLife 代码 |
| 异步框架 | asyncio | Strategos 已验证 |
| Web 框架 | FastAPI | Strategos/Morpheus 已验证 |
| 工作流编排 | LangGraph | PlotLine 已验证 |

---

## 数据存储

| 用途 | 选择 | 理由 |
|-----|------|------|
| 事件存储 | SQLite + aiosqlite | Strategos 已验证，轻量级 |
| 向量存储 | LanceDB | Morpheus 已验证 |
| 全文搜索 | SQLite FTS5 | Morpheus 已验证 |
| 记忆流 | 自定义实现 | 参考 Stanford GA / ReplicantLife |

---

## LLM 调用层

| 功能 | 选择 | 来源 |
|-----|------|------|
| 多 Provider 支持 | 自建 client | 复用 InkOS provider.ts 逻辑 |
| Stream 降级 | 自建 client | 复用 InkOS provider.ts 逻辑 |
| 错误处理 | 自建 client | 复用 InkOS provider.ts 逻辑 |

---

## 核心模块复用

### 来自 Strategos

| 模块 | 文件 | 用途 |
|-----|------|------|
| 时间沙箱 | `core/time.py` | 连续时间模拟 |
| 事件存储 | `core/event_store.py` | 事件溯源 |
| 事件模型 | `core/events.py` | 事件定义 |
| 模拟编排 | `core/simulation.py` | 模拟控制 |

### 来自 ReplicantLife

| 模块 | 文件 | 用途 |
|-----|------|------|
| 角色定义 | `src/agents.py` | Agent 基类 |
| 内驱力 | `src/agents.py` | 目标管理、元认知 |
| 记忆 | `src/agents.py` | 记忆检索 |

### 来自 Morpheus

| 模块 | 文件 | 用途 |
|-----|------|------|
| 三层记忆 | `backend/memory/` | 记忆系统结构 |
| Context Pack | `backend/services/` | 上下文组装 |

### 来自 InkOS

| 模块 | 文件 | 用途 |
|-----|------|------|
| 审计维度 | `agents/continuity.ts` | 33 维度审计 |
| 硬规则 | `agents/post-write-validator.ts` | 11 条硬规则 |
| 风格分析 | `agents/style-analyzer.ts` | 风格指纹 |

---

## 需要自建的模块

| 模块 | 预估代码量 | 说明 |
|-----|-----------|------|
| 情报隔离系统 | ~500 行 | 参考 Strategos Fog of War 概念 |
| 世界敌意系数 | ~300 行 | 无现成方案 |
| 读者耐心指数 | ~300 行 | 无现成方案 |
| 小说事件类型 | ~200 行 | 扩展 Strategos EventType |
| 适配层 | ~500 行 | 将模拟引擎适配到小说生成 |

---

## 项目结构

```
MineNovel/
├── CLAUDE.md                    # AI 助手指南
├── memory-bank/                 # 上下文文档（Memory Bank 模式）
│   ├── ARCHITECTURE.md          # 架构设计
│   ├── IMPLEMENTATION_PLAN.md   # 实施计划
│   ├── PROGRESS.md              # 开发进度
│   ├── TECH_STACK.md            # 技术选型（本文件）
│   ├── COMPETITIVE_ANALYSIS.md  # 竞品分析
│   ├── EXISTING_SOLUTIONS_ANALYSIS.md
│   └── CORE_CODE_ANALYSIS.md
│
├── prompts/                     # 提示词库
│   ├── system/                  # Agent 系统提示词
│   ├── coding/                  # 编码提示词
│   └── meta/                    # 元提示词
│
├── src/                         # 源代码
│   ├── core/                    # 第一层：基础设施
│   ├── world/                   # 第二层：世界观
│   ├── agents/                  # 第三层：角色
│   ├── story/                   # 第四层：故事
│   ├── narrative/               # 第五层：叙事
│   └── review/                  # 第六层：审核
│
├── tests/                       # 测试
│
└── *-reference/                 # 参考代码（只读）
```

---

## 依赖列表

```txt
# 核心依赖
aiosqlite>=0.19.0
lancedb>=0.3.0
langgraph>=0.0.20
pydantic>=2.0.0

# Web 框架
fastapi>=0.100.0
uvicorn>=0.23.0

# LLM
openai>=1.0.0
anthropic>=0.18.0

# 工具
python-dotenv>=1.0.0
rich>=13.0.0
```