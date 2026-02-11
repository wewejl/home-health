"""
密码复杂度验证测试
"""
import pytest
try:
    from app.routes.admin_auth import validate_password_complexity
except ImportError:
    from backend.app.routes.admin_auth import validate_password_complexity


class TestPasswordValidation:
    """密码复杂度验证测试"""

    def test_valid_password(self):
        """测试有效的密码"""
        is_valid, msg = validate_password_complexity("Abc12345")
        assert is_valid is True
        assert msg == ""

    def test_valid_password_with_special_char(self):
        """测试带特殊字符的有效密码"""
        is_valid, msg = validate_password_complexity("Abc12345@#")
        assert is_valid is True
        assert msg == ""

    def test_too_short(self):
        """测试密码过短"""
        is_valid, msg = validate_password_complexity("Abc123")
        assert is_valid is False
        assert "8 个字符" in msg

    def test_no_lowercase(self):
        """测试缺少小写字母"""
        is_valid, msg = validate_password_complexity("ABC12345")
        assert is_valid is False
        assert "小写字母" in msg

    def test_no_uppercase(self):
        """测试缺少大写字母"""
        is_valid, msg = validate_password_complexity("abc12345")
        assert is_valid is False
        assert "大写字母" in msg

    def test_no_digit(self):
        """测试缺少数字"""
        is_valid, msg = validate_password_complexity("Abcdefgh")
        assert is_valid is False
        assert "数字" in msg

    def test_exactly_8_chars_valid(self):
        """测试刚好 8 个字符的有效密码"""
        is_valid, msg = validate_password_complexity("Abc12345")
        assert is_valid is True
        assert msg == ""
