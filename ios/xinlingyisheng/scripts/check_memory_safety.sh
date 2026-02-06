#!/bin/bash
# 内存安全检查脚本 v2.0
# 用于检测可能导致内存问题的代码模式
# 在提交代码前必须运行此脚本

set -e

echo "=== 内存安全检查 v2.0 ==="
echo ""

ISSUES_FOUND=0
WARNINGS_FOUND=0

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查1: deinit 中创建 Task
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "检查1: deinit 中创建异步 Task"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TASK_IN_DEINIT=$(find xinlingyisheng/xinlingyisheng -name "*.swift" -exec grep -l "deinit" {} \; 2>/dev/null | xargs -I {} sh -c 'grep -A 15 "deinit" {} | grep -q "Task.*{" && echo {}' 2>/dev/null || true)

if [ -n "$TASK_IN_DEINIT" ]; then
    echo -e "${RED}❌ 发现问题: deinit 中创建 Task${NC}"
    echo "$TASK_IN_DEINIT"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "${GREEN}✅ 未发现问题${NC}"
fi
echo ""

# 检查2: deinit 中使用 DispatchQueue.async
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "检查2: deinit 中使用 DispatchQueue.async"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DISPATCH_IN_DEINIT=$(find xinlingyisheng/xinlingyisheng -name "*.swift" -exec grep -l "deinit" {} \; 2>/dev/null | xargs -I {} sh -c 'grep -A 15 "deinit" {} | grep -q "DispatchQueue.*async" && echo {}' 2>/dev/null || true)

if [ -n "$DISPATCH_IN_DEINIT" ]; then
    echo -e "${RED}❌ 发现问题: deinit 中使用 DispatchQueue.async${NC}"
    echo "$DISPATCH_IN_DEINIT"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "${GREEN}✅ 未发现问题${NC}"
fi
echo ""

# 检查3: deinit 是否标记为 nonisolated（如果有 @MainActor 属性）
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "检查3: @MainActor 类的 deinit 是否标记 nonisolated"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
MAINACTOR_DEINIT=$(grep -rn "@MainActor" xinlingyisheng/xinlingyisheng --include="*.swift" | grep -A 50 "class.*ViewModel\|class.*Service" | grep -B 50 "deinit" | grep "deinit" | grep -v "nonisolated" | wc -l)

if [ "$MAINACTOR_DEINIT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  有 $MAINACTOR_DEINIT 个 @MainActor 类的 deinit 未标记 nonisolated${NC}"
    echo "建议检查这些类是否在 deinit 中访问了 @MainActor 属性"
    WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
else
    echo -e "${GREEN}✅ 所有 @MainActor 类的 deinit 都正确标记${NC}"
fi
echo ""

# 检查4: Combine sink 使用 weak self
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "检查4: Combine sink 使用 [weak self]"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SINK_WITHOUT_WEAK=$(grep -rn "\.sink" xinlingyisheng/xinlingyisheng --include="*.swift" 2>/dev/null | grep -v "\[weak self\]" | grep -v "\.store(in:" | wc -l)

if [ "$SINK_WITHOUT_WEAK" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  有 $SINK_WITHOUT_WEAK 处 sink 可能缺失 [weak self]${NC}"
    echo "建议人工检查以下位置："
    grep -rn "\.sink" xinlingyisheng/xinlingyisheng --include="*.swift" 2>/dev/null | grep -v "\[weak self\]" | head -5
    WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
else
    echo -e "${GREEN}✅ 所有 sink 都使用了 weak self${NC}"
fi
echo ""

# 检查5: 检查是否有 cleanup() 方法对应的 onDisappear
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "检查5: cleanup() 方法是否在 View 中调用"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
CLEANUP_METHODS=$(grep -rn "func cleanup" xinlingyisheng/xinlingyisheng --include="*.swift" 2>/dev/null | grep -v "//" | wc -l)
ON_DISAPPEAR=$(grep -rn "onDisappear" xinlingyisheng/xinlingyisheng/Views --include="*.swift" 2>/dev/null | wc -l)

echo "ℹ️  发现 $CLEANUP_METHODS 个 cleanup 方法"
echo "ℹ️  发现 $ON_DISAPPEAR 个 onDisappear 调用"
echo ""

# 检查6: 检查是否有未清理的 Timer
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "检查6: Timer 是否在 deinit 中清理"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TIMER_PROPERTY=$(grep -rn "Timer\?" xinlingyisheng/xinlingyisheng --include="*.swift" 2>/dev/null | grep -v "invalidate\|//" | wc -l)

if [ "$TIMER_PROPERTY" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  有 $TIMER_PROPERTY 处 Timer 属性${NC}"
    echo "建议确认这些 Timer 在 deinit 中调用了 invalidate()"
else
    echo -e "${GREEN}✅ 未发现 Timer 属性${NC}"
fi
echo ""

# 总结
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "=== 检查完成 ==="
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $ISSUES_FOUND -eq 0 ] && [ $WARNINGS_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ 所有检查通过，未发现内存安全问题${NC}"
    exit 0
elif [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${YELLOW}⚠️  发现 $WARNINGS_FOUND 个警告，请确认是否需要修复${NC}"
    exit 0
else
    echo -e "${RED}❌ 发现 $ISSUES_FOUND 个严重问题和 $WARNINGS_FOUND 个警告${NC}"
    echo "请修复严重问题后再次运行检查"
    exit 1
fi
