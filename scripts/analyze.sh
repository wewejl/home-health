#!/bin/bash
# 代码分析脚本
# 运行 flake8, mypy, bandit 进行代码检查

set -e

echo "==========================================="
echo "🔍 代码分析工具"
echo "==========================================="
echo ""

# 检查是否在 Docker 环境中
if [ -f "/.dockerenv" ]; then
    echo "⚠️  检测到 Docker 环境"
    echo "使用 docker exec 运行分析..."
    CMD_PREFIX="docker exec home-health-backend"
else
    CMD_PREFIX=""
fi

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 1. Flake8 (代码风格检查)
echo -e "${GREEN}1. Flake8 - Python 代码风格检查${NC}"
echo "--------------------------------"
if [ -n "$CMD_PREFIX" ]; then
    $CMD_PREFIX python -m flake8 app --config=.flake8 --max-line-length=100 || true
else
    flake8 app --config=.flake8 --max-line-length=100 || true
fi
echo ""

# 2. mypy (类型检查)
echo -e "${GREEN}2. mypy - Python 类型检查${NC}"
echo "--------------------------------"
if [ -n "$CMD_PREFIX" ]; then
    $CMD_PREFIX python -m mypy app --config-file pyproject.toml || true
else
    mypy app --config-file pyproject.toml || true
fi
echo ""

# 3. bandit (安全检查)
echo -e "${GREEN}3. bandit - 安全漏洞检查${NC}"
echo "--------------------------------"
if [ -n "$CMD_PREFIX" ]; then
    $CMD_PREFIX python -m bandit -r app -c pyproject.toml || true
else
    bandit -r app -c pyproject.toml || true
fi
echo ""

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}✅ 分析完成${NC}"
echo ""
echo "提示："
echo "  - Flake8: PEP8 代码风格检查"
echo "  - mypy: 静态类型检查"
echo "  - bandit: 安全漏洞扫描"
echo ""
