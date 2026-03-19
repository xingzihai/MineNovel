# Phase 1.6 检查与续接指令

> 执行者：Phase 1.6 续接 Agent
> 角色：代码检查与续接专员
> 预计工时：30-45 分钟
> 背景：上一个 Agent 因上下文限制中断

---

## 一、任务目标

1. 检查 Phase 1.6 已完成的内容
2. 继续未完成的任务
3. 完成验收

---

## 二、检查清单

### 步骤 1：检查已创建的文件

运行以下命令检查文件是否存在：

```bash
# Windows PowerShell
cd MineNovel

# 检查 Web 模块文件
Test-Path src/web/__init__.py
Test-Path src/web/config_manager.py
Test-Path src/web/proxy_status.py
Test-Path src/web/app.py

# 检查启动脚本
Test-Path scripts/run_web.ps1
Test-Path scripts/run_web.sh

# 检查依赖更新
Select-String -Path requirements.txt -Pattern "streamlit"
```

**记录结果**：

| 文件 | 状态 |
|-----|------|
| src/web/__init__.py | ✅/❌ |
| src/web/config_manager.py | ✅/❌ |
| src/web/proxy_status.py | ✅/❌ |
| src/web/app.py | ✅/❌ |
| scripts/run_web.ps1 | ✅/❌ |
| scripts/run_web.sh | ✅/❌ |
| requirements.txt (streamlit) | ✅/❌ |

---

### 步骤 2：检查代码完整性

如果文件存在，检查代码是否完整：

```bash
# 检查 app.py 是否有语法错误
python -c "import ast; ast.parse(open('src/web/app.py').read())"

# 检查模块是否可导入
python -c "from src.web import ConfigManager; print('OK')"
python -c "from src.web import check_proxy_status; print('OK')"
```

---

## 三、续接任务

根据检查结果，执行以下任务：

### 任务 A：如果文件不存在，创建文件

参考 `memory-bank/PHASE_1.6_INSTRUCTIONS.md` 中的完整代码，创建缺失的文件。

### 任务 B：如果文件存在但不完整，修复文件

检查文件是否有以下关键内容：

**src/web/config_manager.py 必须包含**：
- `ConfigManager` 类
- `load_env()` 方法
- `save_env()` 方法
- `load_litellm_config()` 方法
- `get_model_configs()` 方法

**src/web/proxy_status.py 必须包含**：
- `check_proxy_status()` 函数
- `test_model_connection()` 函数

**src/web/app.py 必须包含**：
- Streamlit 页面配置
- 5 个页面（首页、API配置、模型路由、代理状态、连接测试）

### 任务 C：确保目录结构正确

```bash
# 创建目录（如果不存在）
New-Item -ItemType Directory -Force -Path src/web
```

---

## 四、快速创建缺失文件

### 如果 src/web/ 目录不存在或文件缺失

创建 `src/web/__init__.py`：

```python
"""MineNovel Web UI 模块"""

from .config_manager import ConfigManager
from .proxy_status import check_proxy_status, test_model_connection

__all__ = ["ConfigManager", "check_proxy_status", "test_model_connection"]
```

创建 `src/web/config_manager.py`（核心代码）：

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
        lines = []
        if self.env_path.exists():
            with open(self.env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        updated_keys = set()
        for i, line in enumerate(lines):
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in env_vars:
                    lines[i] = f"{key}={env_vars[key]}\n"
                    updated_keys.add(key)
        
        for key, value in env_vars.items():
            if key not in updated_keys:
                lines.append(f"{key}={value}\n")
        
        with open(self.env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def load_litellm_config(self) -> Dict[str, Any]:
        """加载 LiteLLM 配置"""
        if self.litellm_path.exists():
            with open(self.litellm_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {"model_list": []}
        return {"model_list": []}
    
    def get_model_configs(self) -> Dict[str, ModelConfig]:
        """获取所有模型配置"""
        env_vars = self.load_env()
        litellm_config = self.load_litellm_config()
        
        models = {}
        for item in litellm_config.get("model_list", []):
            model_name = item.get("model_name", "")
            params = item.get("litellm_params", {})
            
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
```

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
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            models_response = requests.get(f"{base_url}/v1/models", timeout=5)
            models = []
            if models_response.status_code == 200:
                data = models_response.json()
                models = [m["id"] for m in data.get("data", [])]
            
            return ProxyStatus(is_running=True, url=base_url, models=models)
        else:
            return ProxyStatus(is_running=False, url=base_url, error=f"HTTP {response.status_code}")
    except requests.exceptions.ConnectionError:
        return ProxyStatus(is_running=False, url=base_url, error="无法连接到代理服务")
    except requests.exceptions.Timeout:
        return ProxyStatus(is_running=False, url=base_url, error="连接超时")
    except Exception as e:
        return ProxyStatus(is_running=False, url=base_url, error=str(e))

def test_model_connection(model: str, base_url: str = "http://localhost:4000", api_key: str = "sk-minenovel-proxy-2024") -> Dict[str, Any]:
    """测试模型连接"""
    try:
        from openai import OpenAI
        client = OpenAI(base_url=base_url, api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        return {"success": True, "response": response.choices[0].message.content}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

创建 `scripts/run_web.ps1`：

```powershell
# 启动 MineNovel 配置管理 Web UI
Write-Host "Starting MineNovel Web UI..." -ForegroundColor Green
streamlit run src/web/app.py --server.port 8501
```

---

## 五、更新依赖

确保 `requirements.txt` 包含：

```txt
# Web UI
streamlit>=1.30.0
pyyaml>=6.0
requests>=2.28.0
```

运行：

```bash
pip install streamlit pyyaml requests
```

---

## 六、验收测试

### 测试 1：模块导入

```bash
python -c "from src.web import ConfigManager, check_proxy_status, test_model_connection; print('All imports OK')"
```

### 测试 2：Streamlit 启动

```bash
streamlit run src/web/app.py --server.headless true --server.port 8501
```

检查是否输出类似：

```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
```

### 测试 3：配置保存

```python
from src.web.config_manager import ConfigManager
cm = ConfigManager()
cm.save_env({"TEST_KEY": "test_value"})
env = cm.load_env()
assert env.get("TEST_KEY") == "test_value"
print("Config save/load OK")
```

---

## 七、汇报格式

完成后，请按以下格式汇报：

```markdown
# Phase 1.6 续接汇报

## 执行摘要

- 开始时间：YYYY-MM-DD HH:MM
- 结束时间：YYYY-MM-DD HH:MM
- 状态：成功 / 部分成功 / 失败

## 检查结果

| 文件 | 原状态 | 现状态 |
|-----|-------|-------|
| src/web/__init__.py | ✅/❌ | ✅/❌ |
| src/web/config_manager.py | ✅/❌ | ✅/❌ |
| src/web/proxy_status.py | ✅/❌ | ✅/❌ |
| src/web/app.py | ✅/❌ | ✅/❌ |
| scripts/run_web.ps1 | ✅/❌ | ✅/❌ |

## 执行的操作

- [ ] 检查文件状态
- [ ] 创建缺失文件
- [ ] 修复不完整文件
- [ ] 更新依赖
- [ ] 测试导入
- [ ] 测试 Streamlit 启动

## 验收结果

| 测试 | 结果 |
|-----|------|
| 模块导入 | ✅/❌ |
| Streamlit 启动 | ✅/❌ |
| 配置保存/加载 | ✅/❌ |

## 新增/修改的文件

- [列出所有新增或修改的文件]

## 遇到的问题

[如有问题，按格式记录]
```

---

**开始检查并续接！完成后请按汇报格式提交结果。**