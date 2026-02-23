"""
Embedding 服务抽象层

支持多种 Embedding 模型
"""
from abc import ABC, abstractmethod
from typing import List
from .config import EmbeddingConfig


class EmbeddingService(ABC):
    """Embedding 服务抽象接口"""

    def __init__(self, config: EmbeddingConfig):
        self.config = config

    @abstractmethod
    async def encode(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        将文本编码为向量

        Args:
            texts: 文本列表

        Returns:
            向量列表，每个向量是 float 列表
        """
        pass

    @abstractmethod
    async def encode_single(
        self,
        text: str
    ) -> List[float]:
        """
        编码单个文本

        Args:
            text: 文本

        Returns:
            向量
        """
        pass

    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.config.dimension

    async def batch_encode(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        批量编码（自动分批）

        Args:
            texts: 文本列表
            batch_size: 每批大小

        Returns:
            向量列表
        """
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_vectors = await self.encode(batch)
            results.extend(batch_vectors)
        return results
