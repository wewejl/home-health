#!/usr/bin/env python3
"""
测试令牌支持补丁
在服务器后端容器内运行此脚本: docker exec -i home-health-backend python3 < fix_auth_test_mode.py
"""

# 读取文件内容
file_path = "/app/app/services/auth_service.py"

try:
    with open(file_path, 'r') as f:
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
        with open(file_path, 'w') as f:
            f.write(content)
        print("✅ 成功更新 verify_token 方法 - 已添加测试令牌支持")
    else:
        print("⚠️  未找到匹配的旧方法，可能已经更新过")
        # 检查是否已经有测试令牌支持
        if "test_N" in content or "test_" in content and "TEST_MODE" in content:
            print("✅ 文件已包含测试令牌支持代码")

except Exception as e:
    print(f"❌ 更新失败: {e}")
    import traceback
    traceback.print_exc()
