"""MineNovel 配置管理 Web UI v2.2

支持：
- 可插拔模型池管理
- 模型编辑
- 模型路由配置
- 代理状态监控
- 代理自动启动
"""

import streamlit as st
from pathlib import Path
import sys
import uuid
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.web.model_pool import ModelPool, ModelInstance, ModelProvider, ModelGroup
from src.web.proxy_status import check_proxy_status, test_model_connection
from src.web.proxy_manager import start_proxy_if_not_running, stop_proxy

# 页面配置
st.set_page_config(
    page_title="MineNovel 配置管理",
    page_icon="📚",
    layout="wide"
)

# 初始化模型池
model_pool = ModelPool(str(project_root))

# 初始化 session state
if "editing_model_id" not in st.session_state:
    st.session_state.editing_model_id = None
if "proxy_auto_started" not in st.session_state:
    st.session_state.proxy_auto_started = False
if "proxy_start_message" not in st.session_state:
    st.session_state.proxy_start_message = ""

# 自动启动代理（仅在首次加载时）
if not st.session_state.proxy_auto_started:
    result = start_proxy_if_not_running(check_proxy_status, model_pool=model_pool, max_wait=15)
    st.session_state.proxy_auto_started = True
    st.session_state.proxy_start_message = result["message"]
    if result["started"]:
        st.session_state.proxy_running = True
    elif result["already_running"]:
        st.session_state.proxy_running = True
    else:
        st.session_state.proxy_running = False

# 标题
st.title("📚 MineNovel 配置管理")

# 显示代理状态条
proxy_status = check_proxy_status()
if proxy_status.is_running:
    st.success(f"🟢 代理运行中 (localhost:4000)")
else:
    st.error("🔴 代理未运行 - 请在「代理状态」页面手动启动")

st.markdown("---")

# 侧边栏导航
page = st.sidebar.radio(
    "导航",
    ["🏠 首页", "🗄️ 模型池", "🔀 模型路由", "📊 代理状态", "🧪 连接测试"]
)

# ============ 首页 ============
if page == "🏠 首页":
    st.header("欢迎使用 MineNovel 配置管理")
    
    st.markdown("""
    ### 功能说明
    
    - **🗄️ 模型池**：管理模型实例（添加、编辑、删除、启用/禁用、设为默认）
    - **🔀 模型路由**：为不同任务分配模型
    - **📊 代理状态**：启动和监控 LiteLLM 代理服务（**必须运行**）
    - **🧪 连接测试**：通过代理测试模型连接
    
    ### 快速开始
    
    1. 在「模型池」页面添加你的模型
    2. 在「代理状态」页面启动代理服务
    3. 在「连接测试」页面验证配置
    """)
    
    # 统计信息
    stats = model_pool.get_stats()
    status = check_proxy_status()
    
    st.subheader("📊 当前状态")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("模型总数", stats["total"])
    with col2:
        st.metric("已启用", stats["enabled"])
    with col3:
        st.metric("路由配置", stats["routes"])
    with col4:
        if status.is_running:
            st.metric("代理状态", "🟢 运行中")
        else:
            st.metric("代理状态", "🔴 未启动")

# ============ 模型池管理 ============
elif page == "🗄️ 模型池":
    st.header("🗄️ 模型池管理")
    
    # 检查是否有正在编辑的模型
    editing_model = None
    if st.session_state.editing_model_id:
        editing_model = model_pool.get_model(st.session_state.editing_model_id)
        if not editing_model:
            st.session_state.editing_model_id = None
    
    # 如果有模型在编辑中，显示编辑表单
    if editing_model:
        st.subheader(f"✏️ 编辑模型：{editing_model.name}")
        
        with st.form("edit_model_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                edit_name = st.text_input("显示名称 *", value=editing_model.name)
                # ID 不可编辑
                st.text_input("唯一标识", value=editing_model.id, disabled=True, help="ID 创建后不可修改")
                edit_model_type = st.text_input("模型名称 *", value=editing_model.model,
                                                help="实际调用时使用的模型名")
                
            with col2:
                provider_options = [p.value for p in ModelProvider]
                provider_index = provider_options.index(editing_model.provider) if editing_model.provider in provider_options else 0
                edit_provider = st.selectbox(
                    "提供商",
                    options=provider_options,
                    index=provider_index,
                    format_func=lambda x: {
                        "openai": "OpenAI",
                        "anthropic": "Anthropic",
                        "azure": "Azure OpenAI",
                        "deepseek": "DeepSeek",
                        "moonshot": "Moonshot (Kimi)",
                        "zhipu": "智谱 AI",
                        "ollama": "Ollama (本地)",
                        "custom": "自定义"
                    }.get(x, x)
                )
                
                group_options = [g.value for g in ModelGroup]
                group_index = group_options.index(editing_model.group) if editing_model.group in group_options else 5
                edit_group = st.selectbox(
                    "分组",
                    options=group_options,
                    index=group_index,
                    format_func=lambda x: {
                        "creative": "✍️ 创意写作",
                        "analysis": "🔍 分析审计",
                        "planning": "📋 规划推理",
                        "character": "🎭 角色扮演",
                        "local": "💻 本地模型",
                        "other": "📦 其他"
                    }.get(x, x)
                )
                
                edit_is_default = st.checkbox("设为默认模型", value=editing_model.is_default)
                edit_is_enabled = st.checkbox("启用模型", value=editing_model.enabled)
            
            st.markdown("---")
            st.subheader("API 配置")
            
            col1, col2 = st.columns(2)
            with col1:
                edit_api_key = st.text_input("API Key", value=editing_model.api_key, type="password", placeholder="sk-...")
            with col2:
                edit_base_url = st.text_input("API 端点（可选）", value=editing_model.base_url or "", placeholder="https://api.example.com")
            
            st.markdown("---")
            st.subheader("高级设置")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                edit_max_tokens = st.number_input("最大 Tokens", min_value=100, max_value=128000, value=editing_model.max_tokens)
            with col2:
                edit_supports_stream = st.checkbox("支持流式", value=editing_model.supports_stream)
            with col3:
                edit_description = st.text_input("描述", value=editing_model.description, placeholder="模型用途说明")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                submitted = st.form_submit_button("✅ 保存修改", type="primary")
            with col2:
                cancel = st.form_submit_button("❌ 取消")
            
            if submitted:
                if not edit_name or not edit_model_type:
                    st.error("请填写必填字段")
                else:
                    updated_model = ModelInstance(
                        id=editing_model.id,
                        name=edit_name,
                        model=edit_model_type,
                        provider=edit_provider,
                        api_key=edit_api_key,
                        base_url=edit_base_url if edit_base_url else None,
                        group=edit_group,
                        enabled=edit_is_enabled,
                        is_default=edit_is_default,
                        description=edit_description,
                        max_tokens=edit_max_tokens,
                        supports_stream=edit_supports_stream
                    )
                    model_pool.update_model(updated_model)
                    st.session_state.editing_model_id = None
                    st.success(f"✅ 模型「{edit_name}」已更新！")
                    st.rerun()
            
            if cancel:
                st.session_state.editing_model_id = None
                st.rerun()
        
        st.markdown("---")
    
    tab1, tab2 = st.tabs(["📋 模型列表", "➕ 添加模型"])
    
    # --- 模型列表 ---
    with tab1:
        models = model_pool.list_models()
        
        if not models:
            st.info("暂无模型，请切换到「添加模型」标签添加你的第一个模型")
        else:
            # 按分组显示
            groups = model_pool.get_groups()
            
            for group_name, group_models in groups.items():
                group_label = {
                    "creative": "✍️ 创意写作",
                    "analysis": "🔍 分析审计",
                    "planning": "📋 规划推理",
                    "character": "🎭 角色扮演",
                    "local": "💻 本地模型",
                    "other": "📦 其他"
                }.get(group_name, f"📦 {group_name}")
                
                with st.expander(f"{group_label} ({len(group_models)})", expanded=True):
                    for model in group_models:
                        # 跳过正在编辑的模型
                        if st.session_state.editing_model_id == model.id:
                            continue
                            
                        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                        
                        with col1:
                            default_badge = " ⭐默认" if model.is_default else ""
                            status_badge = "🟢" if model.enabled else "🔴"
                            st.write(f"{status_badge} **{model.name}**{default_badge}")
                            st.caption(f"`{model.model}` | {model.provider}")
                        
                        with col2:
                            st.caption(model.description or "无描述")
                        
                        with col3:
                            if model.is_default:
                                st.caption("已设为默认")
                            else:
                                if st.button("⭐ 默认", key=f"default_{model.id}"):
                                    model_pool.set_default_model(model.id)
                                    st.rerun()
                        
                        with col4:
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                if st.button("✏️", key=f"edit_{model.id}", help="编辑"):
                                    st.session_state.editing_model_id = model.id
                                    st.rerun()
                            with col_b:
                                toggle_label = "禁用" if model.enabled else "启用"
                                if st.button("🔄", key=f"toggle_{model.id}", help=toggle_label):
                                    if model.enabled:
                                        model_pool.disable_model(model.id)
                                    else:
                                        model_pool.enable_model(model.id)
                                    st.rerun()
                            with col_c:
                                if st.button("🗑️", key=f"delete_{model.id}", help="删除"):
                                    model_pool.remove_model(model.id)
                                    st.rerun()
    
    # --- 添加模型 ---
    with tab2:
        st.subheader("添加新模型")
        
        with st.form("add_model_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                model_name = st.text_input("显示名称 *", placeholder="例如：GPT-4o 主力")
                model_id = st.text_input("唯一标识 *", placeholder="例如：gpt4o-main", 
                                         help="用于内部识别，建议使用英文和短横线")
                model_type = st.text_input("模型名称 *", placeholder="例如：gpt-4o 或 claude-3-opus-20240229",
                                           help="实际调用时使用的模型名")
                
            with col2:
                provider = st.selectbox(
                    "提供商",
                    options=[p.value for p in ModelProvider],
                    format_func=lambda x: {
                        "openai": "OpenAI",
                        "anthropic": "Anthropic",
                        "azure": "Azure OpenAI",
                        "deepseek": "DeepSeek",
                        "moonshot": "Moonshot (Kimi)",
                        "zhipu": "智谱 AI",
                        "ollama": "Ollama (本地)",
                        "custom": "自定义"
                    }.get(x, x)
                )
                
                group = st.selectbox(
                    "分组",
                    options=[g.value for g in ModelGroup],
                    index=5,  # 默认 other
                    format_func=lambda x: {
                        "creative": "✍️ 创意写作",
                        "analysis": "🔍 分析审计",
                        "planning": "📋 规划推理",
                        "character": "🎭 角色扮演",
                        "local": "💻 本地模型",
                        "other": "📦 其他"
                    }.get(x, x)
                )
                
                is_default = st.checkbox("设为默认模型", value=False)
                is_enabled = st.checkbox("启用模型", value=True)
            
            st.markdown("---")
            st.subheader("API 配置")
            
            col1, col2 = st.columns(2)
            with col1:
                api_key = st.text_input("API Key", type="password", placeholder="sk-...", key="add_api_key")
            with col2:
                base_url = st.text_input("API 端点（可选）", placeholder="https://api.example.com", key="add_base_url")
            
            st.markdown("---")
            st.subheader("高级设置")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                max_tokens = st.number_input("最大 Tokens", min_value=100, max_value=128000, value=4096, key="add_max_tokens")
            with col2:
                supports_stream = st.checkbox("支持流式", value=True, key="add_stream")
            with col3:
                description = st.text_input("描述", placeholder="模型用途说明", key="add_desc")
            
            submitted = st.form_submit_button("✅ 添加模型", type="primary")
            
            if submitted:
                if not model_name or not model_id or not model_type:
                    st.error("请填写必填字段（名称、标识、模型名称）")
                elif model_pool.get_model(model_id):
                    st.error(f"模型标识「{model_id}」已存在，请使用不同的标识")
                else:
                    new_model = ModelInstance(
                        id=model_id,
                        name=model_name,
                        model=model_type,
                        provider=provider,
                        api_key=api_key,
                        base_url=base_url if base_url else None,
                        group=group,
                        enabled=is_enabled,
                        is_default=is_default,
                        description=description,
                        max_tokens=max_tokens,
                        supports_stream=supports_stream
                    )
                    model_pool.add_model(new_model)
                    st.success(f"✅ 模型「{model_name}」添加成功！")
                    time.sleep(0.5)
                    st.rerun()

# ============ 模型路由 ============
elif page == "🔀 模型路由":
    st.header("🔀 模型路由配置")
    
    st.markdown("""
    为不同任务类型分配模型。如果不设置，将使用默认模型。
    """)
    
    # 获取可用模型
    available_models = model_pool.list_models(enabled_only=True)
    
    if not available_models:
        st.warning("请先在「模型池」中添加并启用模型")
    else:
        # 任务类型定义
        task_types = [
            {"id": "writer", "name": "✍️ 小说写作", "desc": "创意内容生成，需要强创作能力"},
            {"id": "auditor", "name": "🔍 审计校验", "desc": "内容审查、一致性检查"},
            {"id": "planner", "name": "📋 规划推理", "desc": "情节规划、逻辑推理"},
            {"id": "character", "name": "🎭 角色扮演", "desc": "角色对话、心理模拟"},
        ]
        
        default_model = model_pool.get_default_model()
        default_model_id = default_model.id if default_model else None
        
        model_options = {m.id: f"{m.name} ({m.model})" for m in available_models}
        model_options[""] = "-- 使用默认模型 --"
        
        st.subheader("路由配置")
        
        for task in task_types:
            current_route = model_pool.get_route(task["id"])
            current_model_id = current_route.model_id if current_route else ""
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f"**{task['name']}**")
                st.caption(task["desc"])
            
            with col2:
                keys = list(model_options.keys())
                current_index = keys.index(current_model_id) if current_model_id in keys else 0
                selected_model = st.selectbox(
                    "选择模型",
                    options=keys,
                    format_func=lambda x: model_options.get(x, ""),
                    key=f"route_{task['id']}",
                    index=current_index
                )
                
                if selected_model != current_model_id:
                    if selected_model:
                        model_pool.set_route(task["id"], selected_model, task["desc"])
                    else:
                        model_pool.remove_route(task["id"])
                    st.rerun()
        
        # 显示当前路由状态
        st.markdown("---")
        st.subheader("📋 当前路由状态")
        
        routes = model_pool.list_routes()
        if routes:
            for route in routes:
                model = model_pool.get_model(route.model_id)
                if model:
                    st.write(f"- **{route.task_type}** → `{model.name}`")
        else:
            st.info("所有任务将使用默认模型")
        
        if default_model:
            st.markdown(f"**当前默认模型：** `{default_model.name}`")

# ============ 代理状态 ============
elif page == "📊 代理状态":
    st.header("📊 LiteLLM 代理状态")
    
    # 安全说明
    st.info("""
    ℹ️ **代理自动启动**：Web UI 启动时会自动启动代理服务
    
    - API Key 存储在代理服务中，不会暴露给客户端
    - 所有 LLM 请求通过代理统一管理和审计
    """)
    
    status = check_proxy_status()
    
    # 状态和控制
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if status.is_running:
            st.success("✅ 代理服务运行中")
            st.metric("服务地址", status.url)
            if status.models:
                st.write("**可用模型：**")
                for model in status.models:
                    st.write(f"- `{model}`")
        else:
            st.error("❌ 代理服务未运行")
            st.warning("所有 LLM 调用将无法工作，请启动代理")
    
    with col2:
        st.subheader("控制")
        
        if status.is_running:
            if st.button("⏹️ 停止代理", type="secondary"):
                result = stop_proxy()
                if result["success"]:
                    st.success(result["message"])
                else:
                    st.error(result["message"])
                st.rerun()
        else:
            if st.button("▶️ 启动代理", type="primary"):
                result = start_proxy_if_not_running(check_proxy_status, model_pool=model_pool, max_wait=15)
                if result["started"] or result["already_running"]:
                    st.success(result["message"])
                else:
                    st.error(result["message"])
                st.rerun()
        
        if st.button("🔄 刷新状态"):
            st.rerun()
    
    # 导出配置
    st.markdown("---")
    st.subheader("📤 导出 LiteLLM 配置")
    st.markdown("生成配置文件用于手动启动 LiteLLM 代理服务：")
    
    if st.button("生成 litellm_config.yaml"):
        config = model_pool.export_to_litellm_config()
        import yaml
        config_yaml = yaml.dump(config, allow_unicode=True, default_flow_style=False)
        st.code(config_yaml, language="yaml")
        st.info("将以上内容保存到 litellm_config.yaml 文件中")

# ============ 连接测试 ============
elif page == "🧪 连接测试":
    st.header("🧪 模型连接测试")
    
    # 检查代理状态
    proxy_status = check_proxy_status()
    
    if not proxy_status.is_running:
        st.error("❌ 代理服务未运行，无法进行连接测试")
        st.warning("请先在「📊 代理状态」页面启动代理服务")
        st.stop()
    
    available_models = model_pool.list_models(enabled_only=True)
    
    if not available_models:
        st.warning("请先在「模型池」中添加并启用模型")
    else:
        st.success(f"✅ 代理运行中 ({proxy_status.url})")
        
        col1, col2 = st.columns(2)
        
        with col1:
            model_options = {m.id: f"{m.name} ({m.model})" for m in available_models}
            selected_model_id = st.selectbox(
                "选择模型",
                options=list(model_options.keys()),
                format_func=lambda x: model_options[x]
            )
        
        with col2:
            test_message = st.text_area(
                "测试消息",
                value="你好，这是一个测试。请简短回复。",
                height=80
            )
        
        if st.button("🚀 发送测试", type="primary"):
            model = model_pool.get_model(selected_model_id)
            
            if not model:
                st.error("模型不存在")
            else:
                with st.spinner("通过代理测试中..."):
                    # 通过代理测试连接
                    result = test_model_connection(
                        model=model.model,  # 实际模型名
                        test_message=test_message
                    )
                    
                    if result["success"]:
                        st.success("✅ 连接成功！")
                        st.caption(f"代理地址: {result.get('proxy_url', 'N/A')}")
                        st.subheader("📝 响应")
                        st.write(result["response"])
                    else:
                        st.error("❌ 连接失败")
                        st.code(result["error"], language="text")

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9em;">
    MineNovel Configuration Manager v2.1 | 可插拔模型池
</div>
""", unsafe_allow_html=True)