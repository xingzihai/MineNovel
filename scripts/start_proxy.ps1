# 启动 LiteLLM 代理

Write-Host "Starting LiteLLM proxy..."

# 检查 .env 文件
if (-not (Test-Path .env)) {
    Write-Host "Error: .env file not found"
    Write-Host "Please copy .env.example to .env and fill in your API keys"
    exit 1
}

# 加载环境变量
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}

# 启动代理
litellm --config litellm_config.yaml --port 4000