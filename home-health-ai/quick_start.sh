#!/bin/bash
# HIS 门诊智能助手系统 - 快速启动脚本

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     🏥 HIS 门诊智能助手系统 - 快速启动                      ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  本脚本将：                                               ║"
echo "║  1. 检查 Python 版本                                       ║"
echo "║  2. 安装依赖包                                             ║"
echo "║  3. 初始化数据库                                           ║"
echo "║  4. 启动应用程序                                           ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检查 Python 版本
echo "📋 检查 Python 版本..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python 版本: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.10" ]]; then
    echo "❌ Python 版本过低，需要 3.10 或更高版本"
    exit 1
fi

echo "✅ Python 版本检查通过"
echo ""

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  建议在虚拟环境中运行"
    echo "   创建虚拟环境: python3 -m venv venv"
    echo "   激活虚拟环境: source venv/bin/activate"
    echo ""
    read -p "是否继续？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 安装依赖
echo "📦 安装依赖包..."
pip install -q -r requirements.txt
echo "✅ 依赖包安装完成"
echo ""

# 初始化数据库
echo "🗄️  初始化数据库..."

# 检查 PostgreSQL 是否运行
if ! command -v psql &> /dev/null; then
    echo "❌ 未找到 PostgreSQL，请先安装"
    exit 1
fi

# 创建数据库
echo "   创建数据库 his_outpatient..."
createdb his_outpatient 2>/dev/null || echo "   数据库已存在"

# 执行初始化脚本
echo "   执行数据库初始化脚本..."
psql -d his_outpatient -q -f db/schema.sql

echo "✅ 数据库初始化完成"
echo ""

# 检查配置
echo "🔧 检查配置..."
if [[ -z "$DEEPSEEK_API_KEY" ]]; then
    echo "⚠️  未设置 DEEPSEEK_API_KEY 环境变量"
    echo "   将使用配置文件中的默认值"
fi

echo "✅ 配置检查完成"
echo ""

# 启动应用
echo "🚀 启动应用程序..."
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

python3 main.py

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ 程序已退出"
