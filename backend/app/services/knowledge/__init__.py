"""
知识库服务模块

提供向量检索、元数据管理等功能
"""
from .core.vector_store import VectorStore, Document, SearchResult, SearchOptions
from .core.embedding import EmbeddingService
from .knowledge_service import KnowledgeService

__all__ = [
    "VectorStore",
    "Document",
    "SearchResult",
    "SearchOptions",
    "EmbeddingService",
    "KnowledgeService",
]
