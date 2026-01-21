#!/bin/bash
# 在服务器上直接构建并部署（无需外部镜像仓库）

DEPLOY_HOST="${DEPLOY_HOST:-123.206.232.231}"
DEPLOY_USER="${DEPLOY_USER:-root}"
SSH_KEY="${SSH_KEY:-./xinlingyisheng.pem}"

GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }

log_info "=== 开始服务器端构建部署 ==="

# 1. 上传代码到服务器
log_info "步骤 1: 上传代码到服务器..."
rsync -avz -e "ssh -i $SSH_KEY" \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='data/uploads' \
  --exclude='ios' \
  backend/ frontend/ ${DEPLOY_USER}@${DEPLOY_HOST}:/opt/home-health/source/

# 2. 在服务器上构建镜像
log_info "步骤 2: 在服务器上构建镜像..."
ssh -i "$SSH_KEY" ${DEPLOY_USER}@${DEPLOY_HOST} 'bash -s' << 'EOF'
set -e
cd /opt/home-health

echo "构建 backend 镜像..."
docker build -t home-health-backend:latest -f source/backend/Dockerfile source/backend/

echo "构建 frontend 镜像..."
docker build -t home-health-frontend:latest -f source/frontend/Dockerfile source/frontend/

echo "镜像构建完成"
docker images | grep home-health
EOF

# 3. 启动服务
log_info "步骤 3: 启动服务..."
ssh -i "$SSH_KEY" ${DEPLOY_USER}@${DEPLOY_HOST} 'bash -s' << 'EOF'
set -e
cd /opt/home-health

# 确保使用本地镜像
sed -i 's|wewejl/home-health-backend:latest|home-health-backend:latest|g' docker-compose.yml
sed -i 's|wewejl/home-health-frontend:latest|home-health-frontend:latest|g' docker-compose.yml

# 启动服务
docker compose up -d

echo ""
echo "=== 服务状态 ==="
docker compose ps
EOF

log_info "=== 部署完成 ==="
log_info "访问地址: http://${DEPLOY_HOST}/"
