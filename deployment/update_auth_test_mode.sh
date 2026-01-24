#!/bin/bash
# 服务器更新脚本：支持测试令牌认证
# 在服务器上运行此脚本

cd /root/home-health/deployment

echo "=== 步骤 1: 备份当前文件 ==="
docker exec home-health-backend cp /app/app/services/auth_service.py /app/app/services/auth_service.py.bak

echo "=== 步骤 2: 更新 auth_service.py ==="
docker exec -i home-health-backend sh /dev/stdin <<'EOF'
# 读取文件内容
file_path="/app/app/services/auth_service.py"

# 创建新版本的 verify_token 方法
cat > /tmp/patch.py << 'PATCH'
# 此脚本用于添加测试令牌支持
import re

with open('/app/app/services/auth_service.py', 'r') as f:
    content = f.read()

# 找到 verify_token 方法并替换
old_method = '''    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[int]:
        """
        验证JWT Token

        Args:
            token: JWT Token
            token_type: 期望的Token类型

        Returns:
            用户ID 或 None
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # 检查Token类型
            if payload.get("type", "access") != token_type:
                logger.warning(f"[AUTH] Token类型不匹配: expected={token_type}, got={payload.get('type')}")
                return None

            user_id = payload.get("sub")
            if user_id is None:
                return None

            return int(user_id)
        except JWTError as e:
            logger.warning(f"[AUTH] Token验证失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"[AUTH] Token验证异常: {str(e)}")
            return None'''

new_method = '''    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[int]:
        """
        验证JWT Token

        Args:
            token: JWT Token 或测试令牌 (test_N 格式)
            token_type: 期望的Token类型

        Returns:
            用户ID 或 None
        """
        # 测试模式：支持 test_N 格式的测试令牌
        if settings.TEST_MODE and token.startswith("test_"):
            try:
                user_id = int(token.split("_")[1])
                logger.info(f"[AUTH] 测试模式认证: user_id={user_id}")
                return user_id
            except (ValueError, IndexError):
                logger.warning(f"[AUTH] 无效的测试令牌格式: {token}")
                return None

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # 检查Token类型
            if payload.get("type", "access") != token_type:
                logger.warning(f"[AUTH] Token类型不匹配: expected={token_type}, got={payload.get('type')}")
                return None

            user_id = payload.get("sub")
            if user_id is None:
                return None

            return int(user_id)
        except JWTError as e:
            logger.warning(f"[AUTH] Token验证失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"[AUTH] Token验证异常: {str(e)}")
            return None'''

if old_method in content:
    content = content.replace(old_method, new_method)
    with open('/app/app/services/auth_service.py', 'w') as f:
        f.write(content)
    print("已成功更新 verify_token 方法")
else:
    print("未找到匹配的旧方法，可能已经更新过")
PATCH

python3 /tmp/patch.py
EOF

echo "=== 步骤 3: 重启后端容器 ==="
docker-compose restart backend

echo "=== 步骤 4: 等待服务就绪 ==="
sleep 10

echo "=== 步骤 5: 验证修复 ==="
curl -s -X POST "http://localhost/sessions" \
  -H "Authorization: Bearer test_1" \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "dermatology"}' | head -100

echo ""
echo "=== 更新完成 ==="
