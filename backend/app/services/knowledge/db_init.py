"""
知识库数据库初始化脚本

用于在 PostgreSQL 中初始化 pgvector 扩展和相关表结构
"""
from sqlalchemy import text
from ..database import SessionLocal


async def init_knowledge_tables():
    """初始化知识库表"""
    async with SessionLocal() as db:
        # 启用 pgvector 扩展
        await db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # 创建知识库向量表
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_vectors (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT NOT NULL,
                embedding vector(1024),
                metadata JSONB NOT NULL DEFAULT '{}',
                specialty TEXT NOT NULL DEFAULT 'general',
                source TEXT NOT NULL DEFAULT 'internal',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        # 创建元数据表
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_metadata (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                document_id UUID REFERENCES knowledge_vectors(id) ON DELETE CASCADE,
                key TEXT NOT NULL,
                value TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        # 创建向量索引
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS knowledge_vectors_embedding_idx
            ON knowledge_vectors
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """))

        # 创建 GIN 索引
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS knowledge_vectors_metadata_idx
            ON knowledge_vectors USING GIN (metadata)
        """))

        # 创建科室索引
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS knowledge_vectors_specialty_idx
            ON knowledge_vectors(specialty)
        """))

        # 创建更新时间触发器
        await db.execute(text("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
            END;
            $$ language plpgsql
        """))

        await db.execute(text("""
            CREATE TRIGGER update_knowledge_vectors_updated_at
                BEFORE UPDATE ON knowledge_vectors
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """))

        await db.commit()
        print("[KnowledgeDB] 知识库表初始化完成")


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_knowledge_tables())
