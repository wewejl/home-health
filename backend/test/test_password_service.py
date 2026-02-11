"""
PasswordService 单元测试

测试密码服务的所有方法：
- hash_password() 密码哈希
- verify_password() 密码验证
- validate_password_strength() 密码强度验证
- needs_rehash() 哈希更新检查
"""
import pytest

# 导入密码服务
try:
    from app.services.password_service import (
        PasswordService,
        hash_password,
        verify_password,
        validate_password_strength
    )
except ImportError:
    from backend.app.services.password_service import (
        PasswordService,
        hash_password,
        verify_password,
        validate_password_strength
    )


class TestHashPassword:
    """测试密码哈希"""

    def test_hash_password_returns_string(self):
        """测试哈希返回字符串"""
        result = PasswordService.hash_password("test123")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_password_different_salts(self):
        """测试相同密码产生不同哈希（因为盐不同）"""
        password = "password123"
        hash1 = PasswordService.hash_password(password)
        hash2 = PasswordService.hash_password(password)

        # 盐不同导致哈希值不同
        assert hash1 != hash2

    def test_hash_password_contains_bcrypt_prefix(self):
        """测试哈希值包含bcrypt前缀"""
        result = PasswordService.hash_password("test123")

        # bcrypt哈希以$2b$开头
        assert result.startswith("$2b$")

    def test_hash_password_empty_string(self):
        """测试空密码哈希"""
        result = PasswordService.hash_password("")

        assert isinstance(result, str)
        assert len(result) > 0


class TestVerifyPassword:
    """测试密码验证"""

    def test_verify_password_correct(self):
        """测试验证正确的密码"""
        password = "test123"
        hashed = PasswordService.hash_password(password)

        result = PasswordService.verify_password(password, hashed)

        assert result is True

    def test_verify_password_incorrect(self):
        """测试验证错误的密码"""
        password = "test123"
        wrong_password = "wrong123"
        hashed = PasswordService.hash_password(password)

        result = PasswordService.verify_password(wrong_password, hashed)

        assert result is False

    def test_verify_password_case_sensitive(self):
        """测试密码区分大小写"""
        password = "Test123"
        hashed = PasswordService.hash_password(password)

        result = PasswordService.verify_password("test123", hashed)

        assert result is False

    def test_verify_password_invalid_hash(self):
        """测试无效哈希值"""
        result = PasswordService.verify_password("test123", "invalid_hash")

        assert result is False

    def test_verify_password_empty_strings(self):
        """测试空字符串"""
        hashed = PasswordService.hash_password("")

        result = PasswordService.verify_password("", hashed)

        assert result is True

    def test_verify_password_unicode(self):
        """测试Unicode密码"""
        password = "密码123测试"
        hashed = PasswordService.hash_password(password)

        result = PasswordService.verify_password(password, hashed)

        assert result is True


class TestValidatePasswordStrength:
    """测试密码强度验证"""

    def test_validate_valid_password(self):
        """测试有效密码"""
        result = PasswordService.validate_password_strength("abc123")

        assert result == (True, "")

    def test_validate_empty_password(self):
        """测试空密码"""
        result = PasswordService.validate_password_strength("")

        assert result == (False, "密码不能为空")

    def test_validate_short_password(self):
        """测试过短密码"""
        result = PasswordService.validate_password_strength("12345")  # 少于6位

        assert result == (False, "密码长度至少6位")

    def test_validate_exact_min_length(self):
        """测试恰好是最小长度"""
        result = PasswordService.validate_password_strength("123456")

        assert result == (True, "")

    def test_validate_long_password(self):
        """测试过长密码"""
        long_password = "a" * 33  # 超过32位
        result = PasswordService.validate_password_strength(long_password)

        assert result == (False, "密码长度不能超过32位")

    def test_validate_exact_max_length(self):
        """测试恰好是最大长度"""
        max_password = "a" * 32
        result = PasswordService.validate_password_strength(max_password)

        assert result == (True, "")

    def test_validate_password_with_spaces(self):
        """测试包含空格的密码"""
        result = PasswordService.validate_password_strength("abc 123")

        assert result == (False, "密码不能包含空格")

    def test_validate_password_with_only_spaces(self):
        """测试只有空格的密码"""
        result = PasswordService.validate_password_strength("     ")

        # 空格检查在长度检查之后
        assert result == (False, "密码不能包含空格")


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_hash_password_function(self):
        """测试hash_password便捷函数"""
        result = hash_password("test123")

        assert isinstance(result, str)
        assert result.startswith("$2b$")

    def test_verify_password_function(self):
        """测试verify_password便捷函数"""
        password = "test123"
        hashed = hash_password(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_validate_password_strength_function(self):
        """测试validate_password_strength便捷函数"""
        result = validate_password_strength("abc123")

        assert result == (True, "")


class TestNeedsRehash:
    """测试哈希更新检查"""

    def test_needs_rehash_always_false(self):
        """测试当前实现总是返回False"""
        result = PasswordService.needs_rehash("$2b$12$hash")

        assert result is False


class TestEdgeCases:
    """测试边界情况"""

    def test_very_long_password_hash(self):
        """测试超长密码哈希"""
        very_long = "a" * 1000
        result = PasswordService.hash_password(very_long)

        assert isinstance(result, str)

    def test_special_characters_password(self):
        """测试特殊字符密码"""
        special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = PasswordService.hash_password(special)

        result = PasswordService.verify_password(special, hashed)

        assert result is True

    def test_chinese_characters_password(self):
        """测试中文字符密码"""
        chinese = "中文密码测试一二三"
        hashed = PasswordService.hash_password(chinese)

        result = PasswordService.verify_password(chinese, hashed)

        assert result is True

    def test_mixed_script_password(self):
        """测试混合文字密码"""
        mixed = "abc中文123!@#"
        hashed = PasswordService.hash_password(mixed)

        result = PasswordService.verify_password(mixed, hashed)

        assert result is True

    def test_verify_with_none_hash(self):
        """测试None哈希值"""
        result = PasswordService.verify_password("test123", None)

        assert result is False

    def test_verify_with_empty_hash(self):
        """测试空哈希值"""
        result = PasswordService.verify_password("test123", "")

        assert result is False
