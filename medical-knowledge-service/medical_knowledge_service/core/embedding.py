"""
Embedding 服务抽象
"""
from abc import ABC, abstractmethod
from typing import List


class EmbeddingService(ABC):
    """Embedding 服务抽象接口"""

    @abstractmethod
    async def encode(self, texts: List[str]) -> List[List[float]]:
        """
        批量编码文本为向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        pass

    @abstractmethod
    async def encode_single(self, text: str) -> List[float]:
        """
        编码单个文本

        Args:
            text: 文本

        Returns:
            向量
        """
        pass
