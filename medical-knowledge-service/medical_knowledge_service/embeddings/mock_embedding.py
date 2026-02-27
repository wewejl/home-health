"""
Mock Embedding 服务（用于开发测试）
"""
import hashlib
from typing import List

from ..core import EmbeddingService


class MockEmbedding(EmbeddingService):
    """Mock Embedding 服务，生成伪随机向量"""

    def __init__(self, dimension: int = 1024):
        self.dimension = dimension

    async def encode(self, texts: List[str]) -> List[List[float]]:
        """批量编码"""
        return [await self.encode_single(text) for text in texts]

    async def encode_single(self, text: str) -> List[float]:
        """编码单个文本"""
        # 使用多个哈希组合生成更好的分布
        hash1 = hashlib.sha256(text.encode()).digest()
        hash2 = hashlib.md5((text + "_salt").encode()).digest()

        combined = hash1 + hash2
        vector = []

        for i in range(self.dimension):
            byte_idx = i % len(combined)
            val = (combined[byte_idx] / 255.0 - 0.5) * 2
            vector.append(val)

        # L2 归一化
        norm = sum(x * x for x in vector) ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector
