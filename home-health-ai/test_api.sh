#!/bin/bash
# FastAPI 接口测试脚本

BASE_URL="http://localhost:8000"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🧪 FastAPI 接口测试套件                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# =====================================================
# 测试 1: 健康检查
# =====================================================
echo -e "${YELLOW}📋 测试 1: 健康检查${NC}"
echo "GET /health"
curl -s "${BASE_URL}/health" | jq '.'
echo -e "${GREEN}✅ 健康检查完成${NC}"
echo ""

# =====================================================
# 测试 2: 根路径
# =====================================================
echo -e "${YELLOW}📋 测试 2: API 信息${NC}"
echo "GET /"
curl -s "${BASE_URL}/" | jq '.'
echo -e "${GREEN}✅ API 信息获取完成${NC}"
echo ""

# =====================================================
# 测试 3: 单轮对话
# =====================================================
echo -e "${YELLOW}📋 测试 3: 单轮对话${NC}"
echo "POST /chat"
RESPONSE1=$(curl -s -X POST "${BASE_URL}/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_api_001",
    "his_user_id": "doctor_test",
    "message": "你好，我正在看一位叫李明的患者"
  }')
echo "$RESPONSE1" | jq '.'
echo -e "${GREEN}✅ 单轮对话完成${NC}"
echo ""

# =====================================================
# 测试 4: 多轮对话（测试记忆）
# =====================================================
echo -e "${YELLOW}📋 测试 4: 多轮对话（测试记忆）${NC}"
echo "第 1 轮: 告知患者信息"
curl -s -X POST "${BASE_URL}/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_api_memory",
    "his_user_id": "doctor_test",
    "message": "你好，我正在看一位叫王芳的患者，32岁，女性"
  }' | jq '.response' | head -c 100
echo "..."
echo ""

echo "第 2 轮: 测试是否记住"
RESPONSE2=$(curl -s -X POST "${BASE_URL}/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_api_memory",
    "his_user_id": "doctor_test",
    "message": "我刚才说的患者叫什么名字？"
  }')
echo "$RESPONSE2" | jq '.response'
echo ""

if echo "$RESPONSE2" | jq -r '.response' | grep -q "王芳"; then
    echo -e "${GREEN}✅ 记忆功能正常！${NC}"
else
    echo -e "${YELLOW}⚠️  记忆功能可能有问题${NC}"
fi
echo ""

# =====================================================
# 测试 5: 用药专家子 Agent
# =====================================================
echo -e "${YELLOW}📋 测试 5: 用药专家子 Agent${NC}"
echo "POST /chat (复杂用药问题)"
RESPONSE3=$(curl -s -X POST "${BASE_URL}/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_api_medication",
    "his_user_id": "doctor_test",
    "message": "患者同时服用阿司匹林和华法林，需要注意什么？"
  }')
echo "$RESPONSE3" | jq '.response' | head -c 200
echo "..."
echo ""

if echo "$RESPONSE3" | jq -r '.response' | grep -qiE "风险|INR|监测"; then
    echo -e "${GREEN}✅ 用药专家调用成功！${NC}"
else
    echo -e "${YELLOW}⚠️  未检测到用药专家特征${NC}"
fi
echo ""

# =====================================================
# 测试 6: 查询会话历史
# =====================================================
echo -e "${YELLOW}📋 测试 6: 查询会话历史${NC}"
echo "GET /history/test_api_001"
curl -s "${BASE_URL}/history/test_api_001" | jq '.'
echo -e "${GREEN}✅ 会话历史查询完成${NC}"
echo ""

# =====================================================
# 测试 7: 查询会话列表
# =====================================================
echo -e "${YELLOW}📋 测试 7: 查询会话列表${NC}"
echo "GET /sessions?his_user_id=doctor_test"
curl -s "${BASE_URL}/sessions?his_user_id=doctor_test" | jq '.'
echo -e "${GREEN}✅ 会话列表查询完成${NC}"
echo ""

# =====================================================
# 测试 8: 删除会话
# =====================================================
echo -e "${YELLOW}📋 测试 8: 删除会话${NC}"
echo "DELETE /sessions/test_api_001"
curl -s -X DELETE "${BASE_URL}/sessions/test_api_001" | jq '.'
echo -e "${GREEN}✅ 会话删除完成${NC}"
echo ""

# =====================================================
# 测试总结
# =====================================================
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 所有接口测试完成！${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "📚 查看完整 API 文档: ${BASE_URL}/docs"
echo "📊 查看交互式文档: ${BASE_URL}/redoc"
