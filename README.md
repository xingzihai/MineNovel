# MineNovel 项目结构

> 基于 Vibe Coding 的 Memory Bank 模式

```
MineNovel/
│
├── CLAUDE.md                    # AI 助手指南（入口文件）
│
├── memory-bank/                 # 📚 Memory Bank - 上下文文档
│   ├── ARCHITECTURE.md          # 六层架构设计
│   ├── IMPLEMENTATION_PLAN.md   # 实施计划（原 ABSORPTION_ROADMAP）
│   ├── PROGRESS.md              # 开发进度追踪
│   ├── TECH_STACK.md            # 技术选型
│   ├── COMPETITIVE_ANALYSIS.md  # 竞品分析（7 个项目）
│   ├── EXISTING_SOLUTIONS_ANALYSIS.md  # 现成方案汇总
│   └── CORE_CODE_ANALYSIS.md    # 源码详细分析
│
├── prompts/                     # 🎯 提示词库
│   ├── system/                  # Agent 系统提示词
│   │   └── character_engine.md  # 角色内驱力引擎
│   ├── coding/                  # 编码辅助提示词
│   │   └── implement_module.md  # 实现新模块
│   └── meta/                    # 元提示词
│       └── generate_agent_prompt.md  # 生成 Agent 提示词
│
├── src/                         # 📦 源代码（待创建）
│   ├── core/                    # 第一层：基础设施
│   ├── world/                   # 第二层：世界观
│   ├── agents/                  # 第三层：角色
│   ├── story/                   # 第四层：故事
│   ├── narrative/               # 第五层：叙事
│   └── review/                  # 第六层：审核
│
├── tests/                       # 🧪 测试（待创建）
│
└── *-reference/                 # 📖 参考代码（只读）
    ├── inkos-reference/         # InkOS 源码
    ├── plotline-reference/      # PlotLine 源码
    ├── strategos-reference/     # Strategos 源码 ⭐ 时间沙箱
    ├── replicantlife-reference/ # ReplicantLife 源码 ⭐ 角色内驱力
    └── morpheus-reference/      # Morpheus 源码
```

---

## 使用方法

### 开始开发前

1. 阅读 `CLAUDE.md` — 了解 AI 如何帮助你
2. 阅读 `memory-bank/ARCHITECTURE.md` — 理解架构
3. 阅读 `memory-bank/PROGRESS.md` — 了解当前进度

### 实现新模块时

1. 使用 `prompts/coding/implement_module.md` 模板
2. 参考 `*-reference/` 目录下的代码
3. 完成后更新 `memory-bank/PROGRESS.md`

### 设计 Agent 时

1. 使用 `prompts/meta/generate_agent_prompt.md` 生成提示词
2. 参考 `prompts/system/character_engine.md` 示例

---

## Vibe Coding 方法论

本项目采用 Vibe Coding 的核心理念：

1. **规划就是一切** — 先读 memory-bank，再编码
2. **Memory Bank 模式** — 文档即上下文
3. **模块化优先** — 一次只改一个模块
4. **能抄不写** — 复用 *-reference/ 代码

---

## 下一步

- [ ] 创建 `src/` 目录结构
- [ ] 复制 Strategos 核心代码
- [ ] 复制 ReplicantLife Agent 代码
- [ ] 实现时间沙箱原型