"""
Pgvector 向量存储实现
"""
import hashlib
import json
import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core import VectorStore, Document, SearchResult, SearchOptions


class PgvectorStore(VectorStore):
    """PostgreSQL + pgvector 向量存储实现"""

    def __init__(
        self,
        connection_string: str,
        table_name: str = "knowledge_vectors",
        dimension: int = 1024,
        index_type: str = "ivfflat",
        index_params: Optional[Dict[str, Any]] = None
    ):
        self.connection_string = connection_string
        self.table_name = table_name
        self.dimension = dimension
        self.index_type = index_type
        self.index_params = index_params or {"lists": 100}
        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """初始化数据库连接和表结构"""
        self._pool = await asyncpg.create_pool(self.connection_string)

        async with self._pool.acquire() as conn:
            # 启用 pgvector 扩展
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # 创建向量表
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id VARCHAR(255) PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    embedding vector({self.dimension}),
                    specialty VARCHAR(100),
                    category VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # 创建索引
            await self._create_indexes(conn)

            # 创建全文搜索索引（使用简单的 'english' 配置作为后备）
            try:
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {self.table_name}_content_gin
                    ON {self.table_name} USING gin(to_tsvector('english', content))
                """)
            except Exception:
                # 如果全文搜索失败，忽略（向量搜索已足够）
                pass

            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_specialty
                ON {self.table_name}(specialty)
            """)

    async def _create_indexes(self, conn: asyncpg.Connection) -> None:
        """创建向量索引"""
        index_name = f"{self.table_name}_embedding_idx"

        # 检查索引是否存在
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_indexes
                WHERE tablename = $1 AND indexname = $2
            )
        """, self.table_name, index_name)

        if exists:
            return

        # 根据索引类型创建
        if self.index_type == "ivfflat":
            lists = self.index_params.get("lists", 100)
            await conn.execute(f"""
                CREATE INDEX {index_name}
                ON {self.table_name}
                USING ivfflat(embedding vector_cosine_ops)
                WITH (lists = {lists})
            """)
        elif self.index_type == "hnsw":
            m = self.index_params.get("m", 16)
            ef_construction = self.index_params.get("ef_construction", 64)
            await conn.execute(f"""
                CREATE INDEX {index_name}
                ON {self.table_name}
                USING hnsw(embedding vector_cosine_ops)
                WITH (m = {m}, ef_construction = {ef_construction})
            """)
        else:
            # 默认 cosine 操作符索引
            await conn.execute(f"""
                CREATE INDEX {index_name}
                ON {self.table_name} (embedding vector_cosine_ops)
            """)

    async def health_check(self) -> bool:
        """健康检查"""
        if not self._pool:
            return False
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception:
            return False

    def _generate_id(self, content: str, specialty: str) -> str:
        """生成文档唯一 ID"""
        unique_string = f"{specialty}:{content}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:32]

    async def add_documents(
        self,
        documents: List[Document],
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """添加文档"""
        if not self._pool:
            raise RuntimeError("Store not initialized")

        doc_ids = []

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                for i, doc in enumerate(documents):
                    # 生成 ID
                    doc_id = doc.id or self._generate_id(doc.content, doc.specialty)

                    # 获取向量
                    embedding = None
                    if embeddings and i < len(embeddings):
                        embedding = embeddings[i]
                    elif doc.embedding:
                        embedding = doc.embedding

                    # 转换向量为字符串格式
                    embedding_str = None
                    if embedding:
                        embedding_str = f"[{','.join(map(str, embedding))}]"

                    # UPSERT
                    await conn.execute(f"""
                        INSERT INTO {self.table_name} (id, content, metadata, embedding, specialty, category, created_at)
                        VALUES ($1, $2, $3, $4::vector, $5, $6, $7)
                        ON CONFLICT (id) DO UPDATE
                        SET content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding,
                            specialty = EXCLUDED.specialty,
                            category = EXCLUDED.category
                    """, doc_id, doc.content, json.dumps(doc.metadata), embedding_str,
                        doc.specialty, doc.category, doc.created_at or datetime.now())

                    doc_ids.append(doc_id)

        return doc_ids

    async def search(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        options: Optional[SearchOptions] = None
    ) -> List[SearchResult]:
        """向量搜索"""
        if not self._pool:
            raise RuntimeError("Store not initialized")

        opts = options or SearchOptions()

        # 构建查询条件
        conditions = []
        params = []
        param_count = 0

        if opts.specialty:
            param_count += 1
            conditions.append(f"specialty = ${param_count}")
            params.append(opts.specialty)

        if opts.category:
            param_count += 1
            conditions.append(f"category = ${param_count}")
            params.append(opts.category)

        # 元数据过滤
        for key, value in opts.filters.items():
            param_count += 1
            conditions.append(f"metadata->>${key} = ${param_count}")
            params.append(str(value))

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # 如果有查询向量，使用向量搜索；否则使用全文搜索
        if query_embedding:
            # 向量相似度搜索 - 直接在 SQL 中构建向量
            embedding_str = ",".join(map(str, query_embedding))
            param_count += 1
            params.append(opts.top_k)

            query_sql = f"""
                SELECT id, content, metadata, specialty, category,
                       1 - (embedding <=> '[{embedding_str}]'::vector) as score
                FROM {self.table_name}
                {where_clause}
                ORDER BY embedding <=> '[{embedding_str}]'::vector
                LIMIT cast(${param_count} as int)
            """
        else:
            # 全文搜索回退
            param_count += 1
            params.append(f"%{query}%")
            param_count += 1
            params.append(opts.top_k)

            query_sql = f"""
                SELECT id, content, metadata, specialty, category,
                       CASE WHEN content LIKE ${param_count-1} THEN 1.0 ELSE 0.5 END as score
                FROM {self.table_name}
                {where_clause}
                ORDER BY score DESC
                LIMIT cast(${param_count} as int)
            """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query_sql, *params)

        results = []
        for rank, row in enumerate(rows):
            # 解析 metadata
            metadata = row["metadata"]
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}

            doc = Document(
                id=row["id"],
                content=row["content"],
                metadata=metadata,
                specialty=row["specialty"],
                category=row["category"]
            )

            # 应用分数阈值
            score = float(row["score"])
            if score >= opts.score_threshold:
                results.append(SearchResult(document=doc, score=score, rank=rank))

        return results

    async def delete_by_specialty(self, specialty: str) -> int:
        """按科室删除"""
        if not self._pool:
            raise RuntimeError("Store not initialized")

        async with self._pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self.table_name} WHERE specialty = $1",
                specialty
            )
            return int(result.split()[-1]) if result else 0

    async def get_document_count(self, specialty: Optional[str] = None) -> int:
        """获取文档数量"""
        if not self._pool:
            raise RuntimeError("Store not initialized")

        async with self._pool.acquire() as conn:
            if specialty:
                count = await conn.fetchval(
                    f"SELECT COUNT(*) FROM {self.table_name} WHERE specialty = $1",
                    specialty
                )
            else:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.table_name}")

            return count or 0

    async def close(self) -> None:
        """关闭连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
