#!/bin/bash
# FastAPI 启动脚本

cd "$(dirname "$0")"

echo "🚀 启动 HIS 门诊 AI 助手 API..."
echo ""

PYTHONPATH=. ./venv/bin/python -m uvicorn src.api.app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
