"""
SMSService 单元测试

测试短信服务的所有方法：
- 验证码发送
- 验证码验证（成功/失败/过期）
- 限流功能
- 冷却期检查
"""
import pytest
import os
import time
from datetime import datetime, timedelta
from datetime import timezone, datetime as dt
from sqlalchemy.orm import Session
from unittest.mock import patch

# 导入 SMSService 和相关类
try:
    from app.services.sms_service import (
        SMSService,
        VerificationCodeStore,
        VerificationCode,
        RateLimitInfo,
        SMSGateway,
        sms_service
    )
    from app.config import get_settings, reset_settings
except ImportError:
    from backend.app.services.sms_service import (
        SMSService,
        VerificationCodeStore,
        VerificationCode,
        RateLimitInfo,
        SMSGateway,
        sms_service
    )
    from backend.app.config import get_settings, reset_settings


# ============================================================================
# VerificationCodeStore 测试
# ============================================================================

class TestVerificationCodeStore:
    """测试验证码存储管理"""

    def test_generate_code_default_length(self):
        """测试生成默认长度（6位）验证码"""
        store = VerificationCodeStore()
        code = store.generate_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_generate_code_custom_length(self):
        """测试生成自定义长度验证码"""
        store = VerificationCodeStore()
        code = store.generate_code(length=4)
        assert len(code) == 4
        assert code.isdigit()

    def test_generate_code_uniqueness(self):
        """测试验证码生成唯一性（高概率不同）"""
        store = VerificationCodeStore()
        codes = set(store.generate_code() for _ in range(100))
        # 100次生成至少有90个不同的验证码
        assert len(codes) >= 90

    def test_store_code(self):
        """测试存储验证码"""
        store = VerificationCodeStore()
        phone = "13800138000"
        code = "123456"

        code_info = store.store_code(phone, code)

        assert code_info.phone == phone
        assert code_info.code == code
        assert code_info.attempts == 0
        assert code_info.verified is False
        assert code_info.created_at > 0
        assert code_info.expires_at > code_info.created_at

    def test_check_cooldown_no_previous_code(self):
        """测试冷却期检查 - 没有之前的验证码"""
        store = VerificationCodeStore()
        can_send, remaining = store.check_cooldown("13800138001")
        assert can_send is True
        assert remaining == 0

    def test_check_cooldown_within_period(self):
        """测试冷却期检查 - 在冷却期内"""
        store = VerificationCodeStore()
        phone = "13800138002"

        # 先存储一个验证码
        store.store_code(phone, "123456")

        # 立即检查，应该在冷却期内
        can_send, remaining = store.check_cooldown(phone)
        assert can_send is False
        assert 0 < remaining <= store.code_cooldown_seconds

    def test_check_cooldown_after_period(self):
        """测试冷却期检查 - 冷却期已过"""
        store = VerificationCodeStore()
        phone = "13800138003"

        # 先存储一个验证码，但修改创建时间为冷却期之前
        code_info = store.store_code(phone, "123456")
        code_info.created_at = time.time() - store.code_cooldown_seconds - 1

        can_send, remaining = store.check_cooldown(phone)
        assert can_send is True
        assert remaining == 0


class TestPhoneRateLimit:
    """测试手机号频率限制"""

    def test_check_phone_rate_limit_new_phone(self):
        """测试手机号频率限制 - 新手机号"""
        store = VerificationCodeStore()
        allowed, error_msg = store.check_phone_rate_limit("13800138004")
        assert allowed is True
        assert error_msg == ""

    def test_check_phone_rate_limit_under_max(self):
        """测试手机号频率限制 - 未超过最大次数"""
        store = VerificationCodeStore()
        phone = "13800138005"

        # 发送几次，但未达到上限
        for _ in range(5):
            store.increment_rate_limit(phone, "127.0.0.1")

        allowed, error_msg = store.check_phone_rate_limit(phone)
        assert allowed is True
        assert error_msg == ""

    def test_check_phone_rate_limit_exceeds_max(self):
        """测试手机号频率限制 - 超过最大次数"""
        store = VerificationCodeStore()
        phone = "13800138006"

        # 手动设置达到上限的频率限制
        limit_info = store._phone_rate_limits[phone] = RateLimitInfo(
            count=store.phone_rate_limit_max,
            first_request_time=time.time()
        )

        # 应该被锁定
        allowed, error_msg = store.check_phone_rate_limit(phone)
        assert allowed is False
        assert "发送次数过多" in error_msg or "锁定" in error_msg

    def test_check_phone_rate_limit_locked(self):
        """测试手机号频率限制 - 已被锁定"""
        store = VerificationCodeStore()
        phone = "13800138007"

        # 设置为锁定状态
        limit_info = store._phone_rate_limits[phone] = RateLimitInfo()
        limit_info.count = store.phone_rate_limit_max
        limit_info.locked_until = time.time() + 1000

        allowed, error_msg = store.check_phone_rate_limit(phone)
        assert allowed is False
        assert "锁定" in error_msg or "分钟后" in error_msg

    def test_check_phone_rate_limit_window_reset(self):
        """测试手机号频率限制 - 时间窗口重置"""
        store = VerificationCodeStore()
        phone = "13800138008"

        # 设置旧的计数记录
        limit_info = store._phone_rate_limits[phone] = RateLimitInfo()
        limit_info.count = store.phone_rate_limit_max
        limit_info.first_request_time = time.time() - store.phone_rate_limit_window - 1

        # 时间窗口已过期，应该重置
        allowed, error_msg = store.check_phone_rate_limit(phone)
        assert allowed is True
        assert error_msg == ""


class TestIPRateLimit:
    """测试IP频率限制"""

    def test_check_ip_rate_limit_new_ip(self):
        """测试IP频率限制 - 新IP"""
        store = VerificationCodeStore()
        allowed, error_msg = store.check_ip_rate_limit("192.168.1.1")
        assert allowed is True
        assert error_msg == ""

    def test_check_ip_rate_limit_under_max(self):
        """测试IP频率限制 - 未超过最大次数"""
        store = VerificationCodeStore()
        ip = "192.168.1.2"

        # 发送几次，但未达到上限
        for _ in range(10):
            store.increment_rate_limit("13800138009", ip)

        allowed, error_msg = store.check_ip_rate_limit(ip)
        assert allowed is True
        assert error_msg == ""

    def test_check_ip_rate_limit_exceeds_max(self):
        """测试IP频率限制 - 超过最大次数"""
        store = VerificationCodeStore()
        ip = "192.168.1.3"

        # 手动设置达到上限的频率限制
        limit_info = store._ip_rate_limits[ip] = RateLimitInfo(
            count=store.ip_rate_limit_max,
            first_request_time=time.time()
        )

        # 应该被锁定
        allowed, error_msg = store.check_ip_rate_limit(ip)
        assert allowed is False
        assert "请求过于频繁" in error_msg or "稍后重试" in error_msg


# ============================================================================
# 验证码验证测试
# ============================================================================

class TestVerifyCode:
    """测试验证码验证"""

    @patch('app.services.sms_service.settings')
    def test_verify_code_success(self, mock_settings):
        """测试验证码验证成功"""
        mock_settings.TEST_MODE = False
        store = VerificationCodeStore()
        phone = "13800138011"
        code = "123456"

        # 先存储验证码
        store.store_code(phone, code)

        # 验证应该成功
        success, msg = store.verify_code(phone, code)
        assert success is True
        assert msg == ""
        # 验证后验证码应该被删除
        assert phone not in store._codes

    @patch('app.services.sms_service.settings')
    def test_verify_code_wrong_code(self, mock_settings):
        """测试验证码验证 - 错误验证码"""
        mock_settings.TEST_MODE = False
        store = VerificationCodeStore()
        phone = "13800138012"
        correct_code = "123456"

        # 先存储验证码
        store.store_code(phone, correct_code)

        # 验证错误验证码
        success, msg = store.verify_code(phone, "000000")
        assert success is False
        assert "验证码错误" in msg
        # 验证码不应该被删除
        assert phone in store._codes

    @patch('app.services.sms_service.settings')
    def test_verify_code_no_code_sent(self, mock_settings):
        """测试验证码验证 - 未发送验证码"""
        mock_settings.TEST_MODE = False
        store = VerificationCodeStore()
        phone = "13800138013"

        success, msg = store.verify_code(phone, "123456")
        assert success is False
        assert "请先获取验证码" in msg

    @patch('app.services.sms_service.settings')
    def test_verify_code_expired(self, mock_settings):
        """测试验证码验证 - 已过期"""
        mock_settings.TEST_MODE = False
        store = VerificationCodeStore()
        phone = "13800138014"
        code = "123456"

        # 存储一个过期的验证码
        code_info = store.store_code(phone, code)
        code_info.expires_at = time.time() - 1

        success, msg = store.verify_code(phone, code)
        assert success is False
        assert "过期" in msg
        # 过期验证码应该被删除
        assert phone not in store._codes

    @patch('app.services.sms_service.settings')
    def test_verify_code_max_attempts_exceeded(self, mock_settings):
        """测试验证码验证 - 超过最大尝试次数"""
        mock_settings.TEST_MODE = False
        store = VerificationCodeStore()
        phone = "13800138015"
        code = "123456"

        # 存储验证码
        code_info = store.store_code(phone, code)

        # 尝试多次错误验证
        for _ in range(store.max_attempts):
            store.verify_code(phone, "000000")

        # 再试应该返回尝试次数过多
        success, msg = store.verify_code(phone, code)
        assert success is False
        assert "次数过多" in msg or "重新获取" in msg

    @patch('app.services.sms_service.settings')
    def test_verify_code_attempts_decrement_message(self, mock_settings):
        """测试验证码验证 - 剩余次数提示"""
        mock_settings.TEST_MODE = False
        store = VerificationCodeStore()
        phone = "13800138016"
        code = "123456"

        store.store_code(phone, code)

        # 第一次错误尝试
        success, msg = store.verify_code(phone, "000000")
        assert success is False
        remaining = store.max_attempts - 1
        assert str(remaining) in msg

    @patch('app.services.sms_service.settings')
    def test_verify_code_test_mode(self, mock_settings):
        """测试测试模式验证码验证"""
        mock_settings.TEST_MODE = True
        store = VerificationCodeStore()
        phone = "13800138017"

        # 测试模式下，任何验证码都应该通过
        success, msg = store.verify_code(phone, "any_code")
        assert success is True
        assert msg == ""


# ============================================================================
# SMSGateway 测试
# ============================================================================

class TestSMSGateway:
    """测试短信网关"""

    @pytest.mark.asyncio
    async def test_send_sms_test_mode(self):
        """测试测试模式发送短信"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        os.environ["SMS_PROVIDER"] = "mock"
        reset_settings()

        try:
            success, msg = await SMSGateway.send_sms("13800138018", "123456")
            assert success is True
            assert msg == "发送成功"
        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    @pytest.mark.asyncio
    async def test_send_sms_mock_provider(self):
        """测试 Mock 提供商发送短信"""
        original_provider = os.getenv("SMS_PROVIDER")
        os.environ["SMS_PROVIDER"] = "mock"
        reset_settings()

        try:
            success, msg = await SMSGateway.send_sms("13800138019", "123456")
            assert success is True
            assert msg == "发送成功"
        finally:
            if original_provider is not None:
                os.environ["SMS_PROVIDER"] = original_provider
            else:
                os.environ.pop("SMS_PROVIDER", None)
            reset_settings()


# ============================================================================
# SMSService 测试
# ============================================================================

class TestSMSService:
    """测试短信服务主类"""

    def test_singleton_instance(self):
        """测试单例模式"""
        service1 = SMSService()
        service2 = SMSService()
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_send_verification_code_success(self):
        """测试发送验证码成功"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            service = SMSService()
            success, msg, expires_in = await service.send_verification_code("13800138020")

            assert success is True
            assert msg == "验证码发送成功"
            assert expires_in == service.store.code_expire_seconds
        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    @pytest.mark.asyncio
    async def test_send_verification_code_cooldown(self):
        """测试发送验证码 - 冷却期内"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            service = SMSService()
            phone = "13800138021"

            # 第一次发送
            await service.send_verification_code(phone)

            # 立即再次发送，应该在冷却期内
            success, msg, expires_in = await service.send_verification_code(phone)
            assert success is False
            assert "秒后重试" in msg or "请" in msg
            assert expires_in == 0
        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    @pytest.mark.asyncio
    async def test_send_verification_code_rate_limit(self):
        """测试发送验证码 - 超过频率限制"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            service = SMSService()
            phone = "13800138022"
            ip = "192.168.1.10"

            # 手动设置达到上限的频率限制
            limit_info = service.store._phone_rate_limits[phone] = RateLimitInfo(
                count=service.store.phone_rate_limit_max,
                first_request_time=time.time()
            )
            service.store.increment_rate_limit(phone, ip)

            # 尝试发送
            success, msg, expires_in = await service.send_verification_code(phone, ip)
            assert success is False
            assert "次数过多" in msg or "锁定" in msg
            assert expires_in == 0
        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    @pytest.mark.asyncio
    async def test_send_verification_code_ip_rate_limit(self):
        """测试发送验证码 - IP 频率限制"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            service = SMSService()
            phone = "13800138023"
            ip = "192.168.1.11"

            # 手动设置IP达到上限的频率限制
            limit_info = service.store._ip_rate_limits[ip] = RateLimitInfo(
                count=service.store.ip_rate_limit_max,
                first_request_time=time.time()
            )
            service.store.increment_rate_limit(phone, ip)

            # 尝试发送
            success, msg, expires_in = await service.send_verification_code(phone, ip)
            assert success is False
            assert "请求过于频繁" in msg or "稍后重试" in msg
            assert expires_in == 0
        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    @pytest.mark.asyncio
    async def test_verify_code_service_success(self):
        """测试验证码服务 - 验证成功"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            service = SMSService()
            phone = "13800138024"
            code = "123456"

            # 存储验证码
            service.store.store_code(phone, code)

            # 验证
            success, msg = service.verify_code(phone, code)
            assert success is True
            assert msg == ""
        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    @pytest.mark.asyncio
    async def test_verify_code_service_wrong_code(self):
        """测试验证码服务 - 验证码错误"""
        # 保存原始设置并关闭测试模式
    @pytest.mark.asyncio
    @patch('app.services.sms_service.settings')
    async def test_verify_code_service_wrong_code(self, mock_settings):
        """测试验证码服务 - 验证码错误"""
        mock_settings.TEST_MODE = False
        service = SMSService()
        phone = "13800138025"
        correct_code = "123456"

        # 存储验证码
        service.store.store_code(phone, correct_code)

        # 验证错误验证码
        success, msg = service.verify_code(phone, "000000")
        assert success is False
        assert "验证码错误" in msg

    @pytest.mark.asyncio
    async def test_verify_code_service_test_mode(self):
        """测试验证码服务 - 测试模式"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            service = SMSService()
            phone = "13800138026"

            # 测试模式下，任何验证码都应该通过
            success, msg = service.verify_code(phone, "any_code")
            assert success is True
            assert msg == ""
        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


# ============================================================================
# 全局单例测试
# ============================================================================

class TestGlobalSMSService:
    """测试全局短信服务单例"""

    @pytest.mark.asyncio
    async def test_global_sms_service_instance(self):
        """测试全局服务实例"""
        assert sms_service is not None
        assert isinstance(sms_service, SMSService)

    @pytest.mark.asyncio
    async def test_global_sms_service_send(self):
        """测试通过全局服务发送"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            success, msg, expires_in = await sms_service.send_verification_code("13800138027")
            assert success is True
        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()
