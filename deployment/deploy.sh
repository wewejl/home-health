#!/bin/bash
# Home-Health 手动部署脚本
# 用法: ./deploy.sh [environment]
# environment: dev (default) | prod

set -e

# 配置
DEPLOY_HOST="${DEPLOY_HOST:-123.206.232.231}"
DEPLOY_USER="${DEPLOY_USER:-root}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/home-health}"
SSH_KEY="${SSH_KEY:-./xinlingyisheng.pem}"
GITHUB_USERNAME="${GITHUB_USERNAME:-wewejl}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 SSH 密钥
if [ ! -f "$SSH_KEY" ]; then
    log_error "SSH 密钥文件不存在: $SSH_KEY"
    exit 1
fi

chmod 400 "$SSH_KEY"

# SSH 命令封装
SSH="ssh -i $SSH_KEY -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST"

log_info "=== 开始部署 Home-Health ==="
log_info "服务器: $DEPLOY_HOST"
log_info "镜像标签: $IMAGE_TAG"
log_info ""

# 1. 检查服务器连接
log_info "检查服务器连接..."
if $SSH "echo '连接成功'" > /dev/null 2>&1; then
    log_info "✓ 服务器连接正常"
else
    log_error "无法连接到服务器"
    exit 1
fi

# 2. 部署
log_info "部署到服务器..."
$SSH "bash -s" << EOF
set -e

# 创建部署目录
sudo mkdir -p $DEPLOY_PATH
sudo chown -R \$USER:\$USER $DEPLOY_PATH

cd $DEPLOY_PATH

# 拉取或更新 docker-compose.yml
if [ -f docker-compose.yml ]; then
    echo "备份现有配置..."
    cp docker-compose.yml docker-compose.yml.bak
fi

# 更新镜像标签
sed -i "s/IMAGE_TAG=.*/IMAGE_TAG=$IMAGE_TAG/" .env 2>/dev/null || true

# 拉取最新镜像
echo "拉取最新镜像..."
export IMAGE_TAG=$IMAGE_TAG
export GITHUB_USERNAME=$GITHUB_USERNAME
docker compose pull 2>/dev/null || docker-compose pull 2>/dev/null

# 重启服务
echo "重启服务..."
docker compose up -d 2>/dev/null || docker-compose up -d

# 清理旧镜像
echo "清理旧镜像..."
docker image prune -f

echo ""
echo "=== 部署完成 ==="
docker ps --filter "name=home-health" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
EOF

# 3. 健康检查
log_info "等待服务启动..."
sleep 15

log_info "检查服务状态..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DEPLOY_HOST:8100/health 2>/dev/null || echo "000")
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DEPLOY_HOST/ 2>/dev/null || echo "000")

echo ""
log_info "服务状态:"
echo "  后端 (8100): $BACKEND_STATUS"
echo "  前端 (80):   $FRONTEND_STATUS"

if [[ "$BACKEND_STATUS" == "200" ]]; then
    log_info "✓ 后端服务健康"
else
    log_warn "⚠ 后端服务可能需要检查"
fi

if [[ "$FRONTEND_STATUS" == "200" ]]; then
    log_info "✓ 前端服务健康"
else
    log_warn "⚠ 前端服务可能需要检查"
fi

echo ""
log_info "=== 部署完成 ==="
log_info "访问地址: http://$DEPLOY_HOST/"
