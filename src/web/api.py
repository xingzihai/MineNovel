"""MineNovel Web API

FastAPI 后端 + 纯 HTML/CSS/JS 前端
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
import subprocess
import sys
import time
import json
import yaml

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 创建 FastAPI 应用
app = FastAPI(title="MineNovel Config API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
STATIC_DIR = PROJECT_ROOT / "src" / "web" / "static"
STATIC_DIR.mkdir(exist_ok=True)

# ==================== 数据模型 ====================

class ModelInstanceCreate(BaseModel):
    id: str
    name: str
    model: str
    provider: str
    api_key: str = ""
    base_url: Optional[str] = None
    group: str = "other"
    enabled: bool = True
    is_default: bool = False
    description: str = ""
    max_tokens: int = 4096
    supports_stream: bool = True


class ModelInstanceUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    group: Optional[str] = None
    enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    description: Optional[str] = None
    max_tokens: Optional[int] = None
    supports_stream: Optional[bool] = None


class RouteUpdate(BaseModel):
    task_type: str
    model_id: str


class TestRequest(BaseModel):
    model_id: str
    message: str = "Hello, this is a test."


# ==================== 模型池操作 ====================

def get_model_pool():
    """获取模型池实例"""
    from src.web.model_pool import ModelPool
    return ModelPool(str(PROJECT_ROOT))


# ==================== API 路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index():
    """主页"""
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding='utf-8'))
    return HTMLResponse(content="<h1>Please create index.html</h1>")


# ---------- 模型池 API ----------

@app.get("/api/models")
async def list_models():
    """列出所有模型"""
    pool = get_model_pool()
    models = pool.list_models()
    return {
        "models": [m.to_dict() for m in models],
        "stats": pool.get_stats()
    }


@app.post("/api/models")
async def add_model(model: ModelInstanceCreate):
    """添加模型"""
    pool = get_model_pool()
    from src.web.model_pool import ModelInstance
    
    if pool.get_model(model.id):
        raise HTTPException(400, f"Model ID '{model.id}' already exists")
    
    new_model = ModelInstance(**model.dict())
    pool.add_model(new_model)
    return {"success": True, "model": new_model.to_dict()}


@app.get("/api/models/{model_id}")
async def get_model(model_id: str):
    """获取模型详情"""
    pool = get_model_pool()
    model = pool.get_model(model_id)
    if not model:
        raise HTTPException(404, f"Model '{model_id}' not found")
    return model.to_dict()


@app.put("/api/models/{model_id}")
async def update_model(model_id: str, update: ModelInstanceUpdate):
    """更新模型"""
    pool = get_model_pool()
    model = pool.get_model(model_id)
    if not model:
        raise HTTPException(404, f"Model '{model_id}' not found")
    
    # 更新字段
    update_data = update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(model, key, value)
    
    pool.update_model(model)
    return {"success": True, "model": model.to_dict()}


@app.delete("/api/models/{model_id}")
async def delete_model(model_id: str):
    """删除模型"""
    pool = get_model_pool()
    if not pool.remove_model(model_id):
        raise HTTPException(404, f"Model '{model_id}' not found")
    return {"success": True}


@app.post("/api/models/{model_id}/default")
async def set_default_model(model_id: str):
    """设置默认模型"""
    pool = get_model_pool()
    if not pool.set_default_model(model_id):
        raise HTTPException(404, f"Model '{model_id}' not found")
    return {"success": True}


@app.post("/api/models/{model_id}/toggle")
async def toggle_model(model_id: str):
    """启用/禁用模型"""
    pool = get_model_pool()
    model = pool.get_model(model_id)
    if not model:
        raise HTTPException(404, f"Model '{model_id}' not found")
    
    if model.enabled:
        pool.disable_model(model_id)
    else:
        pool.enable_model(model_id)
    
    return {"success": True, "enabled": not model.enabled}


# ---------- 路由 API ----------

@app.get("/api/routes")
async def list_routes():
    """列出所有路由"""
    pool = get_model_pool()
    routes = pool.list_routes()
    return {
        "routes": [{"task_type": r.task_type, "model_id": r.model_id, "description": r.description} for r in routes]
    }


@app.post("/api/routes")
async def set_route(route: RouteUpdate):
    """设置路由"""
    pool = get_model_pool()
    if not pool.set_route(route.task_type, route.model_id):
        raise HTTPException(404, f"Model '{route.model_id}' not found")
    return {"success": True}


@app.delete("/api/routes/{task_type}")
async def delete_route(task_type: str):
    """删除路由"""
    pool = get_model_pool()
    pool.remove_route(task_type)
    return {"success": True}


# ---------- 代理 API ----------

@app.get("/api/proxy/status")
async def get_proxy_status():
    """获取代理状态"""
    from src.web.proxy_status import check_proxy_status
    status = check_proxy_status()
    return {
        "is_running": status.is_running,
        "url": status.url,
        "error": status.error,
        "models": status.models
    }


@app.post("/api/proxy/start")
async def start_proxy():
    """启动代理"""
    from src.web.proxy_manager import start_proxy_if_not_running
    from src.web.proxy_status import check_proxy_status
    
    pool = get_model_pool()
    result = start_proxy_if_not_running(check_proxy_status, model_pool=pool, max_wait=15)
    return result


@app.post("/api/proxy/stop")
async def stop_proxy():
    """停止代理"""
    from src.web.proxy_manager import stop_proxy
    result = stop_proxy()
    return result


# ---------- 测试 API ----------

@app.post("/api/test")
async def test_connection(req: TestRequest):
    """测试连接"""
    from src.web.proxy_status import test_model_connection, check_proxy_status
    import requests
    
    # 直接检查代理健康状态（不依赖返回值）
    try:
        health = requests.get("http://localhost:4000/health", 
                             headers={"Authorization": "Bearer sk-minenovel-proxy-2024"},
                             timeout=5)
        if health.status_code != 200:
            raise HTTPException(400, f"代理服务异常: HTTP {health.status_code}")
    except requests.exceptions.ConnectionError:
        raise HTTPException(400, "代理服务未运行，请先启动代理")
    except requests.exceptions.Timeout:
        raise HTTPException(400, "代理服务响应超时")
    
    pool = get_model_pool()
    model = pool.get_model(req.model_id)
    if not model:
        raise HTTPException(404, f"模型 '{req.model_id}' 不存在")
    
    result = test_model_connection(
        model=model.model,
        test_message=req.message
    )
    return result


# ---------- 导出 API ----------

@app.get("/api/export/litellm")
async def export_litellm_config():
    """导出 LiteLLM 配置"""
    pool = get_model_pool()
    config = pool.export_to_litellm_config()
    return config


# ---------- 静态文件 ----------

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8501)