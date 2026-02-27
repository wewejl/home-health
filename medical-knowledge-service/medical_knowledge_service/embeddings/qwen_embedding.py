"""
阿里云千问 Embedding 服务（专用于中文）
"""
import httpx
import logging
from typing import List
from ..core import EmbeddingService

logger = logging.getLogger(__name__)


class QwenEmbedding(EmbeddingService):
    """阿里云千问 Embedding 服务（专用于中文）"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding",
        model: str = "text-embedding-v3",
        dimension: int = 1024,
        timeout: int = 60
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.dimension = dimension
        self.timeout = timeout

    async def encode(self, texts: List[str]) -> List[List[float]]:
        """批量编码（千问 API 一次处理一个文本）"""
        embeddings = []

        for i, text in enumerate(texts):
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 千问 API 格式
            payload = {
                "model": self.model,
                "input": {
                    "texts": [text]
                }
            }

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.base_url,
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    data = response.json()

                    # 千问返回格式
                    if "output" in data and "embeddings" in data["output"]:
                        embedding = data["output"]["embeddings"][0]["embedding"]
                        embeddings.append(embedding)
                    else:
                        logger.warning(f"[QwenEmbedding] 响应格式异常: {data}")
                        embeddings.append([0.0] * self.dimension)

            except Exception as e:
                logger.error(f"[QwenEmbedding] 编码失败 [{i+1}/{len(texts)}]: {e}")
                embeddings.append([0.0] * self.dimension)

        return embeddings

    async def encode_single(self, text: str) -> List[float]:
        """编码单个文本"""
        results = await self.encode([text])
        return results[0] if results else []
