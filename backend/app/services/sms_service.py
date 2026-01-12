"""
短信服务模块 - 验证码发送与管理

TODO: 接入真实短信网关时，需要:
1. 替换 SMSGateway 实现类
2. 配置短信服务商 API Key
3. 配置短信模板 ID
"""
import random
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from threading import Lock
from ..config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class VerificationCode:
    """验证码数据结构"""
    code: str
    phone: str
    created_at: float
    expires_at: float
    attempts: int = 0
    verified: bool = False


@dataclass
class RateLimitInfo:
    """频率限制信息"""
    count: int = 0
    first_request_time: float = 0
    locked_until: float = 0


class VerificationCodeStore:
    """
    验证码存储管理
    
    生产环境建议替换为 Redis 实现
    """
    
    def __init__(self):
        self._codes: Dict[str, VerificationCode] = {}
        self._phone_rate_limits: Dict[str, RateLimitInfo] = {}
        self._ip_rate_limits: Dict[str, RateLimitInfo] = {}
        self._lock = Lock()
        
        # 配置
        self.code_expire_seconds = 300  # 验证码有效期 5 分钟
        self.code_cooldown_seconds = 60  # 发送冷却时间 60 秒
        self.max_attempts = 5  # 最大验证尝试次数
        self.phone_rate_limit_window = 3600  # 1小时
        self.phone_rate_limit_max = 10  # 同一手机号每小时最多10次
        self.ip_rate_limit_window = 3600  # 1小时
        self.ip_rate_limit_max = 30  # 同一IP每小时最多30次
        self.lock_duration = 1800  # 锁定时长 30 分钟
    
    def generate_code(self, length: int = 6) -> str:
        """生成随机验证码"""
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])
    
    def check_cooldown(self, phone: str) -> Tuple[bool, int]:
        """
        检查是否在冷却期
        返回: (是否可发送, 剩余冷却秒数)
        """
        with self._lock:
            if phone in self._codes:
                code_info = self._codes[phone]
                elapsed = time.time() - code_info.created_at
                if elapsed < self.code_cooldown_seconds:
                    remaining = int(self.code_cooldown_seconds - elapsed)
                    return False, remaining
            return True, 0
    
    def check_phone_rate_limit(self, phone: str) -> Tuple[bool, str]:
        """
        检查手机号频率限制
        返回: (是否允许, 错误消息)
        """
        with self._lock:
            now = time.time()
            
            if phone not in self._phone_rate_limits:
                self._phone_rate_limits[phone] = RateLimitInfo()
            
            limit_info = self._phone_rate_limits[phone]
            
            # 检查是否被锁定
            if limit_info.locked_until > now:
                remaining = int(limit_info.locked_until - now)
                return False, f"该手机号已被锁定，请{remaining // 60}分钟后重试"
            
            # 检查时间窗口是否过期，需要重置
            if now - limit_info.first_request_time > self.phone_rate_limit_window:
                limit_info.count = 0
                limit_info.first_request_time = now
            
            # 检查是否超过限制
            if limit_info.count >= self.phone_rate_limit_max:
                limit_info.locked_until = now + self.lock_duration
                return False, "发送次数过多，请稍后重试"
            
            return True, ""
    
    def check_ip_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """
        检查IP频率限制
        返回: (是否允许, 错误消息)
        """
        with self._lock:
            now = time.time()
            
            if ip not in self._ip_rate_limits:
                self._ip_rate_limits[ip] = RateLimitInfo()
            
            limit_info = self._ip_rate_limits[ip]
            
            # 检查是否被锁定
            if limit_info.locked_until > now:
                remaining = int(limit_info.locked_until - now)
                return False, f"请求过于频繁，请{remaining // 60}分钟后重试"
            
            # 检查时间窗口是否过期
            if now - limit_info.first_request_time > self.ip_rate_limit_window:
                limit_info.count = 0
                limit_info.first_request_time = now
            
            # 检查是否超过限制
            if limit_info.count >= self.ip_rate_limit_max:
                limit_info.locked_until = now + self.lock_duration
                return False, "请求过于频繁，请稍后重试"
            
            return True, ""
    
    def increment_rate_limit(self, phone: str, ip: str):
        """增加频率计数"""
        with self._lock:
            now = time.time()
            
            # 手机号计数
            if phone in self._phone_rate_limits:
                limit_info = self._phone_rate_limits[phone]
                if limit_info.count == 0:
                    limit_info.first_request_time = now
                limit_info.count += 1
            
            # IP 计数
            if ip in self._ip_rate_limits:
                limit_info = self._ip_rate_limits[ip]
                if limit_info.count == 0:
                    limit_info.first_request_time = now
                limit_info.count += 1
    
    def store_code(self, phone: str, code: str) -> VerificationCode:
        """存储验证码"""
        with self._lock:
            now = time.time()
            code_info = VerificationCode(
                code=code,
                phone=phone,
                created_at=now,
                expires_at=now + self.code_expire_seconds
            )
            self._codes[phone] = code_info
            return code_info
    
    def verify_code(self, phone: str, code: str) -> Tuple[bool, str]:
        """
        验证码校验
        返回: (是否验证成功, 错误消息)
        """
        with self._lock:
            now = time.time()
            
            # 测试模式下允许 000000
            if settings.TEST_MODE and code == "000000":
                logger.info(f"[SMS] 测试模式验证通过: phone={phone}")
                return True, ""
            
            if phone not in self._codes:
                return False, "请先获取验证码"
            
            code_info = self._codes[phone]
            
            # 检查是否已过期
            if now > code_info.expires_at:
                del self._codes[phone]
                return False, "验证码已过期，请重新获取"
            
            # 检查验证次数
            if code_info.attempts >= self.max_attempts:
                del self._codes[phone]
                return False, "验证次数过多，请重新获取验证码"
            
            # 验证码比对
            code_info.attempts += 1
            if code_info.code != code:
                remaining = self.max_attempts - code_info.attempts
                return False, f"验证码错误，还剩{remaining}次机会"
            
            # 验证成功，删除验证码
            del self._codes[phone]
            return True, ""
    
    def cleanup_expired(self):
        """清理过期数据"""
        with self._lock:
            now = time.time()
            
            # 清理过期验证码
            expired_phones = [
                phone for phone, info in self._codes.items()
                if now > info.expires_at
            ]
            for phone in expired_phones:
                del self._codes[phone]
            
            # 清理过期频率限制记录
            for rate_dict in [self._phone_rate_limits, self._ip_rate_limits]:
                expired_keys = [
                    key for key, info in rate_dict.items()
                    if (now - info.first_request_time > self.phone_rate_limit_window * 2 
                        and info.locked_until < now)
                ]
                for key in expired_keys:
                    del rate_dict[key]


class SMSGateway:
    """
    短信网关接口
    
    TODO: 接入真实短信服务商时，实现以下方法:
    - 阿里云短信: https://www.aliyun.com/product/sms
    - 腾讯云短信: https://cloud.tencent.com/product/sms
    - 七牛云短信: https://www.qiniu.com/products/sms
    """
    
    @staticmethod
    async def send_sms(phone: str, code: str, template_id: str = "verification") -> Tuple[bool, str]:
        """
        发送短信
        
        Args:
            phone: 手机号
            code: 验证码
            template_id: 短信模板ID
        
        Returns:
            (是否发送成功, 错误消息或成功消息)
        """
        # TODO: 替换为真实短信发送逻辑
        # 示例：阿里云短信发送
        # from alibabacloud_dysmsapi20170525.client import Client
        # client = Client(config)
        # response = await client.send_sms_async(...)
        
        logger.info(f"[SMS] 模拟发送验证码: phone={phone}, code={code}")
        
        # 模拟发送延迟
        import asyncio
        await asyncio.sleep(0.1)
        
        # 模拟成功
        return True, "发送成功"


class SMSService:
    """短信服务主类"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.store = VerificationCodeStore()
        self.gateway = SMSGateway()
        logger.info("[SMS] 短信服务初始化完成")
    
    async def send_verification_code(
        self, 
        phone: str, 
        client_ip: str = "0.0.0.0"
    ) -> Tuple[bool, str, int]:
        """
        发送验证码
        
        Args:
            phone: 手机号
            client_ip: 客户端IP
        
        Returns:
            (是否成功, 消息, 过期时间秒数)
        """
        # 1. 检查冷却期
        can_send, cooldown_remaining = self.store.check_cooldown(phone)
        if not can_send:
            logger.warning(f"[SMS] 冷却期内: phone={phone}, remaining={cooldown_remaining}s")
            return False, f"请{cooldown_remaining}秒后重试", 0
        
        # 2. 检查手机号频率限制
        allowed, error_msg = self.store.check_phone_rate_limit(phone)
        if not allowed:
            logger.warning(f"[SMS] 手机号频率限制: phone={phone}, error={error_msg}")
            return False, error_msg, 0
        
        # 3. 检查IP频率限制
        allowed, error_msg = self.store.check_ip_rate_limit(client_ip)
        if not allowed:
            logger.warning(f"[SMS] IP频率限制: ip={client_ip}, error={error_msg}")
            return False, error_msg, 0
        
        # 4. 生成验证码
        code = self.store.generate_code()
        
        # 5. 发送短信
        success, msg = await self.gateway.send_sms(phone, code)
        if not success:
            logger.error(f"[SMS] 发送失败: phone={phone}, error={msg}")
            return False, "发送失败，请稍后重试", 0
        
        # 6. 存储验证码 & 更新频率限制
        code_info = self.store.store_code(phone, code)
        self.store.increment_rate_limit(phone, client_ip)
        
        expires_in = int(code_info.expires_at - code_info.created_at)
        logger.info(f"[SMS] 验证码发送成功: phone={phone}, expires_in={expires_in}s")
        
        # 事件日志（用于埋点）
        self._log_event("send_code_success", {"phone": phone[-4:], "ip": client_ip})
        
        return True, "验证码发送成功", expires_in
    
    def verify_code(self, phone: str, code: str) -> Tuple[bool, str]:
        """
        验证验证码
        
        Args:
            phone: 手机号
            code: 用户输入的验证码
        
        Returns:
            (是否验证成功, 错误消息)
        """
        success, msg = self.store.verify_code(phone, code)
        
        if success:
            logger.info(f"[SMS] 验证成功: phone={phone}")
            self._log_event("verify_code_success", {"phone": phone[-4:]})
        else:
            logger.warning(f"[SMS] 验证失败: phone={phone}, error={msg}")
            self._log_event("verify_code_failed", {"phone": phone[-4:], "error": msg})
        
        return success, msg
    
    def _log_event(self, event_type: str, data: dict):
        """
        事件日志记录（用于埋点分析）
        
        TODO: 接入正式埋点系统时实现
        """
        logger.info(f"[EVENT] {event_type}: {data}")


# 全局单例
sms_service = SMSService()
