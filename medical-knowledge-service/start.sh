#!/bin/bash
# 独立医学知识库服务 - 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================"
echo "  医学知识库服务 - 本地启动"
echo "================================================"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

# 检查 docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "错误: docker-compose 未安装"
    exit 1
fi

# 启动服务
echo ""
echo "启动 Docker 服务..."
docker-compose up -d

echo ""
echo "等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "检查服务状态..."
docker-compose ps

# 显示日志
echo ""
echo "================================================"
echo "  服务已启动"
echo "================================================"
echo ""
echo "API 地址: http://localhost:8200"
echo "数据库:   localhost:5433"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo ""
echo "测试命令:"
echo "  curl http://localhost:8200/health"
echo "  curl -X POST http://localhost:8200/api/v1/search \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"query\": \"湿疹\", \"specialty\": \"dermatology\"}'"
echo ""
