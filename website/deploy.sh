#!/bin/bash

# 灵犀健康官网部署脚本
# 用于在服务器上部署网站并启动 natapp 内网穿透

set -e

echo "========================================="
echo "  灵犀健康官网 - 服务器部署脚本"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 停止旧容器
echo -e "${YELLOW}[1/4] 停止旧容器...${NC}"
docker compose down 2>/dev/null || true
pkill -f "natapp" 2>/dev/null || true
sleep 2

# 2. 构建并启动 Docker 容器
echo -e "${YELLOW}[2/4] 构建 Docker 镜像...${NC}"
docker compose build

echo -e "${YELLOW}[3/4] 启动容器 (端口 3344)...${NC}"
docker compose up -d

# 3. 验证容器状态
echo -e "${YELLOW}[4/4] 验证服务状态...${NC}"
sleep 3

if docker ps | grep -q "lingxi-health-website"; then
    echo -e "${GREEN}✅ Docker 容器启动成功${NC}"
    echo "   本地访问: http://localhost:3344"
else
    echo -e "${YELLOW}⚠️  容器状态异常，请检查${NC}"
    docker logs lingxi-health-website
    exit 1
fi

# 4. 启动 natapp 内网穿透
echo ""
echo -e "${YELLOW}[5/5] 启动 natapp 内网穿透...${NC}"

# 检查 natapp 是否存在
if [ ! -f "./natapp" ]; then
    echo "⚠️  natapp 不存在，请先下载 natapp"
    echo "   下载地址: https://natapp.cn/"
    echo ""
    echo "   下载后放在当前目录，然后运行此脚本"
    exit 1
fi

# 给 natapp 添加执行权限
chmod +x ./natapp

# 后台启动 natapp
nohup ./natapp --authtoken=e8fdfa13885d4594 > natapp.log 2>&1 &
NATAPP_PID=$!

sleep 3

# 检查 natapp 是否启动成功
if ps -p $NATAPP_PID > /dev/null; then
    echo -e "${GREEN}✅ natapp 启动成功 (PID: $NATAPP_PID)${NC}"
    echo ""
    echo "========================================="
    echo -e "${GREEN}  部署完成！${NC}"
    echo "========================================="
    echo ""
    echo "  本地访问:  http://localhost:3344"
    echo "  外网访问:  http://xinling.natapp1.cc"
    echo ""
    echo "  查看日志:"
    echo "    Docker: docker logs -f lingxi-health-website"
    echo "    Natapp: tail -f natapp.log"
    echo ""
    echo "  停止服务:"
    echo "    docker compose down"
    echo "    pkill -f natapp"
    echo ""
else
    echo -e "${YELLOW}⚠️  natapp 启动可能有问题，请检查日志${NC}"
    tail -20 natapp.log
fi
