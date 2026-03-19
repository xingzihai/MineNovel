#!/bin/bash
# 启动 MineNovel 配置管理 Web UI

echo "Starting MineNovel Web UI..."

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 检查依赖
python -c "import streamlit" 2>/dev/null || pip install streamlit pyyaml requests --quiet

# 启动 Web UI
echo "Launching Web UI at http://localhost:8501"
streamlit run src/web/app.py --server.port 8501