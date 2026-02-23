"""
知识库配置
"""
from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class EmbeddingConfig:
    """Embedding 服务配置"""
    provider: str = "openai"  # openai, local, qwen
    model: str = "bge-large-zh-v1.5"
    dimension: int = 1024
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    batch_size: int = 32
    timeout: int = 30


@dataclass
class VectorStoreConfig:
    """向量存储配置"""
    provider: str = "pgvector"  # pgvector, milvus, faiss
    connection_string: str = ""
    table_name: str = "knowledge_vectors"
    metadata_table_name: str = "knowledge_metadata"
    index_type: str = "ivfflat"  # ivfflat, hnsw
    index_params: Dict = field(default_factory=lambda: {"lists": 100, "m": 16})


@dataclass
class KnowledgeConfig:
    """知识库配置"""
    embedding: EmbeddingConfig = None
    vector_store: VectorStoreConfig = None

    def __post_init__(self):
        if self.embedding is None:
            self.embedding = EmbeddingConfig()
        if self.vector_store is None:
            self.vector_store = VectorStoreConfig()
