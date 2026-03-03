#!/bin/bash
echo "🧪 测试真正的流式响应"
echo "=================================="
echo ""

timeout 3 curl -N -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"real_stream","his_user_id":"doctor","message":"你好"}' \
  2>/dev/null || true

echo ""
echo ""
echo "✅ 测试完成"
