# CLAUDE.md - AI 助手指南

> 本文件指导 AI 助手如何帮助开发 MineNovel 项目

---

## 项目概述

MineNovel 是一个 **AI 小说世界模拟器**，核心理念是"世界在运行，我们只是切了一刀呈现给读者"。

与传统的"写 → 审 → 改"管线不同，MineNovel 采用"推演 → 呈现"模式。

---

## 核心架构

```
第六层：审核校验与读者反馈层
第五层：叙事渲染与节奏控制层
第四层：故事编织与悬念控制层
第三层：角色智能体与状态推演层
第二层：世界观与宏观法则层
第一层：基础设施与记忆计算层
```

详见 `memory-bank/ARCHITECTURE.md`

---

## 开发原则

### 必须遵守

1. **模块化优先** — 每个模块独立文件，禁止单体巨文件
2. **接口先行** — 先定义接口/类型，再实现
3. **一次只改一个模块** — 完成后再进入下一个
4. **测试驱动** — 每个模块完成后必须有验证方式
5. **文档即上下文** — 文档不是事后补，是开发的一部分

### 代码风格

- Python 3.11+
- 使用 dataclass 定义数据模型
- 使用 async/await 处理异步
- 类型注解必须完整

---

## 可复用代码来源

| 模块 | 来源 | 文件 |
|-----|------|------|
| 时间沙箱 | Strategos | `strategos-reference/core/time.py` |
| 事件存储 | Strategos | `strategos-reference/core/event_store.py` |
| 角色内驱力 | ReplicantLife | `replicantlife-reference/src/agents.py` |
| 记忆系统 | Morpheus | `morpheus-reference/backend/memory/` |

---

## 开发流程

### 开始任何任务前

1. 阅读 `memory-bank/ARCHITECTURE.md` 了解架构
2. 阅读 `memory-bank/PROGRESS.md` 了解当前进度
3. 阅读 `memory-bank/IMPLEMENTATION_PLAN.md` 了解计划

### 完成任务后

1. 更新 `memory-bank/PROGRESS.md` 记录进度
2. 如果有架构变更，更新 `memory-bank/ARCHITECTURE.md`
3. 如果有重要决策，记录到 `memory-bank/PROGRESS.md` 的决策部分

### 遇到问题时

1. 先查阅 `memory-bank/COMPETITIVE_ANALYSIS.md` 看竞品怎么做
2. 再查阅 `memory-bank/EXISTING_SOLUTIONS_ANALYSIS.md` 看有没有现成方案
3. 最后查阅 `memory-bank/CORE_CODE_ANALYSIS.md` 看源码细节

---

## 禁止事项

1. ❌ 不要创建单体巨文件（>500 行考虑拆分）
2. ❌ 不要跳过测试直接进入下一个模块
3. ❌ 不要在未阅读架构文档的情况下开始编码
4. ❌ 不要修改 `*-reference/` 目录下的参考代码

---

## 提示词库

项目提供以下提示词模板：

- `prompts/system/` — Agent 系统提示词
- `prompts/coding/` — 编码辅助提示词
- `prompts/meta/` — 元提示词（生成提示词的提示词）

---

## 联系与贡献

- 项目所有者：冰水
- 项目类型：独立开源项目
- 致谢：InkOS、PlotLine、Morpheus、Strategos、ReplicantLife