"""
向量存储抽象层

定义统一的向量存储接口，支持多种向量数据库实现
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Document:
    """知识文档"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """检索结果"""
    document_id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str = ""


@dataclass
class SearchOptions:
    """检索选项"""
    top_k: int = 5
    specialty: str = "general"
    min_score: float = 0.0
    filters: Dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    """向量存储抽象接口"""

    @abstractmethod
    async def initialize(self):
        """初始化向量存储"""
        pass

    @abstractmethod
    async def add_documents(
        self,
        documents: List[Document]
    ) -> List[str]:
        """
        添加文档到向量存储

        Returns:
            文档 ID 列表
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        options: SearchOptions
    ) -> List[SearchResult]:
        """
        向量相似度搜索

        Args:
            query: 查询文本
            options: 检索选项

        Returns:
            检索结果列表，按相似度降序排序
        """
        pass

    @abstractmethod
    async def delete(
        self,
        document_ids: List[str]
    ) -> int:
        """
        删除文档

        Returns:
            删除的文档数量
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """获取文档总数"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
