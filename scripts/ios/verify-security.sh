#!/bin/bash
# iOS 安全配置验证脚本

echo "🔍 验证 iOS 安全配置..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# 1. 检查是否有硬编码 Token
echo ""
echo "1️⃣ 检查硬编码 Token..."
if grep -r "test_1" ios/xinlingyisheng/xinlingyisheng/ --include="*.swift" 2>/dev/null | grep -v ".backup" | grep -v "deprecated" | grep -v "//"; then
    echo -e "${RED}❌ 发现硬编码 Token${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ 未发现硬编码 Token${NC}"
fi

# 2. 检查 HTTP URL（除了 localhost 和 127.0.0.1）
echo ""
echo "2️⃣ 检查非本地 HTTP URL..."
if grep -r "http://" ios/xinlingyisheng/xinlingyisheng/ --include="*.swift" 2>/dev/null | grep -v "127.0.0.1" | grep -v "localhost" | grep -v ".backup" | grep -v "//" | grep -v "ws://"; then
    echo -e "${YELLOW}⚠️  发现非本地 HTTP URL${NC}"
else
    echo -e "${GREEN}✅ 未发现不安全的 HTTP URL${NC}"
fi

# 3. 检查 URL 参数中的 Token
echo ""
echo "3️⃣ 检查 URL 中的 Token（queryItems.*token）..."
if grep -r "queryItems.*token\|URLQueryItem.*token" ios/xinlingyisheng/xinlingyisheng/ --include="*.swift" 2>/dev/null | grep -v ".backup" | grep -v "//" | grep -v "language"; then
    echo -e "${RED}❌ 发现 Token 在 URL 参数中${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ Token 未在 URL 中传递${NC}"
fi

# 4. 检查是否使用了 SecurityConfig
echo ""
echo "4️⃣ 检查是否使用 SecurityConfig..."
if grep -r "SecurityConfig" ios/xinlingyisheng/xinlingyisheng/ --include="*.swift" 2>/dev/null | wc -l | xargs -I {} test {} -gt 0; then
    echo -e "${GREEN}✅ 使用了 SecurityConfig${NC}"
else
    echo -e "${YELLOW}⚠️  未发现 SecurityConfig 使用${NC}"
fi

# 5. 检查 Token 是否通过 Header 传递
echo ""
echo "5️⃣ 检查 Authorization Header..."
if grep -r "Authorization.*Bearer" ios/xinlingyisheng/xinlingyisheng/ --include="*.swift" 2>/dev/null | wc -l | xargs -I {} test {} -gt 0; then
    echo -e "${GREEN}✅ 使用 Authorization Header${NC}"
else
    echo -e "${YELLOW}⚠️  未发现 Authorization Header 使用${NC}"
fi

# 6. 检查 Keychain 存储
echo ""
echo "6️⃣ 检查 Keychain 使用..."
if grep -r "Keychain" ios/xinlingyisheng/xinlingyisheng/ --include="*.swift" 2>/dev/null | wc -l | xargs -I {} test {} -gt 0; then
    echo -e "${GREEN}✅ 使用了 Keychain${NC}"
else
    echo -e "${YELLOW}⚠️  未发现 Keychain 使用${NC}"
fi

# 7. 检查证书文件
echo ""
echo "7️⃣ 检查证书文件..."
if [ -f "ios/Certificates/cert.pem" ] && [ -f "ios/Certificates/key.pem" ]; then
    echo -e "${GREEN}✅ 证书文件存在${NC}"
else
    echo -e "${YELLOW}⚠️  证书文件缺失${NC}"
fi

# 8. 检查 xcconfig 文件
echo ""
echo "8️⃣ 检查 xcconfig 配置文件..."
if [ -f "ios/config/Development.xcconfig" ] && [ -f "ios/config/Production.xcconfig" ]; then
    echo -e "${GREEN}✅ xcconfig 文件存在${NC}"
else
    echo -e "${YELLOW}⚠️  xcconfig 文件缺失${NC}"
fi

# 总结
echo ""
echo "────────────────────────────────────"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ 安全验证通过！${NC}"
    exit 0
else
    echo -e "${RED}❌ 发现 $ERRORS 个安全问题${NC}"
    exit 1
fi
