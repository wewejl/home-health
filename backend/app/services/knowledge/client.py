"""
独立知识库服务客户端

调用独立的 medical-knowledge-service REST API
"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from app.config import get_settings

logger = logging.getLogger(__name__)


class KnowledgeServiceClient:
    """独立知识库服务客户端"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        初始化客户端

        Args:
            base_url: 服务地址，默认从配置读取
            api_key: API 密钥，默认从配置读取
            timeout: 请求超时时间（秒）
        """
        settings = get_settings()
        self.base_url = (base_url or settings.KNOWLEDGE_SERVICE_URL).rstrip("/")
        self.api_key = api_key or settings.KNOWLEDGE_SERVICE_API_KEY
        self.timeout = timeout if timeout is not None else settings.KNOWLEDGE_SERVICE_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端（懒加载）"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.base_url}/health",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[KnowledgeServiceClient] 健康检查失败: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def search(
        self,
        query: str,
        specialty: str = "general",
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> Dict[str, Any]:
        """
        搜索医学知识

        Args:
            query: 搜索查询文本
            specialty: 可选的科室过滤
            top_k: 返回结果数量
            score_threshold: 相似度阈值

        Returns:
            {
                "found": bool,
                "results": [...],
                "count": int,
                "query": str,
                "specialty": str
            }
        """
        try:
            client = await self._get_client()

            data = {
                "query": query,
                "specialty": specialty,
                "top_k": top_k,
                "score_threshold": score_threshold
            }

            response = await client.post(
                f"{self.base_url}/api/v1/search",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            result = response.json()

            # 统一返回格式
            data = result.get("data", {})
            return {
                "found": data.get("count", 0) > 0,
                "results": data.get("results", []),
                "count": data.get("count", 0),
                "query_used": data.get("query", query),
                "specialty": specialty,
                "source": "vector_knowledge_base"
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"[KnowledgeServiceClient] HTTP 错误: {e.response.status_code}")
            return {
                "found": False,
                "results": [],
                "count": 0,
                "query_used": query,
                "specialty": specialty,
                "error": f"HTTP {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"[KnowledgeServiceClient] 搜索失败: {e}")
            return {
                "found": False,
                "results": [],
                "count": 0,
                "query_used": query,
                "specialty": specialty,
                "error": str(e)
            }

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取知识库统计信息

        Returns:
            统计信息
        """
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.base_url}/api/v1/stats",
                headers=self._get_headers()
            )
            response.raise_for_status()
            result = response.json()
            return result.get("data", {})
        except Exception as e:
            logger.error(f"[KnowledgeServiceClient] 获取统计信息失败: {e}")
            return {}

    async def list_specialties(self) -> List[Dict[str, Any]]:
        """
        获取支持的科室列表

        Returns:
            科室列表
        """
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.base_url}/api/v1/specialties",
                headers=self._get_headers()
            )
            response.raise_for_status()
            result = response.json()
            return result.get("data", [])
        except Exception as e:
            logger.error(f"[KnowledgeServiceClient] 获取科室列表失败: {e}")
            return []


# 全局客户端实例（单例）
_client: Optional[KnowledgeServiceClient] = None


def get_knowledge_client() -> KnowledgeServiceClient:
    """获取知识库服务客户端（单例）"""
    global _client
    if _client is None:
        _client = KnowledgeServiceClient()
        logger.info("[KnowledgeServiceClient] 知识库客户端初始化成功")
    return _client
