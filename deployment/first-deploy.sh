#!/bin/bash
# 首次部署 - 从本地上传代码到服务器
# 用法: bash deployment/first-deploy.sh

DEPLOY_HOST="${DEPLOY_HOST:-123.206.232.231}"
DEPLOY_USER="${DEPLOY_USER:-root}"
SSH_KEY="${SSH_KEY:-./xinlingyisheng.pem}"

GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }

log_info "=== 首次部署：上传代码到服务器 ==="

# 1. 上传代码
log_info "步骤 1: 上传代码..."
rsync -avz -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='data/uploads' \
  --exclude='ios' \
  backend/ frontend/ deployment/ ${DEPLOY_USER}@${DEPLOY_HOST}:/opt/home-health/source/

# 2. 构建 Docker 镜像
log_info "步骤 2: 构建 Docker 镜像..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_HOST} 'bash -s' << 'EOS'
  cd /opt/home-health
  docker build -t home-health-backend:latest -f source/backend/Dockerfile source/backend/ 2>&1 | tail -20
  docker build -t home-health-frontend:latest -f source/frontend/Dockerfile source/frontend/ 2>&1 | tail -20
EOS

# 3. 配置并启动服务
log_info "步骤 3: 配置并启动服务..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_HOST} 'bash -s' << 'EOS'
  cd /opt/home-health
  
  # 更新 docker-compose.yml
  sed -i 's|wewejl/home-health-backend:latest|home-health-backend:latest|g' docker-compose.yml
  sed -i 's|wewejl/home-health-frontend:latest|home-health-frontend:latest|g' docker-compose.yml
  
  # 启动服务
  docker compose up -d
  
  echo ""
  echo "=== 服务状态 ==="
  docker compose ps
EOS

log_info "=== 首次部署完成 ==="
log_info "访问地址: http://${DEPLOY_HOST}/"
