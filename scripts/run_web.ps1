# 启动 MineNovel Web UI (FastAPI)

Write-Host "Starting MineNovel Web UI..." -ForegroundColor Green

# 切换到项目根目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

# 检查依赖
python -c "import fastapi" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install fastapi uvicorn pyyaml boto3 --quiet
}

# 启动 Web UI
Write-Host "Launching Web UI at http://localhost:8501" -ForegroundColor Cyan
python -m uvicorn src.web.api:app --host 127.0.0.1 --port 8501