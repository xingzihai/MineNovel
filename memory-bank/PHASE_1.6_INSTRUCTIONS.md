# Phase 1.6 执行指令

> 执行者：Phase 1.6 Agent
> 角色：Web UI 开发专员
> 预计工时：1-1.5 小时
> 前置条件：Phase 1.5 已完成

---

## 一、阶段目标

创建一个 Web 配置界面，让用户可以方便地：
- 配置 API Key（Anthropic、OpenAI）
- 选择和配置模型路由
- 测试代理连接
- 查看代理状态

---

## 二、技术选型

使用 **Streamlit** 作为 Web 框架：

| 优势 | 说明 |
|-----|------|
| Python 原生 | 与项目技术栈一致 |
| 快速开发 | 无需前端知识 |
| 自动状态管理 | 简化表单处理 |
| 内置组件 | 文本输入、下拉选择、按钮等 |

---

## 三、任务清单

### 任务 1.6.1：更新依赖

**指令**：

更新 `requirements.txt`，添加 Streamlit：

```txt
# 核心依赖
aiosqlite>=0.19.0
pydantic>=2.0.0
openai>=1.0.0
anthropic>=0.18.0
python-dotenv>=1.0.0

# LiteLLM 代理
litellm>=1.0.0

# Web UI
streamlit>=1.30.0

# 测试
pytest>=7.0.0
pytest-asyncio>=0.21.0

# 工具
rich>=13.0.0
pyyaml>=6.0
```

---

### 任务 1.6.2：创建配置管理模块

**指令**：

创建 `src/web/config_manager.py`：

```python
"""配置管理模块 - 用于 Web UI"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    model: str
    api_key: str
    api_base: Optional[str] = None

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "."):
        self.config_dir = Path(config_dir)
        self.env_path = self.config_dir / ".env"
        self.litellm_path = self.config_dir / "litellm_config.yaml"
    
    def load_env(self) -> Dict[str, str]:
        """加载 .env 文件"""
        env_vars = {}
        if self.env_path.exists():
            with open(self.env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars
    
    def save_env(self, env_vars: Dict[str, str]) -> None:
        """保存 .env 文件"""
        # 读取原有内容，保留注释
        lines = []
        if self.env_path.exists():
            with open(self.env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # 更新变量
        updated_keys = set()
        for i, line in enumerate(lines):
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in env_vars:
                    lines[i] = f"{key}={env_vars[key]}\n"
                    updated_keys.add(key)
        
        # 添加新变量
        for key, value in env_vars.items():
            if key not in updated_keys:
                lines.append(f"{key}={value}\n")
        
        with open(self.env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def load_litellm_config(self) -> Dict[str, Any]:
        """加载 LiteLLM 配置"""
        if self.litellm_path.exists():
            with open(self.litellm_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {"model_list": [], "general_settings": {}}
    
    def save_litellm_config(self, config: Dict[str, Any]) -> None:
        """保存 LiteLLM 配置"""
        with open(self.litellm_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    def get_model_configs(self) -> Dict[str, ModelConfig]:
        """获取所有模型配置"""
        env_vars = self.load_env()
        litellm_config = self.load_litellm_config()
        
        models = {}
        for item in litellm_config.get("model_list", []):
            model_name = item.get("model_name", "")
            params = item.get("litellm_params", {})
            
            # 从环境变量获取 API Key
            api_key_env = params.get("api_key", "")
            if api_key_env.startswith("os.environ/"):
                env_key = api_key_env.replace("os.environ/", "")
                api_key = env_vars.get(env_key, "")
            else:
                api_key = api_key_env
            
            models[model_name] = ModelConfig(
                name=model_name,
                model=params.get("model", ""),
                api_key=api_key,
                api_base=params.get("api_base")
            )
        
        return models
    
    def update_model_config(self, model_name: str, api_key: str) -> None:
        """更新模型配置"""
        env_vars = self.load_env()
        litellm_config = self.load_litellm_config()
        
        # 确定环境变量名
        env_key_map = {
            "writer": "ANTHROPIC_API_KEY",
            "character": "ANTHROPIC_API_KEY",
            "auditor": "OPENAI_API_KEY",
            "planner": "OPENAI_API_KEY",
            "local": None
        }
        
        env_key = env_key_map.get(model_name)
        if env_key:
            env_vars[env_key] = api_key
        
        # 保存
        self.save_env(env_vars)
```

---

### 任务 1.6.3：创建代理状态检查模块

**指令**：

创建 `src/web/proxy_status.py`：

```python
"""代理状态检查"""

import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ProxyStatus:
    """代理状态"""
    is_running: bool
    url: str
    error: Optional[str] = None
    models: list = None

def check_proxy_status(base_url: str = "http://localhost:4000") -> ProxyStatus:
    """检查代理状态"""
    try:
        # 检查健康状态
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            # 获取可用模型
            models_response = requests.get(f"{base_url}/v1/models", timeout=5)
            models = []
            if models_response.status_code == 200:
                data = models_response.json()
                models = [m["id"] for m in data.get("data", [])]
            
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

def test_model_connection(
    model: str,
    base_url: str = "http://localhost:4000",
    api_key: str = "sk-minenovel-proxy-2024"
) -> Dict[str, Any]:
    """测试模型连接"""
    try:
        from openai import OpenAI
        
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

---

### 任务 1.6.4：创建 Streamlit Web UI

**指令**：

创建 `src/web/app.py`：

```python
"""MineNovel 配置管理 Web UI"""

import streamlit as st
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.web.config_manager import ConfigManager
from src.web.proxy_status import check_proxy_status, test_model_connection

# 页面配置
st.set_page_config(
    page_title="MineNovel 配置管理",
    page_icon="📚",
    layout="wide"
)

# 标题
st.title("📚 MineNovel 配置管理")
st.markdown("---")

# 初始化配置管理器
config_manager = ConfigManager()

# 侧边栏 - 导航
page = st.sidebar.radio(
    "导航",
    ["🏠 首页", "🔑 API 配置", "🤖 模型路由", "📊 代理状态", "🧪 连接测试"]
)

# ============ 首页 ============
if page == "🏠 首页":
    st.header("欢迎使用 MineNovel 配置管理")
    
    st.markdown("""
    ### 功能说明
    
    - **🔑 API 配置**：配置 Anthropic 和 OpenAI 的 API Key
    - **🤖 模型路由**：配置不同任务使用的模型
    - **📊 代理状态**：查看 LiteLLM 代理运行状态
    - **🧪 连接测试**：测试 API 连接是否正常
    
    ### 快速开始
    
    1. 在「API 配置」页面填入你的 API Key
    2. 在「模型路由」页面选择使用的模型
    3. 启动代理服务：`./scripts/start_proxy.sh`
    4. 在「连接测试」页面验证配置
    """)
    
    # 显示当前状态
    st.subheader("当前状态")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("代理状态", "运行中" if check_proxy_status().is_running else "未启动")
    
    with col2:
        env_vars = config_manager.load_env()
        has_anthropic = bool(env_vars.get("ANTHROPIC_API_KEY"))
        has_openai = bool(env_vars.get("OPENAI_API_KEY"))
        st.metric("API Key 配置", f"{sum([has_anthropic, has_openai])}/2")

# ============ API 配置 ============
elif page == "🔑 API 配置":
    st.header("API Key 配置")
    
    st.markdown("""
    配置你的 API Key。这些密钥将存储在本地 `.env` 文件中，不会上传到任何服务器。
    """)
    
    # 加载当前配置
    env_vars = config_manager.load_env()
    
    # Anthropic API Key
    st.subheader("Anthropic API Key")
    st.markdown("用于 Claude 模型（writer、character）")
    
    anthropic_key = st.text_input(
        "Anthropic API Key",
        value=env_vars.get("ANTHROPIC_API_KEY", ""),
        type="password",
        placeholder="sk-ant-..."
    )
    
    # OpenAI API Key
    st.subheader("OpenAI API Key")
    st.markdown("用于 GPT 模型（auditor、planner）")
    
    openai_key = st.text_input(
        "OpenAI API Key",
        value=env_vars.get("OPENAI_API_KEY", ""),
        type="password",
        placeholder="sk-..."
    )
    
    # 保存按钮
    if st.button("💾 保存配置", type="primary"):
        new_env = {}
        if anthropic_key:
            new_env["ANTHROPIC_API_KEY"] = anthropic_key
        if openai_key:
            new_env["OPENAI_API_KEY"] = openai_key
        
        config_manager.save_env(new_env)
        st.success("✅ 配置已保存！")
        st.rerun()
    
    # 显示当前状态
    st.markdown("---")
    st.subheader("当前配置状态")
    
    col1, col2 = st.columns(2)
    with col1:
        if env_vars.get("ANTHROPIC_API_KEY"):
            key = env_vars["ANTHROPIC_API_KEY"]
            st.info(f"Anthropic: {key[:8]}...{key[-4:]}")
        else:
            st.warning("Anthropic: 未配置")
    
    with col2:
        if env_vars.get("OPENAI_API_KEY"):
            key = env_vars["OPENAI_API_KEY"]
            st.info(f"OpenAI: {key[:8]}...{key[-4:]}")
        else:
            st.warning("OpenAI: 未配置")

# ============ 模型路由 ============
elif page == "🤖 模型路由":
    st.header("模型路由配置")
    
    st.markdown("""
    配置不同任务使用的模型。这些配置将保存到 `litellm_config.yaml` 文件中。
    """)
    
    # 加载当前配置
    litellm_config = config_manager.load_litellm_config()
    models = config_manager.get_model_configs()
    
    # 显示模型配置
    st.subheader("当前模型路由")
    
    model_info = {
        "writer": {"desc": "小说写作", "default": "claude-3-opus-20240229", "provider": "Anthropic"},
        "auditor": {"desc": "审计校验", "default": "gpt-4o", "provider": "OpenAI"},
        "planner": {"desc": "规划", "default": "gpt-4-turbo", "provider": "OpenAI"},
        "character": {"desc": "角色内驱力", "default": "claude-3-sonnet-20240229", "provider": "Anthropic"},
        "local": {"desc": "本地模型", "default": "ollama/llama3", "provider": "Ollama"},
    }
    
    for model_name, info in model_info.items():
        with st.expander(f"**{model_name}** - {info['desc']} ({info['provider']})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                current_model = models.get(model_name)
                model_value = st.text_input(
                    "模型名称",
                    value=current_model.model if current_model else info["default"],
                    key=f"model_{model_name}"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("测试", key=f"test_{model_name}"):
                    with st.spinner("测试中..."):
                        result = test_model_connection(model_value)
                        if result["success"]:
                            st.success(f"✅ 连接成功：{result['response'][:50]}...")
                        else:
                            st.error(f"❌ 连接失败：{result['error']}")

# ============ 代理状态 ============
elif page == "📊 代理状态":
    st.header("LiteLLM 代理状态")
    
    # 检查代理状态
    status = check_proxy_status()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if status.is_running:
            st.success("✅ 代理服务运行中")
            st.metric("服务地址", status.url)
            if status.models:
                st.write("**可用模型：**")
                for model in status.models:
                    st.write(f"- {model}")
        else:
            st.error(f"❌ 代理服务未运行")
            if status.error:
                st.warning(f"错误：{status.error}")
    
    with col2:
        st.subheader("启动代理")
        st.markdown("""
        **方式1：直接启动**
        ```bash
        ./scripts/start_proxy.sh
        ```
        
        **方式2：Docker 启动**
        ```bash
        docker-compose -f docker-compose.litellm.yml up -d
        ```
        """)
        
        if st.button("🔄 刷新状态"):
            st.rerun()

# ============ 连接测试 ============
elif page == "🧪 连接测试":
    st.header("API 连接测试")
    
    st.markdown("""
    测试 API 连接是否正常。请确保：
    1. 已配置 API Key
    2. 代理服务已启动
    """)
    
    # 选择模型
    model_options = ["writer", "auditor", "planner", "character", "local"]
    selected_model = st.selectbox("选择模型", model_options)
    
    # 测试消息
    test_message = st.text_area(
        "测试消息",
        value="你好，这是一个测试消息。请简短回复。",
        height=100
    )
    
    # 发送测试
    if st.button("🚀 发送测试", type="primary"):
        if not check_proxy_status().is_running:
            st.error("❌ 代理服务未运行，请先启动代理")
        else:
            with st.spinner("发送中..."):
                result = test_model_connection(selected_model)
                
                if result["success"]:
                    st.success("✅ 连接成功！")
                    st.subheader("响应")
                    st.write(result["response"])
                else:
                    st.error(f"❌ 连接失败：{result['error']}")

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    MineNovel Configuration Manager v0.1.0
</div>
""", unsafe_allow_html=True)
```

---

### 任务 1.6.5：创建 Web 模块初始化文件

**指令**：

创建 `src/web/__init__.py`：

```python
"""MineNovel Web UI 模块"""

from .config_manager import ConfigManager
from .proxy_status import check_proxy_status, test_model_connection

__all__ = ["ConfigManager", "check_proxy_status", "test_model_connection"]
```

---

### 任务 1.6.6：创建启动脚本

**指令**：

创建 `scripts/run_web.ps1`（Windows）：

```powershell
# 启动 MineNovel 配置管理 Web UI

Write-Host "Starting MineNovel Web UI..." -ForegroundColor Green

# 检查依赖
python -c "import streamlit" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing streamlit..." -ForegroundColor Yellow
    pip install streamlit pyyaml
}

# 启动 Web UI
streamlit run src/web/app.py --server.port 8501
```

创建 `scripts/run_web.sh`（Linux/Mac）：

```bash
#!/bin/bash
# 启动 MineNovel 配置管理 Web UI

echo "Starting MineNovel Web UI..."

# 检查依赖
python -c "import streamlit" 2>/dev/null || pip install streamlit pyyaml

# 启动 Web UI
streamlit run src/web/app.py --server.port 8501
```

---

## 四、验收标准

| 标准 | 验证命令 |
|-----|---------|
| Web 模块可导入 | `python -c "from src.web import ConfigManager"` |
| Streamlit 可启动 | `streamlit run src/web/app.py --server.headless true` |
| 配置可保存 | 在 Web UI 中配置 API Key 并保存 |
| 状态可检查 | Web UI 显示代理状态 |

---

## 五、使用说明

### 启动 Web UI

```bash
# Windows
.\scripts\run_web.ps1

# Linux/Mac
./scripts/run_web.sh

# 或直接运行
streamlit run src/web/app.py
```

### 访问地址

```
http://localhost:8501
```

### 功能截图预期

```
┌─────────────────────────────────────────────┐
│  📚 MineNovel 配置管理                       │
├─────────────────────────────────────────────┤
│  🔑 API 配置  🤖 模型路由  📊 代理状态       │
├─────────────────────────────────────────────┤
│                                             │
│  Anthropic API Key: [••••••••••••]         │
│                                             │
│  OpenAI API Key: [••••••••••••]            │
│                                             │
│  [💾 保存配置]                              │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 六、禁止事项

1. ❌ 不要在代码中硬编码 API Key
2. ❌ 不要提交包含真实 API Key 的配置文件
3. ❌ 不要添加超出任务范围的功能

---

## 七、汇报格式

完成后，请按以下格式汇报：

```markdown
# Phase 1.6 执行汇报

## 执行摘要

- 开始时间：YYYY-MM-DD HH:MM
- 结束时间：YYYY-MM-DD HH:MM
- 状态：成功 / 部分成功 / 失败

## 任务完成情况

| 任务 | 状态 | 备注 |
|-----|------|------|
| 1.6.1 更新依赖 | ✅ | |
| 1.6.2 创建配置管理模块 | ✅ | |
| 1.6.3 创建代理状态检查模块 | ✅ | |
| 1.6.4 创建 Streamlit Web UI | ✅ | |
| 1.6.5 创建 Web 模块初始化文件 | ✅ | |
| 1.6.6 创建启动脚本 | ✅ | |

## 新增文件

- src/web/__init__.py
- src/web/config_manager.py
- src/web/proxy_status.py
- src/web/app.py
- scripts/run_web.ps1
- scripts/run_web.sh

## 验收结果

| 标准 | 结果 |
|-----|------|
| Web 模块可导入 | ✅ |
| Streamlit 可启动 | ✅ |
| 配置可保存 | ✅ |
| 状态可检查 | ✅ |

## 功能截图

[可选] 提供 Web UI 截图
```

---

**开始执行！完成后请按汇报格式提交结果。**