# MineNovel 项目优化建议

> 目标：优化项目以更好地配合 VS Code Roo Code 插件开发

---

## 一、当前项目状态分析

### ✅ 做得好的地方

| 项目 | 状态 |
|-----|------|
| Memory Bank 文档体系 | ✅ 完整，符合 Vibe Coding 方法论 |
| .gitignore 配置 | ✅ 正确排除了 reference 目录 |
| 项目结构 | ✅ 六层架构清晰 |
| 测试覆盖 | ✅ 有测试文件 |
| CLAUDE.md | ✅ 提供了 AI 助手指南 |

### ⚠️ 需要优化的地方

| 问题 | 影响 |
|-----|------|
| 无 pyproject.toml | 现代 Python 项目标准 |
| 无类型存根文件 | IDE/AI 类型提示不完整 |
| reference 目录在本地但未排除显示 | 可能干扰 Roo Code |
| 缺少 .rooignore 或 .cursorrules | AI 工具专用配置 |
| 文档分散在多处 | AI 上下文可能过长 |
| 无 pre-commit hooks | 代码质量保障 |

---

## 二、具体优化建议

### 优化 1：添加 pyproject.toml（推荐）

**原因**：现代 Python 项目标准，更好的依赖管理

**操作**：创建 `pyproject.toml`

```toml
[project]
name = "minenovel"
version = "0.1.0"
description = "AI小说世界模拟器"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "xingzihai"}
]
keywords = ["ai", "novel", "simulation", "llm"]

dependencies = [
    "aiosqlite>=0.19.0",
    "pydantic>=2.0.0",
    "openai>=1.0.0",
    "anthropic>=0.18.0",
    "python-dotenv>=1.0.0",
    "litellm>=1.0.0",
    "streamlit>=1.30.0",
    "pyyaml>=6.0",
    "requests>=2.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[project.scripts]
minenovel = "src.web.app:main"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N"]

[tool.mypy]
python_version = "3.11"
strict = true
```

---

### 优化 2：创建 .cursorrules（Roo Code 兼容）

**原因**：Roo Code 和 Cursor 都支持此文件，提供项目特定规则

**操作**：创建 `.cursorrules`

```
# MineNovel 项目规则

## 项目概述
MineNovel 是一个 AI 小说世界模拟器，采用"推演→呈现"模式。

## 架构
- 六层架构：基础设施、世界观、角色、故事、叙事、审核
- 参考 memory-bank/ARCHITECTURE.md 了解详细设计

## 开发规则

### 必须遵守
1. 阅读 memory-bank/PROGRESS.md 了解当前进度
2. 阅读 memory-bank/IMPLEMENTATION_PLAN.md 了解计划
3. 一次只改一个模块
4. 添加类型注解
5. 编写测试

### 代码风格
- Python 3.11+
- 使用 dataclass 定义数据模型
- 使用 async/await
- line-length = 100

### 禁止事项
- ❌ 硬编码 API Key
- ❌ 创建单体巨文件（>500行）
- ❌ 跳过测试

## 重要文件
- CLAUDE.md: AI 助手完整指南
- memory-bank/ARCHITECTURE.md: 架构设计
- memory-bank/PROGRESS.md: 开发进度
- memory-bank/TECH_STACK.md: 技术选型
```

---

### 优化 3：创建 .rooignore

**原因**：让 Roo Code 忽略不需要分析的文件

**操作**：创建 `.rooignore`

```
# 参考代码
*-reference/
inkos-reference/
plotline-reference/
strategos-reference/
replicantlife-reference/
morpheus-reference/

# Python
__pycache__/
*.py[cod]
.venv/
venv/

# 测试缓存
.pytest_cache/
.coverage
htmlcov/

# 数据文件
data/
*.db
*.sqlite3

# 日志
logs/
*.log

# 临时文件
tmp/
*.tmp
```

---

### 优化 4：简化 CLAUDE.md

**原因**：当前 CLAUDE.md 较长，Roo Code 可能上下文溢出

**操作**：将 CLAUDE.md 简化为入口文件

```markdown
# MineNovel - AI 小说世界模拟器

## 快速开始

开发前必读：
1. `memory-bank/ARCHITECTURE.md` - 架构设计
2. `memory-bank/PROGRESS.md` - 当前进度
3. `memory-bank/TECH_STACK.md` - 技术选型

## 核心规则

- 一次只改一个模块
- 添加类型注解
- 编写测试
- 禁止硬编码 API Key

## 项目结构

```
src/
├── core/      # 第一层：基础设施
├── world/     # 第二层：世界观
├── agents/    # 第三层：角色
├── story/     # 第四层：故事
├── narrative/ # 第五层：叙事
└── review/    # 第六层：审核
```

详细指南见 `.cursorrules`
```

---

### 优化 5：创建 Makefile 或 justfile

**原因**：常用命令标准化，方便 Roo Code 执行

**操作**：创建 `Makefile`

```makefile
.PHONY: install test run clean lint format

install:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

run:
	streamlit run src/web/app.py

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	rm -rf .coverage htmlcov
	find . -name "*.pyc" -delete

lint:
	ruff check src/ tests/

format:
	black src/ tests/

typecheck:
	mypy src/

check: lint format typecheck test
```

---

### 优化 6：创建开发环境配置

**操作**：创建 `.vscode/settings.json`

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "ms-python.black-formatter",
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/*-reference": true
  },
  "search.exclude": {
    "**/*-reference": true
  }
}
```

创建 `.vscode/extensions.json`

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "matangover.mypy"
  ]
}
```

---

### 优化 7：将 reference 目录移出项目

**原因**：减少 Roo Code 扫描的文件数量，提升响应速度

**操作**：

```bash
# 将 reference 目录移到项目外
mkdir -p ../MineNovel-references
mv *-reference ../MineNovel-references/
```

然后在 `.gitignore` 和 `.rooignore` 中添加：

```
# 参考代码（外部）
../MineNovel-references/
```

---

### 优化 8：创建 CONTRIBUTING.md

**原因**：标准化贡献流程，AI 助手也能参考

**操作**：创建 `CONTRIBUTING.md`

```markdown
# 贡献指南

## 开发流程

1. 阅读 memory-bank/PROGRESS.md 了解当前进度
2. 选择一个任务
3. 创建分支：`git checkout -b feature/xxx`
4. 开发 + 测试
5. 提交：`git commit -m "feat: xxx"`
6. 推送：`git push origin feature/xxx`
7. 创建 PR

## 代码规范

- 使用 black 格式化
- 使用 ruff 检查
- 添加类型注解
- 编写测试

## 提交信息格式

```
feat: 新功能
fix: 修复
docs: 文档
test: 测试
refactor: 重构
```
```

---

## 三、优先级排序

| 优先级 | 优化项 | 工作量 | 价值 |
|-------|-------|-------|-----|
| 🔴 高 | 创建 .cursorrules | 5 分钟 | AI 理解项目 |
| 🔴 高 | 创建 .rooignore | 2 分钟 | AI 忽略无关文件 |
| 🟡 中 | 移动 reference 目录 | 5 分钟 | 性能提升 |
| 🟡 中 | 创建 pyproject.toml | 10 分钟 | 现代化 |
| 🟢 低 | 创建 Makefile | 5 分钟 | 命令标准化 |
| 🟢 低 | 创建 .vscode 配置 | 5 分钟 | IDE 配置 |

---

## 四、推荐立即执行

```bash
# 1. 创建关键配置文件
cd MineNovel

# 创建 .cursorrules
# 创建 .rooignore
# 创建 pyproject.toml

# 2. 移动 reference 目录
mkdir -p ../MineNovel-references
mv *-reference ../MineNovel-references/

# 3. 简化 CLAUDE.md

# 4. 提交更新
git add .
git commit -m "chore: 优化项目配置以支持 Roo Code 开发"
git push
```

---

## 五、Roo Code 使用建议

### 推荐工作流

1. **开始开发前**
   - 让 Roo Code 阅读 `memory-bank/PROGRESS.md`
   - 让 Roo Code 阅读 `memory-bank/ARCHITECTURE.md`

2. **开发时**
   - 一次只做一个任务
   - 让 Roo Code 专注当前模块

3. **完成后**
   - 让 Roo Code 更新 `memory-bank/PROGRESS.md`
   - 运行测试

### 提示词示例

```
请阅读 memory-bank/PROGRESS.md 了解项目进度，然后帮我完成 [具体任务]。

要求：
1. 先阅读 memory-bank/ARCHITECTURE.md 了解架构
2. 参考现有代码风格
3. 添加类型注解
4. 编写测试
```

---

是否需要我帮你执行这些优化？