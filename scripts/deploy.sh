#!/bin/bash
# ============================================
# 鑫琳医生 (Home-Health) 生产环境部署脚本
# ============================================
#
# 使用方法:
#   ./scripts/deploy.sh [环境]
#
# 示例:
#   ./scripts/deploy.sh production  # 部署到生产环境
#   ./scripts/deploy.sh staging      # 部署到测试环境

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认环境
ENVIRONMENT=${1:-production}

# 服务器配置
SERVER_IP="123.206.232.231"
SERVER_USER="ubuntu"
KEY_FILE="$(dirname "$0")/../xinlingyisheng.pem"
REMOTE_DIR="/opt/home-health"
SOURCE_DIR="$REMOTE_DIR/source"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查密钥文件
check_key_file() {
    if [ ! -f "$KEY_FILE" ]; then
        log_error "密钥文件不存在: $KEY_FILE"
        exit 1
    fi
    chmod 400 "$KEY_FILE"
}

# SSH 命令封装
ssh_exec() {
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$1"
}

# SCP 文件上传
scp_upload() {
    scp -i "$KEY_FILE" -o StrictHostKeyChecking=no "$1" "$SERVER_USER@$SERVER_IP:$2"
}

# 部署前检查
pre_deploy_check() {
    log_info "执行部署前检查..."

    # 检查本地代码是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        log_warn "本地有未提交的更改，建议先提交"
        read -p "是否继续部署? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "部署已取消"
            exit 1
        fi
    fi

    # 检查生产环境配置文件
    if [ "$ENVIRONMENT" = "production" ] && [ ! -f "backend/.env.production" ]; then
        log_error "生产环境配置文件不存在: backend/.env.production"
        log_error "请先创建配置文件（参考 backend/.env.example）"
        exit 1
    fi

    log_info "部署前检查完成"
}

# 上传代码
upload_code() {
    log_info "上传代码到服务器..."

    # 在服务器上拉取代码
    ssh_exec "cd $SOURCE_DIR && git fetch origin && git checkout main && git pull origin main"

    log_info "代码上传完成"
}

# 备份数据库
backup_database() {
    log_info "备份数据库..."

    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S).sql"
    ssh_exec "cd $REMOTE_DIR && sudo docker exec home-health-postgres pg_dump -U xinlin_prod home_health > backups/$BACKUP_NAME"

    log_info "数据库备份完成: $BACKUP_NAME"
}

# 部署应用
deploy_app() {
    log_info "部署应用..."

    # 根据环境选择配置文件
    if [ "$ENVIRONMENT" = "production" ]; then
        CONFIG_FILE=".env.production"
        CORS_ORIGINS="http://123.206.232.231"
        DEBUG="false"
        TEST_MODE="false"
    else
        CONFIG_FILE=".env"
        CORS_ORIGINS="*"
        DEBUG="true"
        TEST_MODE="true"
    fi

    # 上传环境配置（如果存在）
    if [ -f "backend/$CONFIG_FILE" ]; then
        log_info "上传环境配置: $CONFIG_FILE"
        scp_upload "backend/$CONFIG_FILE" "$SOURCE_DIR/backend/.env"
    fi

    # 停止现有容器
    ssh_exec "cd $REMOTE_DIR && sudo docker-compose down"

    # 重建并启动容器
    ssh_exec "cd $REMOTE_DIR && sudo docker-compose build --no-cache"
    ssh_exec "cd $REMOTE_DIR && sudo docker-compose up -d"

    log_info "应用部署完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    sleep 10  # 等待服务启动

    # 检查后端健康状态
    HEALTH_URL="http://$SERVER_IP/api/health"
    MAX_RETRIES=30
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f -s "$HEALTH_URL" > /dev/null 2>&1; then
            log_info "后端服务健康检查通过"

            # 检查详细健康状态
            DETAILED_HEALTH=$(curl -s "$HEALTH_URL/detailed")
            log_info "详细健康状态: $DETAILED_HEALTH"

            return 0
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -n "."
        sleep 2
    done

    log_error "健康检查失败，服务未能在预期时间内启动"
    return 1
}

# 查看日志
view_logs() {
    log_info "查看服务日志（Ctrl+C 退出）..."
    ssh_exec "cd $REMOTE_DIR && sudo docker-compose logs -f --tail=50"
}

# 主流程
main() {
    log_info "开始部署到环境: $ENVIRONMENT"
    log_info "目标服务器: $SERVER_IP"

    check_key_file
    pre_deploy_check
    backup_database
    upload_code
    deploy_app

    if health_check; then
        log_info "============================================"
        log_info "部署成功！"
        log_info "============================================"
        log_info "前端地址: http://$SERVER_IP/"
        log_info "后端API: http://$SERVER_IP/api/"
        log_info "健康检查: http://$SERVER_IP/api/health"
        log_info "详细监控: http://$SERVER_IP/api/health/detailed"
        log_info "============================================"

        read -p "是否查看日志? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            view_logs
        fi
    else
        log_error "部署失败，请检查日志"
        ssh_exec "cd $REMOTE_DIR && sudo docker-compose logs --tail=100"
        exit 1
    fi
}

# 执行主流程
main
