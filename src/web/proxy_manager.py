"""代理管理模块 - 完全后台运行"""

import subprocess
import sys
import time
import os
import yaml
from pathlib import Path

# 全局代理进程
_proxy_process = None


def ensure_litellm_config(project_root: Path, model_pool) -> bool:
    """确保 litellm_config.yaml 存在且是最新的"""
    config_path = project_root / "litellm_config.yaml"
    
    try:
        config = model_pool.export_to_litellm_config()
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        print(f"生成配置文件失败: {e}")
        return False


def start_proxy_background(config_path: str, port: int = 4000) -> dict:
    """完全后台启动代理（无窗口）"""
    global _proxy_process
    
    python_exe = sys.executable
    scripts_dir = Path(python_exe).parent / "Scripts"
    litellm_exe = scripts_dir / "litellm.exe"
    
    if sys.platform == 'win32':
        # Windows: 使用 litellm.exe
        if litellm_exe.exists():
            exe_path = str(litellm_exe)
            args = [exe_path, "-c", config_path, "--port", str(port)]
        else:
            return {"success": False, "error": "litellm.exe not found"}
        
        # 使用 subprocess 完全隐藏窗口
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        _proxy_process = subprocess.Popen(
            args,
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            startupinfo=startupinfo
        )
        
        return {"success": True, "pid": _proxy_process.pid}
    
    else:
        # Linux/Mac
        _proxy_process = subprocess.Popen(
            ["litellm", "-c", config_path, "--port", str(port)],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
        return {"success": True, "pid": _proxy_process.pid}


def start_proxy_if_not_running(check_func, model_pool=None, max_wait: int = 10) -> dict:
    """检查代理状态，如果未运行则自动启动"""
    global _proxy_process
    
    # 先检查是否已在运行
    status = check_func()
    if status.is_running:
        return {
            "started": False,
            "message": "代理已在运行中",
            "already_running": True
        }
    
    project_root = Path(__file__).parent.parent.parent
    litellm_config = project_root / "litellm_config.yaml"
    
    # 生成/更新配置
    if model_pool:
        if not ensure_litellm_config(project_root, model_pool):
            return {
                "started": False,
                "message": "无法生成配置文件",
                "already_running": False
            }
    
    if not litellm_config.exists():
        return {
            "started": False,
            "message": "配置文件不存在，请先添加模型",
            "already_running": False
        }
    
    if model_pool:
        enabled_models = model_pool.list_models(enabled_only=True)
        if not enabled_models:
            return {
                "started": False,
                "message": "没有启用的模型",
                "already_running": False
            }
    
    # 后台启动
    result = start_proxy_background(str(litellm_config), 4000)
    
    if not result["success"]:
        return {
            "started": False,
            "message": "启动进程失败",
            "already_running": False
        }
    
    # 等待启动
    for _ in range(max_wait):
        time.sleep(1)
        status = check_func()
        if status.is_running:
            return {
                "started": True,
                "message": "代理启动成功",
                "already_running": False
            }
    
    return {
        "started": False,
        "message": f"启动超时（{max_wait}秒）",
        "already_running": False
    }


def stop_proxy() -> dict:
    """停止代理服务"""
    global _proxy_process
    
    try:
        if sys.platform == 'win32':
            # 静默终止
            subprocess.run(
                ['taskkill', '/F', '/IM', 'litellm.exe'],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            # 通过端口查找
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in result.stdout.split('\n'):
                if ':4000' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        subprocess.run(
                            ['taskkill', '/F', '/PID', pid],
                            capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
        else:
            subprocess.run(['pkill', '-f', 'litellm'], capture_output=True)
        
        _proxy_process = None
        time.sleep(1)
        return {"success": True, "message": "代理已停止"}
    except Exception as e:
        return {"success": False, "message": f"停止失败: {str(e)}"}