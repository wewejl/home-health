#!/bin/bash

# 灵犀健康官网 - 停止服务脚本

echo "停止灵犀健康官网服务..."

# 停止 Docker 容器
echo "[1/2] 停止 Docker 容器..."
docker compose down

# 停止 natapp
echo "[2/2] 停止 natapp..."
pkill -f "natapp" || echo "  natapp 未运行"

echo ""
echo "✅ 服务已停止"
