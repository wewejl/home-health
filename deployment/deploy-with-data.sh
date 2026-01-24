#!/bin/bash
# 灵犀医生 - 完整部署脚本（包含数据迁移）
# 用法: bash deployment/deploy-with-data.sh

set -e

# ============================================
# 配置区域
# ============================================
DEPLOY_HOST="${DEPLOY_HOST:-123.206.232.231}"
DEPLOY_USER="${DEPLOY_USER:-ubuntu}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/home-health}"
SSH_KEY="${SSH_KEY:-./xinlingyisheng.pem}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# 数据库配置
PG_DB="${PG_DB:-xinlin_prod}"
PG_USER="${PG_USER:-xinlin_prod}"
PG_CONTAINER="${PG_CONTAINER:-home-health-postgres}"

# ============================================
# 颜色输出
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}==>${NC} $1"; }

# ============================================
# 前置检查
# ============================================
if [ ! -f "$SSH_KEY" ]; then
    log_error "SSH 密钥文件不存在: $SSH_KEY"
    log_info "请设置 SSH_KEY 环境变量，或确保密钥文件在当前目录"
    exit 1
fi

chmod 400 "$SSH_KEY"

SSH="ssh -i $SSH_KEY -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST"
SCP="scp -i $SSH_KEY -o StrictHostKeyChecking=no"

# ============================================
# 步骤 1: 导出本地数据
# ============================================
log_step "步骤 1/6: 导出本地 SQLite 数据"

if [ ! -f "backend/app.db" ]; then
    log_warn "本地数据库不存在，跳过数据迁移"
    SKIP_MIGRATE=true
else
    log_info "运行数据导出脚本..."
    python3 deployment/migrate-export.py

    if [ -f "deployment/migrate-data/dump.sql" ]; then
        SKIP_MIGRATE=false
        log_info "数据导出成功: deployment/migrate-data/dump.sql"
    else
        log_error "数据导出失败"
        exit 1
    fi
fi

# ============================================
# 步骤 2: 检查服务器连接
# ============================================
log_step "步骤 2/6: 检查服务器连接"

if $SSH "echo '连接成功'" > /dev/null 2>&1; then
    log_info "✓ 服务器连接正常"
else
    log_error "无法连接到服务器"
    exit 1
fi

# ============================================
# 步骤 3: 上传代码和配置
# ============================================
log_step "步骤 3/6: 上传代码到服务器"

log_info "上传 docker-compose.yml..."
$SCP docker-compose.yml $DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/docker-compose.yml

log_info "上传环境配置..."
$SCP .env.production $DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/.env.production

log_info "上传后端代码..."
$SSH "mkdir -p $DEPLOY_PATH/source" || true
rsync -avz -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='venv' \
  backend/ ${DEPLOY_USER}@${DEPLOY_HOST}:$DEPLOY_PATH/source/backend/

# ============================================
# 步骤 4: 上传并迁移数据
# ============================================
if [ "$SKIP_MIGRATE" = true ]; then
    log_step "步骤 4/6: 跳过数据迁移"
else
    log_step "步骤 4/6: 迁移数据库数据"

    log_info "上传数据转储文件..."
    $SSH "mkdir -p $DEPLOY_PATH/migrate-data"
    $SCP deployment/migrate-data/dump.sql $DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/migrate-data/dump.sql

    log_info "在服务器上导入数据..."

    $SSH "bash -s" << EOF
set -e

echo "停止后端服务..."
cd $DEPLOY_PATH
docker compose stop backend 2>/dev/null || true
docker compose rm -f backend 2>/dev/null || true

echo "等待 PostgreSQL 准备就绪..."
until docker exec $PG_CONTAINER pg_isready -U $PG_USER > /dev/null 2>&1; do
    echo "  等待 PostgreSQL 启动..."
    sleep 2
done

echo "备份数据库..."
docker exec $PG_CONTAINER pg_dump -U $PG_USER $PG_DB > /tmp/backup_\$(date +%Y%m%d_%H%M%S).sql 2>/dev/null || true

echo "导入数据..."
docker exec -i $PG_CONTAINER psql -U $PG_USER -d $PG_DB < $DEPLOY_PATH/migrate-data/dump.sql

echo "✓ 数据导入完成"
echo ""
EOF
fi

# ============================================
# 步骤 5: 构建和启动服务
# ============================================
log_step "步骤 5/6: 构建和启动服务"

$SSH "bash -s" << EOF
set -e

cd $DEPLOY_PATH

echo "停止现有服务..."
docker compose down 2>/dev/null || true

echo "构建镜像..."
docker build -t home-health-backend:latest -f source/backend/Dockerfile source/backend/

echo "启动服务..."
docker compose up -d

echo "等待服务启动..."
sleep 10

echo ""
echo "=== 服务状态 ==="
docker compose ps
EOF

# ============================================
# 步骤 6: 健康检查
# ============================================
log_step "步骤 6/6: 健康检查"

sleep 5

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

if [[ "$FRONTEND_STATUS" == "200" || "$FRONTEND_STATUS" == "000" ]]; then
    # 000 可能是前端还在启动
    log_info "✓ 前端服务启动中或已就绪"
fi

# ============================================
# 完成
# ============================================
echo ""
log_info "=== 部署完成 ==="
echo ""
echo "访问地址:"
echo "  前端: http://$DEPLOY_HOST/"
echo "  后端: http://$DEPLOY_HOST:8100/"
echo "  API文档: http://$DEPLOY_HOST:8100/docs"
echo ""
echo "查看日志:"
echo "  docker exec -f home-health-backend tail -f /app/logs/app.log"
