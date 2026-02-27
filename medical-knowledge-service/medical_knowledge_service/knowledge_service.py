"""
医学知识库服务核心类
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from .core import (
    VectorStore, Document, SearchResult, SearchOptions,
    EmbeddingService, KnowledgeConfig
)
from .stores import PgvectorStore
from .embeddings import MockEmbedding, OpenAIEmbedding, QwenEmbedding
from .loaders import load_icd10_documents


class KnowledgeService:
    """医学知识库服务"""

    def __init__(self, config: Optional[KnowledgeConfig] = None):
        """
        初始化知识库服务

        Args:
            config: 知识库配置
        """
        self.config = config or KnowledgeConfig()
        self._store: Optional[VectorStore] = None
        self._embedding: Optional[EmbeddingService] = None
        self._initialized = False

    async def initialize(self) -> None:
        """初始化服务"""
        if self._initialized:
            return

        # 初始化 Embedding 服务
        embedding_config = self.config.embedding
        if embedding_config.provider == "mock":
            self._embedding = MockEmbedding(dimension=embedding_config.dimension)
        elif embedding_config.provider == "qwen":
            self._embedding = QwenEmbedding(
                api_key=embedding_config.api_key or "",
                base_url=embedding_config.base_url,
                model=embedding_config.model,
                dimension=embedding_config.dimension,
                timeout=embedding_config.timeout
            )
        elif embedding_config.provider in ("openai", "dashscope"):
            self._embedding = OpenAIEmbedding(
                api_key=embedding_config.api_key or "",
                base_url=embedding_config.base_url,
                model=embedding_config.model,
                dimension=embedding_config.dimension,
                timeout=embedding_config.timeout
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {embedding_config.provider}")

        # 初始化向量存储
        store_config = self.config.vector_store
        if store_config.provider == "pgvector":
            self._store = PgvectorStore(
                connection_string=store_config.connection_string,
                table_name=store_config.table_name,
                dimension=embedding_config.dimension,
                index_type=store_config.index_type,
                index_params=store_config.index_params
            )
        else:
            raise ValueError(f"Unsupported vector store provider: {store_config.provider}")

        # 初始化存储
        await self._store.initialize()

        self._initialized = True

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        if not self._initialized:
            return {"status": "not_initialized"}

        store_healthy = await self._store.health_check()

        return {
            "status": "healthy" if store_healthy else "unhealthy",
            "store": store_healthy,
            "embedding_provider": self.config.embedding.provider,
            "vector_store_provider": self.config.vector_store.provider
        }

    async def load_data(self, force_reload: bool = False) -> Dict[str, int]:
        """
        加载知识库数据

        Args:
            force_reload: 是否强制重新加载

        Returns:
            各科室加载的文档数量
        """
        if not self._initialized:
            await self.initialize()

        # 加载 ICD-10 数据
        documents = load_icd10_documents()

        # 按科室分组
        specialty_docs: Dict[str, List[Document]] = {}
        for doc in documents:
            if doc.specialty not in specialty_docs:
                specialty_docs[doc.specialty] = []
            specialty_docs[doc.specialty].append(doc)

        # 如果不强制重新加载，检查是否已有数据
        if not force_reload:
            to_delete = []
            for specialty in specialty_docs:
                count = await self._store.get_document_count(specialty)
                if count > 0:
                    to_delete.append(specialty)
            for specialty in to_delete:
                del specialty_docs[specialty]

        # 加载文档
        loaded_counts: Dict[str, int] = {}
        for specialty, docs in specialty_docs.items():
            # 生成 embeddings
            texts = [doc.content for doc in docs]
            embeddings = await self._embedding.encode(texts)

            # 添加到存储
            await self._store.add_documents(docs, embeddings)

            loaded_counts[specialty] = len(docs)

        return loaded_counts

    async def search(
        self,
        query: str,
        specialty: Optional[str] = None,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> Dict[str, Any]:
        """
        搜索医学知识

        Args:
            query: 查询文本
            specialty: 可选的科室过滤
            top_k: 返回结果数量
            score_threshold: 相似度阈值

        Returns:
            搜索结果
        """
        if not self._initialized:
            await self.initialize()

        # 生成查询向量
        query_embedding = await self._embedding.encode_single(query)

        # 构建搜索选项
        options = SearchOptions(
            top_k=top_k,
            specialty=specialty,
            score_threshold=score_threshold
        )

        # 执行搜索
        results = await self._store.search(
            query=query,
            query_embedding=query_embedding,
            options=options
        )

        # 格式化结果
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.document.content,
                "metadata": result.document.metadata,
                "specialty": result.document.specialty,
                "score": round(result.score, 4),
                "rank": result.rank
            })

        return {
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results),
            "specialty": specialty
        }

    async def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        if not self._initialized:
            await self.initialize()

        total_count = await self._store.get_document_count()

        # 获取各科室文档数量
        specialty_counts: Dict[str, int] = {}
        for specialty in ["dermatology", "cardiology", "respiratory", "gastroenterology",
                          "neurology", "endocrinology", "orthopedics", "ophthalmology",
                          "otorhinolaryngology", "obstetrics_gynecology", "pediatrics"]:
            count = await self._store.get_document_count(specialty)
            if count > 0:
                specialty_counts[specialty] = count

        return {
            "total_documents": total_count,
            "by_specialty": specialty_counts,
            "embedding_dimension": self.config.embedding.dimension
        }

    async def close(self) -> None:
        """关闭服务"""
        if self._store:
            await self._store.close()
        self._initialized = False
