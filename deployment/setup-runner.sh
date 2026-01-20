#!/bin/bash
# 在国内服务器上安装 GitHub Actions 自托管 Runner
#
# 使用方法：
# 1. 复制此脚本到服务器
# 2. 执行: bash setup-runner.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO="wewejl/home-health"
RUNNER_TOKEN="AKKKBAGYGCRGLQ3SWK6X57LJN6VS4"  # 有效期 1 小时
RUNNER_NAME="home-health-$(hostname)"

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

log_info "=== 安装 GitHub Actions 自托管 Runner ==="
log_info "Runner 名称: $RUNNER_NAME"

# 1. 安装依赖
log_info "步骤 1: 安装依赖..."
yum install -y curl jq git docker || apt-get update && apt-get install -y curl jq git docker.io

# 2. 创建工作目录
log_info "步骤 2: 创建 Runner 工作目录..."
mkdir -p /opt/actions-runner
cd /opt/actions-runner

# 3. 下载 Runner
log_info "步骤 3: 下载 Runner..."
if [ ! -d "actions-runner" ]; then
  curl -o actions-runner-linux-x64-2.321.0.tar.gz -L \
    https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-linux-x64-2.321.0.tar.gz

  tar xzf ./actions-runner-linux-x64-2.321.0.tar.gz
  rm actions-runner-linux-x64-2.321.0.tar.gz
fi

# 4. 配置 Runner
log_info "步骤 4: 配置 Runner..."
cd /opt/actions-runner/actions-runner || cd /opt/actions-runner

./config.sh \
  --url "https://github.com/$REPO" \
  --token "$RUNNER_TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "self-hosted,china,production" \
  --work "/opt/actions-runner/_work" \
  --replace \
  --unattended

# 5. 安装服务
log_info "步骤 5: 安装 systemd 服务..."
./svc.sh install

# 6. 启动服务
log_info "步骤 6: 启动 Runner 服务..."
./svc.sh start

# 7. 设置开机自启
systemctl enable actions.runner.* --now

log_info "=== Runner 安装完成 ==="
log_warn "请在 GitHub 验证 Runner 状态: https://github.com/$REPO/settings/actions"

# 显示状态
sleep 2
systemctl status "actions.runner.$(echo $REPO | tr '/' '.').$RUNNER_NAME" --no-pager || true
