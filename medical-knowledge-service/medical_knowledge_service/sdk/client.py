"""
Python SDK 客户端
"""
import httpx
from typing import Optional, List, Dict, Any


class KnowledgeClient:
    """医学知识库服务 SDK 客户端"""

    def __init__(
        self,
        base_url: str = "http://localhost:8200",
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化客户端

        Args:
            base_url: 服务基础 URL
            api_key: API 密钥
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法
            path: 请求路径
            data: 请求体数据

        Returns:
            响应数据
        """
        url = f"{self.base_url}{path}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        return await self._request("GET", "/health")

    async def search(
        self,
        query: str,
        specialty: Optional[str] = None,
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
            搜索结果
        """
        data = {
            "query": query,
            "specialty": specialty,
            "top_k": top_k,
            "score_threshold": score_threshold
        }
        response = await self._request("POST", "/api/v1/search", data)
        return response.get("data", {})

    async def load_data(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载知识库数据

        Args:
            force_reload: 是否强制重新加载

        Returns:
            加载结果
        """
        data = {"force_reload": force_reload}
        response = await self._request("POST", "/api/v1/data/load", data)
        return response.get("data", {})

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取知识库统计信息

        Returns:
            统计信息
        """
        response = await self._request("GET", "/api/v1/stats")
        return response.get("data", {})

    async def list_specialties(self) -> List[Dict[str, Any]]:
        """
        获取支持的科室列表

        Returns:
            科室列表
        """
        response = await self._request("GET", "/api/v1/specialties")
        return response.get("data", [])


# 同步客户端（使用线程池）
class SyncKnowledgeClient:
    """同步版本的 SDK 客户端"""

    def __init__(
        self,
        base_url: str = "http://localhost:8200",
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化客户端

        Args:
            base_url: 服务基础 URL
            api_key: API 密钥
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.Client(timeout=self.timeout)

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def close(self):
        """关闭客户端"""
        self._client.close()

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        response = self._client.get(
            f"{self.base_url}/health",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def search(
        self,
        query: str,
        specialty: Optional[str] = None,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> Dict[str, Any]:
        """搜索医学知识"""
        data = {
            "query": query,
            "specialty": specialty,
            "top_k": top_k,
            "score_threshold": score_threshold
        }
        response = self._client.post(
            f"{self.base_url}/api/v1/search",
            json=data,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        response = self._client.get(
            f"{self.base_url}/api/v1/stats",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def list_specialties(self) -> List[Dict[str, Any]]:
        """获取科室列表"""
        response = self._client.get(
            f"{self.base_url}/api/v1/specialties",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json().get("data", [])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
