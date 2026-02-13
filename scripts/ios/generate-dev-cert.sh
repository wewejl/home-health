#!/bin/bash
# iOS 开发环境自签名 HTTPS 证书生成脚本

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CERT_DIR="${PROJECT_ROOT}/ios/Certificates"

echo "📁 证书目录: $CERT_DIR"
mkdir -p "$CERT_DIR"

# 检查是否已存在证书
if [ -f "$CERT_DIR/cert.pem" ] && [ -f "$CERT_DIR/key.pem" ]; then
    echo "⚠️  证书已存在，跳过生成"
    echo "如需重新生成，请先删除: $CERT_DIR"
    exit 0
fi

# 生成自签名证书（有效期 365 天）
echo "🔐 生成自签名证书..."
openssl req -x509 -newkey rsa:4096 \
    -keyout "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -days 365 \
    -nodes \
    -subj "/CN=127.0.0.1" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1"

echo "✅ 证书生成完成!"
echo "   证书文件: $CERT_DIR/cert.pem"
echo "   私钥文件: $CERT_DIR/key.pem"
echo ""
echo "📝 证书信息:"
openssl x509 -in "$CERT_DIR/cert.pem" -noout -subject -dates
