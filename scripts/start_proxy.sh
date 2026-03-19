#!/bin/bash
# 启动 LiteLLM 代理

echo "Starting LiteLLM proxy..."

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and fill in your API keys"
    exit 1
fi

# 加载环境变量
export $(cat .env | grep -v '^#' | xargs)

# 启动代理
litellm --config litellm_config.yaml --port 4000