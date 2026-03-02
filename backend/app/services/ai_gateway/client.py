"""HTTP client for remote AI service."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from ...config import get_settings
from ...schemas.ai_gateway import ChatRespondRequest, ChatRespondResponse


@dataclass
class AIGatewayClientError(Exception):
    """Unified gateway error for mapping upstream failures."""

    code: str
    message: str
    retryable: bool
    status_code: int | None = None

    def __str__(self) -> str:
        status = f" status={self.status_code}" if self.status_code is not None else ""
        return f"{self.code}:{status} {self.message}"


class AIGatewayClient:
    """Small typed client for POST /v1/chat/respond."""

    # 健康检查缓存（秒）
    _HEALTH_CHECK_TTL = 10
    _last_health_check: float = 0.0
    _last_health_status: bool = True

    def __init__(self):
        self._settings = get_settings()
        self._base_url = self._settings.AI_SERVICE_URL.rstrip("/")

    async def health_check(self) -> bool:
        """检查远程 AI 服务健康状态（带缓存）"""
        import time
        now = time.time()
        if now - self._last_health_check < self._HEALTH_CHECK_TTL:
            return self._last_health_status

        try:
            timeout = httpx.Timeout(2.0)  # 健康检查快速超时
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(f"{self._base_url}/health")
                self._last_health_status = response.status_code == 200
        except Exception:
            self._last_health_status = False
        finally:
            self._last_health_check = now
        return self._last_health_status

    async def respond(
        self,
        payload: ChatRespondRequest,
        transport_request_id: str | None = None,
    ) -> ChatRespondResponse:
        url = f"{self._base_url}/v1/chat/respond"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._settings.AI_SERVICE_TOKEN}",
        }
        if transport_request_id:
            headers["X-Request-Id"] = transport_request_id

        retries = max(0, int(self._settings.AI_SERVICE_MAX_RETRIES))
        max_attempts = retries + 1
        timeout = httpx.Timeout(
            timeout=float(self._settings.AI_SERVICE_TIMEOUT),
            connect=float(self._settings.AI_SERVICE_CONNECT_TIMEOUT),
        )

        last_error: AIGatewayClientError | None = None
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        url,
                        json=payload.model_dump(exclude_none=True),
                        headers=headers,
                    )

                if response.status_code == 200:
                    return ChatRespondResponse.model_validate(response.json())

                err = self._map_http_error(response)
                last_error = err
                if err.retryable and attempt < max_attempts - 1:
                    await asyncio.sleep(self._retry_backoff_seconds(attempt))
                    continue
                raise err

            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as exc:
                last_error = AIGatewayClientError(
                    code="AI_TIMEOUT",
                    message=str(exc),
                    retryable=True,
                )
                if attempt < max_attempts - 1:
                    await asyncio.sleep(self._retry_backoff_seconds(attempt))
                    continue
                raise last_error from exc
            except httpx.HTTPError as exc:
                last_error = AIGatewayClientError(
                    code="AI_UPSTREAM_5XX",
                    message=str(exc),
                    retryable=True,
                )
                if attempt < max_attempts - 1:
                    await asyncio.sleep(self._retry_backoff_seconds(attempt))
                    continue
                raise last_error from exc

        if last_error is not None:
            raise last_error
        raise AIGatewayClientError(
            code="AI_INTERNAL_ERROR",
            message="unknown gateway error",
            retryable=False,
        )

    def _retry_backoff_seconds(self, attempt: int) -> float:
        # simple linear backoff: base_ms * (attempt + 1)
        base_ms = max(1, int(self._settings.AI_SERVICE_RETRY_BACKOFF_MS))
        return (base_ms * (attempt + 1)) / 1000.0

    def _map_http_error(self, response: httpx.Response) -> AIGatewayClientError:
        status = response.status_code
        message = self._extract_message(response)

        if status == 400:
            return AIGatewayClientError("AI_BAD_REQUEST", message, retryable=False, status_code=status)
        if status in {401, 403}:
            return AIGatewayClientError("AI_UNAUTHORIZED", message, retryable=False, status_code=status)
        if status == 429:
            return AIGatewayClientError("AI_OVERLOADED", message, retryable=True, status_code=status)
        if status >= 500:
            return AIGatewayClientError("AI_UPSTREAM_5XX", message, retryable=True, status_code=status)
        return AIGatewayClientError("AI_INTERNAL_ERROR", message, retryable=False, status_code=status)

    def _extract_message(self, response: httpx.Response) -> str:
        try:
            data = response.json()
            if isinstance(data, dict):
                if isinstance(data.get("error"), dict):
                    return str(data["error"].get("message") or data["error"].get("code") or response.text)
                if data.get("detail"):
                    return str(data["detail"])
        except Exception:
            pass
        return response.text[:500]

