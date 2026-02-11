"""
认证相关测试
"""
import pytest
from backend.app.services.admin_auth_service import AdminAuthService
from backend.app.models.admin_user import AdminUser


class TestAdminAuthService:
    """管理员认证服务测试"""

    def test_hash_password(self):
        """测试密码哈希"""
        password = "TestPassword123"
        hash_result = AdminAuthService.hash_password(password)

        assert hash_result is not None
        assert hash_result != password
        assert hash_result.startswith("$2b$")  # bcrypt hash

    def test_verify_password_correct(self):
        """测试验证正确密码"""
        password = "TestPassword123"
        hash_result = AdminAuthService.hash_password(password)

        is_valid = AdminAuthService.verify_password(password, hash_result)
        assert is_valid is True

    def test_verify_password_incorrect(self):
        """测试验证错误密码"""
        password = "TestPassword123"
        wrong_password = "WrongPassword123"
        hash_result = AdminAuthService.hash_password(password)

        is_valid = AdminAuthService.verify_password(wrong_password, hash_result)
        assert is_valid is False

    def test_create_admin_token(self):
        """测试创建管理员 Token"""
        admin_id = 123
        token = AdminAuthService.create_admin_token(admin_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long

    def test_verify_admin_token_valid(self):
        """测试验证有效的管理员 Token"""
        admin_id = 456
        token = AdminAuthService.create_admin_token(admin_id)

        verified_id = AdminAuthService.verify_admin_token(token)
        assert verified_id == admin_id

    def test_verify_admin_token_invalid(self):
        """测试验证无效的管理员 Token"""
        invalid_token = "invalid.token.here"

        verified_id = AdminAuthService.verify_admin_token(invalid_token)
        assert verified_id is None
