"""
医学知识库服务

独立的医学知识库向量检索服务，可被其他项目复用。

使用示例:
```python
from medical_knowledge_service import KnowledgeClient

# 异步客户端
client = KnowledgeClient(base_url="http://localhost:8200")
results = await client.search("湿疹的症状", specialty="dermatology")

# 同步客户端
from medical_knowledge_service import SyncKnowledgeClient
client = SyncKnowledgeClient(base_url="http://localhost:8200")
results = client.search("高血压的治疗")
```
"""

__version__ = "1.0.0"
__author__ = "Lingxi Health"

from .core import (
    VectorStore, Document, SearchResult, SearchOptions,
    EmbeddingService, EmbeddingConfig, VectorStoreConfig, KnowledgeConfig
)
from .knowledge_service import KnowledgeService
from .sdk import KnowledgeClient, SyncKnowledgeClient

__all__ = [
    # 核心
    "VectorStore",
    "Document",
    "SearchResult",
    "SearchOptions",
    "EmbeddingService",
    "EmbeddingConfig",
    "VectorStoreConfig",
    "KnowledgeConfig",
    # 服务
    "KnowledgeService",
    # SDK
    "KnowledgeClient",
    "SyncKnowledgeClient",
]
