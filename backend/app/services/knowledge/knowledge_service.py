"""
知识库服务

对外提供统一的知识检索接口
"""
from typing import List, Dict, Any, Optional
from .core.vector_store import VectorStore, SearchResult, SearchOptions, Document
from .core.embedding import EmbeddingService
from .repositories.pgvector_store import PgvectorStore
from .core.embedding_impl import get_embedding_service
from .core.config import KnowledgeConfig
from app.config import get_settings


class KnowledgeService:
    """知识库服务（单例）"""

    _instance: Optional["KnowledgeService"] = None
    _vector_store: Optional[VectorStore] = None
    _embedding: Optional[EmbeddingService] = None

    def __init__(self, config: KnowledgeConfig = None):
        self.config = config or KnowledgeConfig()
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "KnowledgeService":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self):
        """初始化知识库服务"""
        if self._initialized:
            return

        # 初始化 Embedding 服务
        self._embedding = get_embedding_service(self.config.embedding)

        # 初始化向量存储
        from app.config import get_settings
        settings = get_settings()
        db_config = self.config.vector_store

        # 转换 SQLAlchemy URL 为 asyncpg 兼容格式
        db_url = str(settings.DATABASE_URL)
        # postgresql+psycopg://... -> postgresql://...
        db_url = db_url.replace('postgresql+psycopg://', 'postgresql://')
        db_config.connection_string = db_url

        self._vector_store = PgvectorStore(db_config)
        await self._vector_store.initialize()

        self._initialized = True
        print("[KnowledgeService] 知识库服务初始化完成")

    async def search(
        self,
        query: str,
        specialty: str = "general",
        top_k: int = 5,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        统一检索接口

        Args:
            query: 查询内容
            specialty: 科室类型
            top_k: 返回结果数量
            filters: 元数据过滤条件

        Returns:
            {
                "found": bool,
                "results": [...],
                "count": int,
                "query_used": str
            }
        """
        # 生成查询向量
        query_vector = await self._embedding.encode_single(query)

        # 构建检索选项
        options = SearchOptions(
            top_k=top_k,
            specialty=specialty,
            min_score=0.0,
            filters=filters or {}
        )

        # 执行检索
        results = await self._vector_store.search(query, query_vector, options)

        return {
            "found": len(results) > 0,
            "results": [
                {
                    "document_id": r.document_id,
                    "content": r.content,
                    "metadata": r.metadata,
                    "score": r.score,
                    "source": r.source
                }
                for r in results
            ],
            "count": len(results),
            "query_used": query
        }

    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        specialty: str = "general",
        source: str = "manual"
    ) -> str:
        """添加单个文档"""
        # 生成向量
        embedding = await self._embedding.encode_single(content)

        document = Document(
            id=None,
            content=content,
            metadata=metadata,
            embedding=embedding
        )

        ids = await self._vector_store.add_documents([document])
        return ids[0] if ids else ""

    async def add_documents_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """批量添加文档"""
        # 批量生成向量
        texts = [doc["content"] for doc in documents]
        embeddings = await self._embedding.batch_encode(texts)

        docs = [
            Document(
                id=doc.get("id"),
                content=doc["content"],
                metadata=doc.get("metadata", {}),
                embedding=embedding
            )
            for doc, embedding in zip(documents, embeddings)
        ]

        return await self._vector_store.add_documents(docs)

    async def count(self) -> int:
        """获取文档总数"""
        return await self._vector_store.count()

    async def health_check(self) -> bool:
        """健康检查"""
        if not self._initialized:
            return False
        return await self._vector_store.health_check()
