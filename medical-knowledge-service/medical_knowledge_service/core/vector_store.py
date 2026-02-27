"""
向量存储抽象接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Document:
    """文档数据模型"""
    id: Optional[str] = None
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    specialty: str = "general"
    category: str = "general"
    created_at: Optional[datetime] = None


@dataclass
class SearchResult:
    """搜索结果数据模型"""
    document: Document
    score: float
    rank: int = 0


@dataclass
class SearchOptions:
    """搜索选项"""
    top_k: int = 5
    specialty: Optional[str] = None
    category: Optional[str] = None
    score_threshold: float = 0.0
    filters: Dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    """向量存储抽象接口"""

    @abstractmethod
    async def initialize(self) -> None:
        """初始化向量存储"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass

    @abstractmethod
    async def add_documents(
        self,
        documents: List[Document],
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        添加文档到向量存储

        Args:
            documents: 文档列表
            embeddings: 可选的预计算向量

        Returns:
            文档 ID 列表
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        options: Optional[SearchOptions] = None
    ) -> List[SearchResult]:
        """
        向量相似度搜索

        Args:
            query: 查询文本
            options: 搜索选项

        Returns:
            搜索结果列表
        """
        pass

    @abstractmethod
    async def delete_by_specialty(self, specialty: str) -> int:
        """
        按科室删除文档

        Args:
            specialty: 科室名称

        Returns:
            删除的文档数量
        """
        pass

    @abstractmethod
    async def get_document_count(self, specialty: Optional[str] = None) -> int:
        """
        获取文档数量

        Args:
            specialty: 可选的科室过滤

        Returns:
            文档数量
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭连接"""
        pass
