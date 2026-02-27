"""
OpenAI 兼容的 Embedding 服务
"""
import httpx
from typing import List, Optional

from ..core import EmbeddingService


class OpenAIEmbedding(EmbeddingService):
    """OpenAI 兼容的 Embedding 服务（支持 Qwen、通义千问等）"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "text-embedding-3-small",
        dimension: Optional[int] = None,
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dimension = dimension
        self.timeout = timeout

    async def encode(self, texts: List[str]) -> List[List[float]]:
        """批量编码"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "input": texts,
            "model": self.model
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json=data,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()

        # 提取向量
        embeddings = [item["embedding"] for item in result["data"]]

        # 如果指定了维度且模型支持截断
        if self.dimension and len(embeddings[0]) > self.dimension:
            embeddings = [emb[:self.dimension] for emb in embeddings]

        return embeddings

    async def encode_single(self, text: str) -> List[float]:
        """编码单个文本"""
        result = await self.encode([text])
        return result[0]
