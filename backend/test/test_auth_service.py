"""
AuthService 单元测试

测试认证服务的所有方法：
- Token 创建和验证
- 用户创建和获取
- 用户资料更新
- 密码注册和登录
- 密码重置

参考设计文档: docs/plans/2026-02-11-test-coverage-100-implementation-plan.md Task 7
"""
import pytest
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# 导入 AuthService
try:
    from app.services.auth_service import AuthService
    from app.models.user import User
    from app.config import get_settings, reset_settings
except ImportError:
    from backend.app.services.auth_service import AuthService
    from backend.app.models.user import User
    from backend.app.config import get_settings, reset_settings


# ============================================================================
# Token 相关测试
# ============================================================================

class TestTokenCreation:
    """测试 Token 创建"""

    def test_create_token_access(self, db_session: Session):
        """测试创建 access token"""
        token = AuthService.create_token(1, "access")
        assert token is not None
        assert isinstance(token, str)
        # JWT token 应该包含三个部分 (header.payload.signature)
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_token_refresh(self, db_session: Session):
        """测试创建 refresh token"""
        token = AuthService.create_token(1, "refresh")
        assert token is not None
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_tokens_pair(self, db_session: Session):
        """测试创建 token 对"""
        access, refresh = AuthService.create_tokens(1)
        assert access is not None
        assert refresh is not None
        assert access != refresh  # 两个 token 应该不同
        # 两个都应该是有效的 JWT 格式
        assert len(access.split(".")) == 3
        assert len(refresh.split(".")) == 3


class TestTokenVerification:
    """测试 Token 验证"""

    def test_verify_valid_access_token(self, db_session: Session):
        """测试验证有效的 access token"""
        token = AuthService.create_token(1, "access")
        user_id = AuthService.verify_token(token, "access")
        assert user_id == 1

    def test_verify_valid_refresh_token(self, db_session: Session):
        """测试验证有效的 refresh token"""
        token = AuthService.create_token(1, "refresh")
        user_id = AuthService.verify_token(token, "refresh")
        assert user_id == 1

    def test_verify_invalid_token(self, db_session: Session):
        """测试验证无效 token"""
        user_id = AuthService.verify_token("invalid_token", "access")
        assert user_id is None

    def test_verify_malformed_token(self, db_session: Session):
        """测试验证格式错误的 token"""
        # 只有两部分，不是有效的 JWT
        user_id = AuthService.verify_token("header.payload", "access")
        assert user_id is None

    def test_verify_token_type_mismatch(self, db_session: Session):
        """测试 token 类型不匹配"""
        access_token = AuthService.create_token(1, "access")
        # 尝试用 refresh 类型验证 access token
        user_id = AuthService.verify_token(access_token, "refresh")
        assert user_id is None  # 应该返回 None 因为类型不匹配

    def test_verify_test_mode_token_valid(self, db_session: Session):
        """测试测试模式 token - 有效格式"""
        # 设置测试模式
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            user_id = AuthService.verify_token("test_123", "access")
            assert user_id == 123
        finally:
            # 恢复原始设置
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_verify_test_mode_token_invalid_format(self, db_session: Session):
        """测试测试模式 token - 无效格式"""
        # 设置测试模式
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            # 无效的测试 token 格式
            user_id = AuthService.verify_token("test_abc", "access")
            assert user_id is None  # 应该返回 None 因为 "abc" 不是有效的整数
        finally:
            # 恢复原始设置
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_verify_test_mode_token_without_prefix(self, db_session: Session):
        """测试测试模式 - 没有 test_ 前缀的普通 token"""
        # 设置测试模式
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            # 普通 token 应该正常验证
            token = AuthService.create_token(1, "access")
            user_id = AuthService.verify_token(token, "access")
            assert user_id == 1
        finally:
            # 恢复原始设置
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestTokenRefresh:
    """测试 Token 刷新"""

    def test_refresh_tokens_valid(self, db_session: Session):
        """测试刷新有效的 token"""
        refresh_token = AuthService.create_token(1, "refresh")
        result = AuthService.refresh_tokens(refresh_token)
        assert result is not None
        new_access, new_refresh = result
        assert new_access is not None
        assert new_refresh is not None
        assert isinstance(new_access, str)
        assert isinstance(new_refresh, str)
        # 新 token 应该和旧 token 不同
        assert new_access != refresh_token

    def test_refresh_tokens_invalid(self, db_session: Session):
        """测试刷新无效的 token"""
        result = AuthService.refresh_tokens("invalid_token")
        assert result is None

    def test_refresh_tokens_with_access_token(self, db_session: Session):
        """测试用 access token 刷新（应该失败）"""
        access_token = AuthService.create_token(1, "access")
        # access token 不能用于刷新
        result = AuthService.refresh_tokens(access_token)
        assert result is None  # 因为 token 类型不匹配


# ============================================================================
# 用户创建和获取测试
# ============================================================================

class TestUserCreation:
    """测试用户创建和获取"""

    def test_get_or_create_user_new(self, db_session: Session):
        """测试创建新用户"""
        user, is_new = AuthService.get_or_create_user(db_session, "19912345678")
        assert is_new is True
        assert user.phone == "19912345678"
        assert user.id is not None
        assert user.nickname == f"用户5678"  # 默认昵称是手机号后四位
        assert user.is_profile_completed is False
        assert user.is_active is True

    def test_get_or_create_user_existing(self, db_session: Session):
        """测试获取已存在的用户"""
        phone = "19912345679"
        # 第一次创建
        user1, is_new1 = AuthService.get_or_create_user(db_session, phone)
        assert is_new1 is True

        # 第二次获取
        user2, is_new2 = AuthService.get_or_create_user(db_session, phone)
        assert is_new2 is False
        assert user2.id == user1.id
        assert user2.phone == phone

    def test_get_user_by_id_exists(self, db_session: Session):
        """测试根据 ID 获取存在的用户"""
        user, _ = AuthService.get_or_create_user(db_session, "19912345680")
        retrieved = AuthService.get_user_by_id(db_session, user.id)
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.phone == user.phone

    def test_get_user_by_id_not_exists(self, db_session: Session):
        """测试根据 ID 获取不存在的用户"""
        retrieved = AuthService.get_user_by_id(db_session, 99999)
        assert retrieved is None

    def test_get_user_by_id_inactive(self, db_session: Session):
        """测试获取已禁用的用户"""
        user, _ = AuthService.get_or_create_user(db_session, "19912345681")
        user.is_active = False
        db_session.commit()

        retrieved = AuthService.get_user_by_id(db_session, user.id)
        assert retrieved is None  # 不活跃用户不应该被获取

    def test_get_user_by_phone_exists(self, db_session: Session):
        """测试根据手机号获取存在的用户"""
        user, _ = AuthService.get_or_create_user(db_session, "19912345682")
        retrieved = AuthService.get_user_by_phone(db_session, user.phone)
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.phone == user.phone

    def test_get_user_by_phone_not_exists(self, db_session: Session):
        """测试根据手机号获取不存在的用户"""
        retrieved = AuthService.get_user_by_phone(db_session, "19912345683")
        assert retrieved is None


# ============================================================================
# 用户资料更新测试
# ============================================================================

class TestUserProfileUpdate:
    """测试用户资料更新"""

    def test_update_user_profile_nickname_and_gender(self, db_session: Session):
        """测试更新昵称和性别"""
        user, _ = AuthService.get_or_create_user(db_session, "19912345690")
        updated = AuthService.update_user_profile(
            db_session, user,
            {"nickname": "测试用户", "gender": "male"}
        )
        assert updated.nickname == "测试用户"
        assert updated.gender == "male"
        # 完善了昵称和性别后，应该标记为资料已完善
        assert updated.is_profile_completed is True

    def test_update_user_profile_partial_update(self, db_session: Session):
        """测试部分更新用户资料"""
        user, _ = AuthService.get_or_create_user(db_session, "19912345691")
        updated = AuthService.update_user_profile(
            db_session, user,
            {"nickname": "新昵称"}
        )
        assert updated.nickname == "新昵称"
        # 只更新昵称，没有性别，不应该标记为资料已完善
        assert updated.is_profile_completed is False

    def test_update_user_profile_all_fields(self, db_session: Session):
        """测试更新所有用户资料字段"""
        user, _ = AuthService.get_or_create_user(db_session, "19912345692")
        from datetime import date
        profile_data = {
            "nickname": "完整用户",
            "avatar_url": "https://example.com/avatar.jpg",
            "gender": "female",
            "birthday": date(1990, 1, 1),
            "emergency_contact_name": "张三",
            "emergency_contact_phone": "13800138000",
            "emergency_contact_relation": "spouse"
        }
        updated = AuthService.update_user_profile(db_session, user, profile_data)
        assert updated.nickname == "完整用户"
        assert updated.avatar_url == "https://example.com/avatar.jpg"
        assert updated.gender == "female"
        assert updated.birthday == date(1990, 1, 1)
        assert updated.emergency_contact_name == "张三"
        assert updated.emergency_contact_phone == "13800138000"
        assert updated.emergency_contact_relation == "spouse"
        assert updated.is_profile_completed is True

    def test_update_user_profile_none_values_ignored(self, db_session: Session):
        """测试更新时 None 值被忽略"""
        user, _ = AuthService.get_or_create_user(db_session, "19912345693")
        user.nickname = "原始昵称"
        db_session.commit()

        # 尝试将昵称设为 None（应该被忽略）
        updated = AuthService.update_user_profile(
            db_session, user,
            {"nickname": None, "gender": "male"}
        )
        # 昵称应该保持不变
        assert updated.nickname == "原始昵称"
        assert updated.gender == "male"


# ============================================================================
# 手机号状态检查测试
# ============================================================================

class TestPhoneStatusCheck:
    """测试手机号状态检查"""

    def test_check_phone_status_not_exists(self, db_session: Session):
        """测试检查手机号状态 - 用户不存在"""
        exists, has_password = AuthService.check_phone_status(db_session, "19912345700")
        assert exists is False
        assert has_password is False

    def test_check_phone_status_exists_no_password(self, db_session: Session):
        """测试检查手机号状态 - 用户存在但无密码"""
        user, _ = AuthService.get_or_create_user(db_session, "19912345701")
        exists, has_password = AuthService.check_phone_status(db_session, user.phone)
        assert exists is True
        assert has_password is False

    def test_check_phone_status_exists_with_password(self, db_session: Session):
        """测试检查手机号状态 - 用户存在且有密码"""
        user, _ = AuthService.register_with_password(
            db_session, "19912345702", "Test123456"
        )
        exists, has_password = AuthService.check_phone_status(db_session, user.phone)
        assert exists is True
        assert has_password is True


# ============================================================================
# 密码注册测试
# ============================================================================

class TestPasswordRegistration:
    """测试密码注册"""

    def test_register_with_password_new_user(self, db_session: Session):
        """测试密码注册新用户"""
        user, is_new = AuthService.register_with_password(
            db_session, "19912345800", "Test123456"
        )
        assert is_new is True
        assert user.phone == "19912345800"
        assert user.password_hash is not None
        assert len(user.password_hash) > 0
        assert user.has_password is True

    def test_register_with_password_existing_user_no_password(self, db_session: Session):
        """测试为已存在的无密码用户设置密码"""
        # 先创建一个没有密码的用户
        user1, _ = AuthService.get_or_create_user(db_session, "19912345801")
        assert user1.password_hash is None

        # 为该用户设置密码
        user2, is_new = AuthService.register_with_password(
            db_session, "19912345801", "Test123456"
        )
        assert is_new is False  # 不是新用户
        assert user2.id == user1.id
        assert user2.password_hash is not None
        assert user2.has_password is True

    def test_register_with_password_existing_user_with_password(self, db_session: Session):
        """测试为已有密码的用户重新设置密码（覆盖旧密码）"""
        # 先注册一个用户
        user1, _ = AuthService.register_with_password(
            db_session, "19912345802", "OldPassword123"
        )
        old_hash = user1.password_hash

        # 用新密码重新注册（会覆盖旧密码）
        user2, is_new = AuthService.register_with_password(
            db_session, "19912345802", "NewPassword123"
        )
        assert is_new is False
        assert user2.id == user1.id
        # 密码哈希应该不同
        assert user2.password_hash != old_hash


# ============================================================================
# 密码登录测试
# ============================================================================

class TestPasswordLogin:
    """测试密码登录"""

    def test_login_with_password_success(self, db_session: Session):
        """测试密码登录成功"""
        # 先注册
        AuthService.register_with_password(db_session, "19912345900", "Test123456")
        # 再登录
        user, error = AuthService.login_with_password(
            db_session, "19912345900", "Test123456"
        )
        assert user is not None
        assert error == ""
        assert user.phone == "19912345900"

    def test_login_with_password_wrong_password(self, db_session: Session):
        """测试密码登录 - 错误密码"""
        # 先注册
        AuthService.register_with_password(db_session, "19912345901", "Test123456")
        # 错误密码登录
        user, error = AuthService.login_with_password(
            db_session, "19912345901", "WrongPassword"
        )
        assert user is None
        assert error != ""
        assert "手机号或密码错误" in error

    def test_login_with_password_user_not_exists(self, db_session: Session):
        """测试密码登录 - 用户不存在"""
        user, error = AuthService.login_with_password(
            db_session, "19912345902", "Test123456"
        )
        assert user is None
        assert error != ""
        assert "手机号或密码错误" in error

    def test_login_with_password_user_inactive(self, db_session: Session):
        """测试密码登录 - 账号已禁用"""
        # 先注册一个用户
        user, _ = AuthService.register_with_password(
            db_session, "19912345903", "Test123456"
        )
        # 禁用用户
        user.is_active = False
        db_session.commit()

        # 尝试登录
        logged_in_user, error = AuthService.login_with_password(
            db_session, "19912345903", "Test123456"
        )
        assert logged_in_user is None
        assert error == "账号已被禁用"

    def test_login_with_password_no_password_set(self, db_session: Session):
        """测试密码登录 - 用户未设置密码"""
        # 创建一个没有密码的用户
        user, _ = AuthService.get_or_create_user(db_session, "19912345904")
        assert user.password_hash is None

        # 尝试用密码登录
        logged_in_user, error = AuthService.login_with_password(
            db_session, "19912345904", "SomePassword"
        )
        assert logged_in_user is None
        assert error == "该账号未设置密码，请使用验证码登录"


# ============================================================================
# 密码设置和重置测试
# ============================================================================

class TestPasswordSetAndReset:
    """测试密码设置和重置"""

    def test_set_user_password(self, db_session: Session):
        """测试设置用户密码"""
        user, _ = AuthService.get_or_create_user(db_session, "19912346000")
        assert user.password_hash is None

        success = AuthService.set_user_password(db_session, user, "NewPassword123")
        assert success is True
        # 刷新后验证密码已设置
        db_session.refresh(user)
        assert user.password_hash is not None
        assert user.has_password is True

    def test_set_user_password_update_existing(self, db_session: Session):
        """测试更新已存在的密码"""
        user, _ = AuthService.register_with_password(
            db_session, "19912346001", "OldPassword123"
        )
        old_hash = user.password_hash

        success = AuthService.set_user_password(db_session, user, "NewPassword123")
        assert success is True
        # 刷新后验证密码已更新
        db_session.refresh(user)
        assert user.password_hash != old_hash

    def test_reset_password_success(self, db_session: Session):
        """测试重置密码成功"""
        user, _ = AuthService.get_or_create_user(db_session, "19912346002")
        success, error = AuthService.reset_password(
            db_session, user.phone, "NewPassword123"
        )
        assert success is True
        assert error == ""
        # 刷新后验证密码已设置
        db_session.refresh(user)
        assert user.password_hash is not None
        assert user.has_password is True

    def test_reset_password_user_not_exists(self, db_session: Session):
        """测试重置密码 - 用户不存在"""
        success, error = AuthService.reset_password(
            db_session, "19912346003", "NewPassword123"
        )
        assert success is False
        assert error == "用户不存在"

    def test_reset_password_user_inactive(self, db_session: Session):
        """测试重置密码 - 账号已禁用"""
        user, _ = AuthService.get_or_create_user(db_session, "19912346004")
        user.is_active = False
        db_session.commit()

        success, error = AuthService.reset_password(
            db_session, user.phone, "NewPassword123"
        )
        assert success is False
        assert error == "账号已被禁用"


# ============================================================================
# 认证事件日志测试
# ============================================================================

class TestAuthEventLogging:
    """测试认证事件日志"""

    def test_log_auth_event_basic(self, db_session: Session, caplog):
        """测试记录基本认证事件"""
        import logging
        caplog.set_level(logging.INFO)

        AuthService.log_auth_event("login", user_id=123)

        # 验证日志被记录
        assert "[AUTH_EVENT]" in caplog.text
        assert "login" in caplog.text

    def test_log_auth_event_with_extra(self, db_session: Session, caplog):
        """测试记录带额外信息的认证事件"""
        import logging
        caplog.set_level(logging.INFO)

        AuthService.log_auth_event(
            "register",
            user_id=456,
            extra={"phone": "13800138000", "method": "password"}
        )

        # 验证日志被记录
        assert "[AUTH_EVENT]" in caplog.text
        assert "register" in caplog.text
