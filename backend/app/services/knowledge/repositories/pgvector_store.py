"""
Pgvector 向量存储实现

使用 PostgreSQL + pgvector 扩展实现向量存储
"""
import asyncpg
from typing import List, Dict, Any, Optional
import json
import uuid

from ..core.vector_store import VectorStore, Document, SearchResult, SearchOptions
from ..core.config import VectorStoreConfig


class PgvectorStore(VectorStore):
    """Pgvector 向量存储实现"""

    def __init__(self, config: VectorStoreConfig, dimension: int = 1024):
        self.config = config
        self.dimension = dimension
        self._pool = None

    async def initialize(self):
        """初始化数据库连接和表结构"""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.config.connection_string,
                min_size=2,
                max_size=10
            )

            # 创建扩展
            async with self._pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

                # 创建向量表
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.config.table_name} (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        content TEXT NOT NULL,
                        embedding vector({self.dimension}),
                        metadata JSONB NOT NULL DEFAULT '{{}}',
                        specialty TEXT NOT NULL DEFAULT 'general',
                        source TEXT NOT NULL DEFAULT 'internal',
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)

                # 创建元数据表
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.config.metadata_table_name} (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        document_id UUID REFERENCES {self.config.table_name}(id) ON DELETE CASCADE,
                        key TEXT NOT NULL,
                        value TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)

                # 创建向量索引（IVFFLAT）
                index_params = self.config.index_params or {"lists": 100}
                lists_value = index_params.get("lists", 100)
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {self.config.table_name}_embedding_idx
                    ON {self.config.table_name}
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = {lists_value})
                """)

                # 创建 GIN 索引用于元数据查询
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {self.config.table_name}_metadata_idx
                    ON {self.config.table_name}
                    USING GIN (metadata)
                """)

                # 创建科目索引
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {self.config.table_name}_specialty_idx
                    ON {self.config.table_name}(specialty)
                """)

                print(f"[PgvectorStore] 初始化完成: {self.config.table_name}")

    async def add_documents(
        self,
        documents: List[Document]
    ) -> List[str]:
        """添加文档"""
        document_ids = []

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                for doc in documents:
                    doc_id = doc.id or str(uuid.uuid4())

                    # 准备向量数据
                    if doc.embedding is None:
                        # 如果没有向量，需要先生成（这里暂时跳过）
                        continue

                    # 转换 metadata 为 JSON
                    metadata_json = json.dumps(doc.metadata, ensure_ascii=False)

                    # 插入数据
                    await conn.execute(
                        f"""
                        INSERT INTO {self.config.table_name}
                        (id, content, embedding, metadata, specialty, source)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        doc_id,
                        doc.content,
                        str(doc.embedding),
                        metadata_json,
                        doc.metadata.get("specialty", "general"),
                        doc.metadata.get("source", "internal")
                    )

                    document_ids.append(doc_id)

        return document_ids

    async def search(
        self,
        query: str,
        query_vector: List[float],
        options: SearchOptions
    ) -> List[SearchResult]:
        """向量相似度搜索"""
        if query_vector is None:
            return []

        results = []

        async with self._pool.acquire() as conn:
            # 构建查询参数
            params = []
            param_count = 0

            # 将向量转换为字符串格式
            vector_str = f"[{','.join(map(str, query_vector))}]"

            # 构建 WHERE 子句
            where_clauses = []
            if options.specialty:
                param_count += 1
                where_clauses.append(f"specialty = ${param_count}")
                params.append(options.specialty)

            # 添加元数据过滤
            for key, value in options.filters.items():
                param_count += 1
                where_clauses.append(f"metadata->>${param_count} = ${param_count + 1}")
                params.append(key)
                params.append(value)
                param_count += 1

            where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

            # 构建 LIMIT 参数
            param_count += 1
            limit_param = param_count
            params.append(options.top_k)

            query_sql = f"""
                SELECT id, content, metadata, specialty, source,
                       1 - (embedding <=> '{vector_str}'::vector) AS score
                FROM {self.config.table_name}
                WHERE {where_sql}
                ORDER BY embedding <=> '{vector_str}'::vector
                LIMIT ${limit_param}
            """

            rows = await conn.fetch(query_sql, *params)

            for row in rows:
                if row["score"] < options.min_score:
                    continue
                results.append(SearchResult(
                    document_id=str(row["id"]),
                    content=row["content"],
                    metadata=row["metadata"],
                    score=row["score"],
                    source=row.get("source", "")
                ))

        return results

    async def delete(
        self,
        document_ids: List[str]
    ) -> int:
        """删除文档"""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self.config.table_name} WHERE id = ANY($1::uuid[])",
                document_ids
            )
            return result.split()[-1]

    async def count(self) -> int:
        """获取文档总数"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(f"SELECT COUNT(*) FROM {self.config.table_name}")
            return int(row[0])

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    async def close(self):
        """关闭连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
