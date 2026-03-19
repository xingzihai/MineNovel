// MineNovel Web UI - Frontend Logic

const API_BASE = '';

// 编辑状态
let editingModelId = null;

// ==================== 工具函数 ====================

async function api(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
            'Content-Type': 'application/json',
        },
        ...options,
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Request failed');
    }
    return response.json();
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ==================== 页面导航 ====================

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const page = item.dataset.page;
        
        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        
        // 显示对应页面
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.getElementById(`page-${page}`).classList.add('active');
        
        // 加载页面数据
        loadPageData(page);
    });
});

function loadPageData(page) {
    switch (page) {
        case 'home':
            loadStats();
            break;
        case 'models':
            loadModels();
            break;
        case 'routes':
            loadRoutes();
            break;
        case 'proxy':
            refreshProxyStatus();
            break;
        case 'test':
            loadTestModels();
            break;
    }
}

// ==================== 首页统计 ====================

async function loadStats() {
    try {
        const data = await api('/api/models');
        document.getElementById('statTotal').textContent = data.stats.total;
        document.getElementById('statEnabled').textContent = data.stats.enabled;
        document.getElementById('statRoutes').textContent = data.stats.routes;
        
        // 代理状态
        const proxy = await api('/api/proxy/status');
        document.getElementById('statProxy').textContent = proxy.is_running ? '运行中' : '未启动';
    } catch (e) {
        console.error('Failed to load stats:', e);
    }
}

// ==================== 模型管理 ====================

async function loadModels() {
    const container = document.getElementById('modelsContainer');
    container.innerHTML = '<p class="hint">加载中...</p>';
    
    try {
        const data = await api('/api/models');
        const models = data.models;
        
        if (models.length === 0) {
            container.innerHTML = '<p class="hint">暂无模型，点击「添加模型」创建你的第一个模型</p>';
            return;
        }
        
        container.innerHTML = models.map(model => `
            <div class="model-card ${model.enabled ? '' : 'disabled'}">
                <div class="model-info">
                    <h4>
                        <span class="model-name">${escapeHtml(model.name)}</span>
                        ${model.is_default ? '<span class="model-badge">默认</span>' : ''}
                        ${model.enabled ? '' : '<span style="color: var(--accent-error)">已禁用</span>'}
                    </h4>
                    <div class="model-type">${escapeHtml(model.model)} | ${model.provider}</div>
                    ${model.base_url ? `<div class="model-url" style="font-size:12px;color:var(--text-muted)">${escapeHtml(model.base_url)}</div>` : ''}
                </div>
                <div class="model-actions">
                    <button class="btn btn-sm btn-outline" onclick="editModel('${model.id}')">✏️ 编辑</button>
                    ${!model.is_default ? `<button class="btn btn-sm btn-outline" onclick="setDefault('${model.id}')">⭐ 默认</button>` : ''}
                    <button class="btn btn-sm btn-outline" onclick="toggleModel('${model.id}')">${model.enabled ? '禁用' : '启用'}</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteModel('${model.id}')">删除</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = `<p class="hint" style="color: var(--accent-error)">加载失败: ${e.message}</p>`;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showAddModelModal() {
    editingModelId = null;
    document.getElementById('modalTitle').textContent = '添加模型';
    document.getElementById('btnSaveModel').textContent = '添加';
    document.getElementById('modelId').disabled = false;
    document.getElementById('addModelModal').classList.add('show');
    clearModelForm();
}

function hideAddModelModal() {
    document.getElementById('addModelModal').classList.remove('show');
    editingModelId = null;
    clearModelForm();
}

function clearModelForm() {
    document.getElementById('modelName').value = '';
    document.getElementById('modelId').value = '';
    document.getElementById('modelType').value = '';
    document.getElementById('modelApiKey').value = '';
    document.getElementById('modelBaseUrl').value = '';
    document.getElementById('modelDesc').value = '';
    document.getElementById('modelMaxTokens').value = '4096';
    document.getElementById('modelEnabled').checked = true;
    document.getElementById('modelDefault').checked = false;
    document.getElementById('modelProvider').value = 'custom';
    document.getElementById('modelGroup').value = 'other';
}

async function editModel(modelId) {
    try {
        const model = await api(`/api/models/${modelId}`);
        
        editingModelId = modelId;
        document.getElementById('modalTitle').textContent = '编辑模型';
        document.getElementById('btnSaveModel').textContent = '保存';
        document.getElementById('modelId').disabled = true;
        
        // 填充表单
        document.getElementById('modelName').value = model.name || '';
        document.getElementById('modelId').value = model.id || '';
        document.getElementById('modelType').value = model.model || '';
        document.getElementById('modelApiKey').value = model.api_key || '';
        document.getElementById('modelBaseUrl').value = model.base_url || '';
        document.getElementById('modelDesc').value = model.description || '';
        document.getElementById('modelMaxTokens').value = model.max_tokens || 4096;
        document.getElementById('modelEnabled').checked = model.enabled !== false;
        document.getElementById('modelDefault').checked = model.is_default === true;
        document.getElementById('modelProvider').value = model.provider || 'custom';
        document.getElementById('modelGroup').value = model.group || 'other';
        
        document.getElementById('addModelModal').classList.add('show');
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function saveModel() {
    const name = document.getElementById('modelName').value.trim();
    const id = document.getElementById('modelId').value.trim();
    const model = document.getElementById('modelType').value.trim();
    
    if (!name || !id || !model) {
        showToast('请填写必填字段', 'error');
        return;
    }
    
    const modelData = {
        id,
        name,
        model,
        provider: document.getElementById('modelProvider').value,
        api_key: document.getElementById('modelApiKey').value,
        base_url: document.getElementById('modelBaseUrl').value || null,
        group: document.getElementById('modelGroup').value,
        description: document.getElementById('modelDesc').value,
        max_tokens: parseInt(document.getElementById('modelMaxTokens').value) || 4096,
        enabled: document.getElementById('modelEnabled').checked,
        is_default: document.getElementById('modelDefault').checked,
    };
    
    try {
        if (editingModelId) {
            // 更新模型
            await api(`/api/models/${editingModelId}`, {
                method: 'PUT',
                body: JSON.stringify(modelData),
            });
            showToast('模型已更新');
        } else {
            // 添加模型
            await api('/api/models', {
                method: 'POST',
                body: JSON.stringify(modelData),
            });
            showToast('模型添加成功');
        }
        
        hideAddModelModal();
        loadModels();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function setDefault(modelId) {
    try {
        await api(`/api/models/${modelId}/default`, { method: 'POST' });
        showToast('已设为默认模型');
        loadModels();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function toggleModel(modelId) {
    try {
        await api(`/api/models/${modelId}/toggle`, { method: 'POST' });
        showToast('状态已更新');
        loadModels();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function deleteModel(modelId) {
    if (!confirm(`确定要删除模型 "${modelId}" 吗？`)) return;
    
    try {
        await api(`/api/models/${modelId}`, { method: 'DELETE' });
        showToast('模型已删除');
        loadModels();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// ==================== 路由管理 ====================

const TASK_TYPES = [
    { id: 'writer', name: '✍️ 小说写作', desc: '创意内容生成，需要强创作能力' },
    { id: 'auditor', name: '🔍 审计校验', desc: '内容审查、一致性检查' },
    { id: 'planner', name: '📋 规划推理', desc: '情节规划、逻辑推理' },
    { id: 'character', name: '🎭 角色扮演', desc: '角色对话、心理模拟' },
];

async function loadRoutes() {
    const container = document.getElementById('routesList');
    container.innerHTML = '<p class="hint">加载中...</p>';
    
    try {
        const [modelsData, routesData] = await Promise.all([
            api('/api/models'),
            api('/api/routes'),
        ]);
        
        const models = modelsData.models.filter(m => m.enabled);
        const routes = routesData.routes;
        const routeMap = {};
        routes.forEach(r => routeMap[r.task_type] = r.model_id);
        
        container.innerHTML = TASK_TYPES.map(task => {
            const currentModelId = routeMap[task.id] || '';
            return `
                <div class="route-item">
                    <div class="route-task">
                        <div class="route-task-name">${task.name}</div>
                        <div class="route-task-desc">${task.desc}</div>
                    </div>
                    <div class="route-model">
                        <select class="form-control" onchange="setRoute('${task.id}', this.value)">
                            <option value="">-- 使用默认模型 --</option>
                            ${models.map(m => `
                                <option value="${m.id}" ${currentModelId === m.id ? 'selected' : ''}>
                                    ${escapeHtml(m.name)}
                                </option>
                            `).join('')}
                        </select>
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        container.innerHTML = `<p class="hint" style="color: var(--accent-error)">加载失败: ${e.message}</p>`;
    }
}

async function setRoute(taskType, modelId) {
    try {
        if (modelId) {
            await api('/api/routes', {
                method: 'POST',
                body: JSON.stringify({ task_type: taskType, model_id: modelId }),
            });
            showToast('路由已更新');
        } else {
            await api(`/api/routes/${taskType}`, { method: 'DELETE' });
            showToast('已移除路由');
        }
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// ==================== 代理管理 ====================

async function refreshProxyStatus() {
    const indicator = document.getElementById('proxyIndicator');
    const dot = indicator.querySelector('.indicator-dot');
    const text = indicator.querySelector('.indicator-text');
    
    const statusCard = document.getElementById('proxyStatusCard');
    const stateIcon = statusCard.querySelector('.state-icon');
    const stateText = statusCard.querySelector('.state-text');
    const urlEl = document.getElementById('proxyUrl');
    const modelsEl = document.getElementById('proxyModels');
    
    const btnStart = document.getElementById('btnStartProxy');
    const btnStop = document.getElementById('btnStopProxy');
    
    try {
        const status = await api('/api/proxy/status');
        
        if (status.is_running) {
            dot.className = 'indicator-dot running';
            text.textContent = '代理运行中';
            
            stateIcon.textContent = '🟢';
            stateText.textContent = '代理运行中';
            stateText.className = 'state-text running';
            urlEl.textContent = status.url;
            
            btnStart.style.display = 'none';
            btnStop.style.display = 'inline-flex';
            
            if (status.models && status.models.length > 0) {
                modelsEl.innerHTML = status.models.map(m => 
                    `<span class="proxy-model-tag">${escapeHtml(m)}</span>`
                ).join('');
            } else {
                modelsEl.innerHTML = '<p class="hint">暂无注册模型</p>';
            }
        } else {
            dot.className = 'indicator-dot stopped';
            text.textContent = '代理未运行';
            
            stateIcon.textContent = '🔴';
            stateText.textContent = '代理未运行';
            stateText.className = 'state-text stopped';
            urlEl.textContent = status.error || '未启动';
            
            btnStart.style.display = 'inline-flex';
            btnStop.style.display = 'none';
            
            modelsEl.innerHTML = '<p class="hint">代理未运行</p>';
        }
    } catch (e) {
        dot.className = 'indicator-dot stopped';
        text.textContent = '检查失败';
        stateText.textContent = '检查失败';
        stateText.className = 'state-text stopped';
    }
}

async function startProxy() {
    const btn = document.getElementById('btnStartProxy');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> 启动中...';
    
    try {
        const result = await api('/api/proxy/start', { method: 'POST' });
        if (result.started || result.already_running) {
            showToast(result.message);
            await refreshProxyStatus();
        } else {
            showToast(result.message, 'error');
        }
    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '▶️ 启动代理';
    }
}

async function stopProxy() {
    const btn = document.getElementById('btnStopProxy');
    btn.disabled = true;
    
    try {
        const result = await api('/api/proxy/stop', { method: 'POST' });
        showToast(result.message);
        await refreshProxyStatus();
    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        btn.disabled = false;
    }
}

// ==================== 连接测试 ====================

async function loadTestModels() {
    const select = document.getElementById('testModelSelect');
    select.innerHTML = '<option value="">加载中...</option>';
    
    try {
        const data = await api('/api/models');
        const models = data.models.filter(m => m.enabled);
        
        if (models.length === 0) {
            select.innerHTML = '<option value="">暂无可用模型</option>';
            return;
        }
        
        select.innerHTML = models.map(m => 
            `<option value="${m.id}">${escapeHtml(m.name)} (${m.model})</option>`
        ).join('');
    } catch (e) {
        select.innerHTML = '<option value="">加载失败</option>';
    }
}

async function runTest() {
    const modelId = document.getElementById('testModelSelect').value;
    const message = document.getElementById('testMessage').value;
    const btn = document.getElementById('btnTest');
    const resultDiv = document.getElementById('testResult');
    const resultContent = document.getElementById('testResultContent');
    
    if (!modelId) {
        showToast('请选择模型', 'error');
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> 测试中...';
    resultDiv.style.display = 'block';
    resultContent.innerHTML = '<p class="hint">测试中...</p>';
    
    try {
        const result = await api('/api/test', {
            method: 'POST',
            body: JSON.stringify({ model_id: modelId, message }),
        });
        
        if (result.success) {
            resultContent.innerHTML = `
                <div style="color: var(--accent-success); margin-bottom: 12px;">✅ 连接成功</div>
                <div style="background: var(--bg-tertiary); padding: 12px; border-radius: 8px;">
                    ${escapeHtml(result.response)}
                </div>
            `;
        } else {
            resultContent.innerHTML = `
                <div style="color: var(--accent-error); margin-bottom: 12px;">❌ 连接失败</div>
                <div style="background: var(--bg-tertiary); padding: 12px; border-radius: 8px; color: var(--accent-error);">
                    ${escapeHtml(result.error)}
                </div>
            `;
        }
    } catch (e) {
        resultContent.innerHTML = `
            <div style="color: var(--accent-error);">❌ 请求失败: ${escapeHtml(e.message)}</div>
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 发送测试';
    }
}

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    refreshProxyStatus();
    
    // 定期刷新代理状态
    setInterval(refreshProxyStatus, 30000);
});