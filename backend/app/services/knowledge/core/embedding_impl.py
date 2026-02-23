"""
Embedding 服务实现

支持多种 Embedding 提供商
"""
import httpx
from typing import List
from .embedding import EmbeddingService
from .config import EmbeddingConfig
import asyncio


class OpenAIEmbedding(EmbeddingService):
    """OpenAI 兼容的 Embedding 服务"""

    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.openai.com/v1"
        self.model = config.model

    async def encode(self, texts: List[str]) -> List[List[float]]:
        """批量编码"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "input": texts
        }

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return [item["embedding"] for item in data["data"]]

    async def encode_single(self, text: str) -> List[float]:
        """编码单个文本"""
        results = await self.encode([text])
        return results[0] if results else []


class MockEmbedding(EmbeddingService):
    """模拟 Embedding 服务（用于开发测试）"""

    async def encode(self, texts: List[str]) -> List[List[float]]:
        """生成伪向量（仅用于测试）"""
        # 简单的哈希模拟
        import hashlib
        vectors = []
        dim = self.config.dimension

        for text in texts:
            # 使用文本的哈希值生成伪随机向量
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()

            # 扩展到指定维度
            vector = []
            for i in range(dim):
                # 使用不同字节组合生成 -1 到 1 之间的值
                byte_val = hash_bytes[i % len(hash_bytes)]
                normalized = (byte_val / 255.0) * 2 - 1
                vector.append(normalized)

            # 归一化
            norm = sum(v**2 for v in vector) ** 0.5
            if norm > 0:
                vector = [v / norm for v in vector]

            vectors.append(vector)

        return vectors

    async def encode_single(self, text: str) -> List[float]:
        results = await self.encode([text])
        return results[0] if results else []


def get_embedding_service(config: EmbeddingConfig) -> EmbeddingService:
    """获取 Embedding 服务实例"""
    if config.provider == "openai" and config.api_key:
        return OpenAIEmbedding(config)
    else:
        # 默认使用 Mock，后续可添加本地模型实现
        return MockEmbedding(config)
