"""
核心抽象接口
"""
from .vector_store import VectorStore, Document, SearchResult, SearchOptions
from .embedding import EmbeddingService
from .config import EmbeddingConfig, VectorStoreConfig, KnowledgeConfig

__all__ = [
    "VectorStore",
    "Document",
    "SearchResult",
    "SearchOptions",
    "EmbeddingService",
    "EmbeddingConfig",
    "VectorStoreConfig",
    "KnowledgeConfig",
]
