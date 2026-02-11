#!/bin/bash
# 数据库备份脚本
# 用法: ./scripts/backup/backup-db.sh

set -e

# 配置
BACKUP_DIR="./backups/postgres"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="backup_${TIMESTAMP}.sql"
CONTAINER_NAME="home_health_db"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建备份目录
mkdir -p "$BACKUP_DIR"

log_info "开始备份数据库..."

# 检查容器是否运行
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    log_error "容器 $CONTAINER_NAME 未运行"
    exit 1
fi

# 执行备份
log_info "备份到: $BACKUP_DIR/$BACKUP_FILE"

docker exec "$CONTAINER_NAME" pg_dump -U postgres -d home_health > "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    log_info "备份成功！"

    # 压缩备份文件
    gzip "$BACKUP_DIR/$BACKUP_FILE"
    log_info "已压缩: ${BACKUP_FILE}.gz"

    # 显示文件大小
    SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}.gz" | cut -f1)
    log_info "备份文件大小: $SIZE"

    # 清理 30 天前的备份
    log_info "清理 30 天前的备份..."
    find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +30 -delete

    # 列出最近 5 个备份
    log_info "最近 5 个备份:"
    ls -lt "$BACKUP_DIR" | head -6 | tail -5
else
    log_error "备份失败！"
    exit 1
fi
