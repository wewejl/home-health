"""
知识库服务模块

提供向量检索、元数据管理等功能
"""
from .core.vector_store import VectorStore, Document, SearchResult, SearchOptions
from .core.embedding import EmbeddingService
from .knowledge_service import KnowledgeService
from .client import KnowledgeServiceClient, get_knowledge_client

__all__ = [
    # 核心接口
    "VectorStore",
    "Document",
    "SearchResult",
    "SearchOptions",
    "EmbeddingService",
    # 嵌入式服务（已废弃，保留向后兼容）
    "KnowledgeService",
    # 独立服务客户端（新）
    "KnowledgeServiceClient",
    "get_knowledge_client",
]
