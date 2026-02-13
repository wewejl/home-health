#!/bin/bash
# 灵犀健康项目 - 统一启动脚本
# 用途: 一键启动所有开发服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  灵犀健康 - 开发环境启动${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# 检查 Docker 是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker 运行正常${NC}"
}

# 启动后端服务
start_backend() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  启动后端服务${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 检查 docker-compose.yml
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}❌ 未找到 docker-compose.yml${NC}"
        exit 1
    fi

    # 启动 Docker 容器
    docker-compose up -d backend db

    # 等待后端启动
    echo -e "${YELLOW}⏳ 等待后端服务启动...${NC}"
    sleep 5

    # 检查后端健康状态
    MAX_ATTEMPTS=30
    ATTEMPT=0
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if curl -s http://localhost:8100/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 后端服务启动成功${NC}"
            echo -e "   📍 API: http://localhost:8100"
            echo -e "   📍 文档: http://localhost:8100/docs"
            break
        fi
        ATTEMPT=$((ATTEMPT + 1))
        sleep 2
    done

    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo -e "${RED}❌ 后端服务启动超时${NC}"
        echo -e "${YELLOW}💡 查看日志: docker-compose logs backend${NC}"
    fi
}

# 启动前端服务
start_frontend() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  启动前端服务${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 检查 node_modules
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${YELLOW}⏳ 首次启动，安装前端依赖...${NC}"
        cd frontend
        npm install
        cd "$PROJECT_ROOT"
    fi

    # 启动前端（后台运行）
    cd frontend
    npm run dev > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd "$PROJECT_ROOT"

    echo -e "${GREEN}✅ 前端服务启动中...${NC}"
    echo -e "   📍 地址: http://localhost:5173"
    echo -e "   📍 PID: $FRONTEND_PID"
    echo -e "   💡 查看日志: tail -f /tmp/frontend.log"
}

# 启动 iOS 模拟器
start_ios() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  启动 iOS 模拟器${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 检查 Xcode 项目
    if [ ! -d "ios/xinlingyisheng/xinlingyisheng.xcodeproj" ]; then
        echo -e "${YELLOW}⚠️  未找到 Xcode 项目${NC}"
        echo -e "   💡 请手动打开 Xcode 启动模拟器"
        return
    fi

    # 检查是否有可用的模拟器
    if command -v xcrun &> /dev/null; then
        # 查找可用的模拟器
        DEVICE=$(xcrun simctl list devices available | grep "iPhone 15" | head -1 | grep -oE 'iPhone 15 [^\)]+' | head -1)

        if [ -z "$DEVICE" ]; then
            DEVICE=$(xcrun simctl list devices available | grep "iPhone" | head -1 | grep -oE 'iPhone [^\)]+' | head -1)
        fi

        if [ -n "$DEVICE" ]; then
            echo -e "${YELLOW}⏳ 启动模拟器: $DEVICE${NC}"
            xcrun simctl boot "$DEVICE" 2>/dev/null || echo -e "${YELLOW}⚠️  模拟器可能已在运行${NC}"
            echo -e "${GREEN}✅ 模拟器已就绪${NC}"
            echo -e "   💡 请在 Xcode 中构建并运行应用"
        else
            echo -e "${YELLOW}⚠️  未找到可用的模拟器${NC}"
            echo -e "   💡 请通过 Xcode 启动"
        fi
    else
        echo -e "${YELLOW}⚠️  未找到 xcrun 命令${NC}"
        echo -e "   💡 请通过 Xcode 启动模拟器"
    fi
}

# 打印服务状态
print_status() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  服务状态${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Docker 容器状态
    echo -e "${BLUE}Docker 容器:${NC}"
    docker-compose ps
    echo ""

    # 端口监听状态
    echo -e "${BLUE}端口监听:${NC}"
    if lsof -i :8100 > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅${NC} 后端 API: http://localhost:8100"
    else
        echo -e "   ${RED}❌${NC} 后端 API: http://localhost:8100 (未启动)"
    fi

    if lsof -i :5173 > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅${NC} 前端: http://localhost:5173"
    else
        echo -e "   ${YELLOW}⏳${NC} 前端: http://localhost:5173 (启动中...)"
    fi

    if lsof -i :5432 > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅${NC} PostgreSQL: localhost:5432"
    fi

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  快捷命令${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  后端日志: ${YELLOW}docker-compose logs -f backend${NC}"
    echo -e "  前端日志: ${YELLOW}tail -f /tmp/frontend.log${NC}"
    echo -e "  停止服务: ${YELLOW}docker-compose down${NC}"
    echo ""
}

# 主函数
main() {
    # 解析参数
    START_BACKEND=true
    START_FRONTEND=true
    START_IOS=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend-only)
                START_FRONTEND=false
                START_IOS=false
                shift
                ;;
            --frontend-only)
                START_BACKEND=false
                START_IOS=false
                shift
                ;;
            --ios)
                START_IOS=true
                shift
                ;;
            --no-frontend)
                START_FRONTEND=false
                shift
                ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  --backend-only    仅启动后端"
                echo "  --frontend-only   仅启动前端"
                echo "  --ios             同时启动 iOS 模拟器"
                echo "  --no-frontend     不启动前端"
                echo "  -h, --help        显示帮助"
                exit 0
                ;;
            *)
                echo -e "${RED}未知选项: $1${NC}"
                echo "使用 -h 或 --help 查看帮助"
                exit 1
                ;;
        esac
    done

    # 检查 Docker
    if [ "$START_BACKEND" = true ]; then
        check_docker
    fi

    # 启动服务
    if [ "$START_BACKEND" = true ]; then
        start_backend
    fi

    if [ "$START_FRONTEND" = true ]; then
        start_frontend
    fi

    if [ "$START_IOS" = true ]; then
        start_ios
    fi

    # 打印状态
    print_status

    echo -e "${GREEN}✅ 开发环境启动完成！${NC}"
    echo ""
}

# 运行主函数
main "$@"
