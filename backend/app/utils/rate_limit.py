"""
简单的速率限制工具

基于内存的速率限制实现，用于防止 API 暴力攻击
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    内存速率限制器

    使用滑动窗口算法进行速率限制
    """

    def __init__(self):
        # 存储每个标识符的请求记录: {key: [(timestamp, count), ...]}
        self._requests: Dict[str, list[Tuple[float, int]]] = defaultdict(list)
        # 清理过期数据的间隔（秒）
        self._cleanup_interval = 300
        self._last_cleanup = time.time()

    def _cleanup_expired(self, current_time: float, window_size: int):
        """清理过期的请求记录"""
        if current_time - self._last_cleanup > self._cleanup_interval:
            cutoff = current_time - window_size
            for key in list(self._requests.keys()):
                self._requests[key] = [
                    (ts, count) for ts, count in self._requests[key]
                    if ts > cutoff
                ]
                if not self._requests[key]:
                    del self._requests[key]
            self._last_cleanup = current_time

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        检查是否允许请求

        Args:
            key: 限制键（如 IP 地址、用户 ID 等）
            max_requests: 时间窗口内允许的最大请求数
            window_seconds: 时间窗口大小（秒）

        Returns:
            (是否允许, 剩余请求数)
        """
        current_time = time.time()

        # 清理过期数据
        self._cleanup_expired(current_time, window_seconds)

        # 获取该键的请求记录
        requests = self._requests[key]

        # 移除窗口外的记录
        cutoff = current_time - window_seconds
        self._requests[key] = [(ts, count) for ts, count in requests if ts > cutoff]
        requests = self._requests[key]

        # 计算窗口内的总请求数
        total_requests = sum(count for _, count in requests)

        if total_requests >= max_requests:
            return False, 0

        # 记录本次请求
        self._requests[key].append((current_time, 1))
        return True, max_requests - total_requests - 1

    def get_remaining_requests(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> int:
        """获取剩余请求数"""
        current_time = time.time()
        cutoff = current_time - window_seconds
        requests = [
            (ts, count) for ts, count in self._requests.get(key, [])
            if ts > cutoff
        ]
        total = sum(count for _, count in requests)
        return max(0, max_requests - total)


# 全局速率限制器实例
_rate_limiters: Dict[str, RateLimiter] = {}


def get_rate_limiter(name: str = "default") -> RateLimiter:
    """获取指定名称的速率限制器"""
    if name not in _rate_limiters:
        _rate_limiters[name] = RateLimiter()
    return _rate_limiters[name]


# 预定义的速率限制规则
RATE_LIMITS = {
    # 认证相关：更严格的限制
    "send_code": (5, 60),      # 每分钟最多 5 次验证码
    "login": (10, 60),          # 每分钟最多 10 次登录
    "register": (3, 60),        # 每分钟最多 3 次注册

    # 一般 API：适度限制
    "api": (100, 60),           # 每分钟最多 100 次

    # 上传相关：严格限制
    "upload": (10, 60),         # 每分钟最多 10 次上传
}


def check_rate_limit(
    request: Request,
    limit_type: str = "api",
    key_func: callable = None
) -> None:
    """
    检查速率限制，超过限制则抛出 HTTPException

    Args:
        request: FastAPI Request 对象
        limit_type: 限制类型（对应 RATE_LIMITS 中的键）
        key_func: 自定义键函数，接收 request 返回限制键

    Raises:
        HTTPException: 当超过速率限制时
    """
    if limit_type not in RATE_LIMITS:
        logger.warning(f"未知的速率限制类型: {limit_type}，使用默认限制")
        limit_type = "api"

    max_requests, window_seconds = RATE_LIMITS[limit_type]

    # 获取限制键
    if key_func:
        key = key_func(request)
    else:
        # 默认使用客户端 IP
        key = request.client.host if request.client else "unknown"

    limiter = get_rate_limiter(limit_type)
    allowed, remaining = limiter.is_allowed(key, max_requests, window_seconds)

    if not allowed:
        logger.warning(f"速率限制触发: {limit_type}, key={key}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "请求过于频繁，请稍后再试",
                "limit_type": limit_type,
                "retry_after": window_seconds
            }
        )

    # 将剩余请求数添加到 request state，以便在响应头中使用
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = max_requests
