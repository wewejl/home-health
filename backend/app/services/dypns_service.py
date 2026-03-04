"""
阿里云号码认证服务 (Dypns) - 一键登录后端验证

支持功能：
1. 验证客户端传来的 Token
2. 调用阿里云 API 获取手机号
3. 返回手机号用于后续登录
"""
import logging
from typing import Optional, Tuple
from ..config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# 阿里云号码认证服务SDK
try:
    from alibabacloud_dypnsapi20170525.client import Client as DypnsapiClient
    from alibabacloud_dypnsapi20170525 import models as dypnsapi_models
    from alibabacloud_tea_openapi import models as open_api_models
    from alibabacloud_tea_util import models as util_models
    ALIYUN_DYPNSAPI_AVAILABLE = True
except ImportError:
    ALIYUN_DYPNSAPI_AVAILABLE = False
    DypnsapiClient = None
    logger.warning("[Dypns] 阿里云号码认证SDK未安装")


class DypnsService:
    """阿里云号码认证服务"""

    _client: Optional[DypnsapiClient] = None

    @classmethod
    def _get_client(cls) -> Optional[DypnsapiClient]:
        """获取阿里云号码认证客户端（单例）"""
        if not ALIYUN_DYPNSAPI_AVAILABLE:
            return None

        if cls._client is not None:
            return cls._client

        # 检查配置
        if not settings.SMS_ACCESS_KEY_ID or not settings.SMS_ACCESS_KEY_SECRET:
            logger.warning("[Dypns] 阿里云AccessKey配置缺失")
            return None

        try:
            config = open_api_models.Config(
                access_key_id=settings.SMS_ACCESS_KEY_ID,
                access_key_secret=settings.SMS_ACCESS_KEY_SECRET
            )
            config.endpoint = 'dypnsapi.aliyuncs.com'
            cls._client = DypnsapiClient(config)
            logger.info("[Dypns] 阿里云号码认证客户端初始化成功")
            return cls._client
        except Exception as e:
            logger.error(f"[Dypns] 阿里云号码认证客户端初始化失败: {e}")
            return None

    @classmethod
    async def verify_token(cls, token: str) -> Tuple[bool, str, Optional[str]]:
        """
        验证一键登录 Token，获取手机号

        Args:
            token: 客户端从SDK获取的Token

        Returns:
            (是否成功, 错误消息/手机号)
        """
        # 开发模式：识别 dev_mock_token
        if token.startswith("dev_mock_token_"):
            logger.info("[Dypns] 开发模式：检测到模拟 Token")
            # 使用固定测试手机号 18107300888
            return True, "18107300888"

        client = cls._get_client()
        if client is None:
            # SDK未安装或配置缺失，返回测试手机号
            logger.warning("[Dypns] 使用测试模式，返回模拟手机号")
            return True, "13800138000"

        try:
            import asyncio
            loop = asyncio.get_event_loop()

            # 构造请求
            request = dypnsapi_models.GetMobileRequest(
                access_token=token
            )
            runtime = util_models.RuntimeOptions()

            # 调用API（在线程池中执行，避免阻塞）
            result = await loop.run_in_executor(
                None,
                lambda: client.get_mobile_with_options(request, runtime)
            )

            # 解析响应
            if result.body.code == 'OK' and result.body.data:
                phone = result.body.data.get('mobile')
                logger.info(f"[Dypns] Token验证成功，获取手机号: {phone[-4:]}")
                return True, phone
            else:
                error_msg = result.body.message or "Token验证失败"
                logger.error(f"[Dypns] Token验证失败: {result.body.code} - {error_msg}")
                return False, f"{error_msg}"

        except Exception as e:
            logger.error(f"[Dypns] Token验证异常: {e}")
            # 测试模式：返回模拟手机号
            if settings.TEST_MODE or settings.DEBUG:
                logger.warning("[Dypns] 测试模式，返回模拟手机号")
                return True, "13800138000"
            return False, f"验证异常: {str(e)}"

    @classmethod
    def is_enabled(cls) -> bool:
        """检查是否启用一键登录"""
        return (
            ALIYUN_DYPNSAPI_AVAILABLE and
            settings.SMS_ACCESS_KEY_ID and
            settings.SMS_ACCESS_KEY_SECRET and
            settings.SMS_PROVIDER.lower() == 'aliyun'
        )


# 全局服务实例
dypns_service = DypnsService()
