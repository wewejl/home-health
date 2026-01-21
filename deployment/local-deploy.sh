#!/bin/bash
# 本地构建并部署到服务器（无需外部镜像仓库）

set -e

DEPLOY_HOST="${DEPLOY_HOST:-123.206.232.231}"
DEPLOY_USER="${DEPLOY_USER:-root}"
SSH_KEY="${SSH_KEY:-./xinlingyisheng.pem}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

log_info "=== 开始本地构建部署 ==="

# 1. 本地构建镜像
log_info "步骤 1: 本地构建 Docker 镜像..."
cd "$(dirname "$0")/.."

log_info "构建 backend 镜像..."
docker build -t home-health-backend:latest ./backend

log_info "构建 frontend 镜像..."
docker build -t home-health-frontend:latest ./frontend

# 2. 导出镜像
log_info "步骤 2: 导出镜像为 tar 包..."
docker save home-health-backend:latest home-health-frontend:latest -o /tmp/home-health-images.tar

# 3. 上传到服务器
log_info "步骤 3: 上传镜像到服务器..."
scp -i "$SSH_KEY" /tmp/home-health-images.tar ${DEPLOY_USER}@${DEPLOY_HOST}:/tmp/

# 4. 服务器加载镜像并启动
log_info "步骤 4: 服务器加载镜像并启动..."
ssh -i "$SSH_KEY" ${DEPLOY_USER}@${DEPLOY_HOST} 'bash -s' << 'EOF'
set -e

# 加载镜像
echo "加载镜像..."
docker load -i /tmp/home-health-images.tar

# 给镜像打标签
docker tag home-health-backend:latest home-health-backend:latest
docker tag home-health-frontend:latest home-health-frontend:latest

# 启动服务
cd /opt/home-health
docker compose up -d

# 清理
rm -f /tmp/home-health-images.tar

echo ""
echo "=== 服务状态 ==="
docker compose ps
EOF

# 5. 清理本地文件
rm -f /tmp/home-health-images.tar

log_info "=== 部署完成 ==="
log_info "访问地址: http://${DEPLOY_HOST}/"
