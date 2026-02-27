#!/usr/bin/env python3
"""
导入儿科数据到知识库

用法:
    python scripts/import_pediatrics.py          # 交互式确认
    python scripts/import_pediatrics.py --force  # 强制重新导入
    python scripts/import_pediatrics.py --skip   # 跳过已存在的数据
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from medical_knowledge_service.knowledge_service import KnowledgeService
from medical_knowledge_service.core import KnowledgeConfig, EmbeddingConfig, VectorStoreConfig
from medical_knowledge_service.loaders import load_pediatrics_documents


async def import_pediatrics_data(force=False, skip_existing=False, use_qwen=True):
    """导入儿科数据到向量知识库"""

    # 千问 API 密钥
    qwen_api_key = "sk-61e2b328d6614408867ac61240423740"

    # 创建配置
    if use_qwen:
        config = KnowledgeConfig(
            embedding=EmbeddingConfig(
                provider="qwen",
                api_key=qwen_api_key,
                base_url="https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding",
                model="text-embedding-v3",
                dimension=1024,
                timeout=60,
            ),
            vector_store=VectorStoreConfig(
                provider="pgvector",
                connection_string="postgresql://postgres:postgres@localhost:5434/medical_knowledge",
                table_name="knowledge_vectors",
            )
        )
    else:
        config = KnowledgeConfig(
            embedding=EmbeddingConfig(
                provider="mock",
                dimension=1024,
            ),
            vector_store=VectorStoreConfig(
                provider="pgvector",
                connection_string="postgresql://postgres:postgres@localhost:5434/medical_knowledge",
                table_name="knowledge_vectors",
            )
        )

    # 初始化服务
    print("初始化知识库服务...")
    service = KnowledgeService(config)
    await service.initialize()

    # 加载儿科数据
    print("\n加载儿科数据文件...")
    documents = load_pediatrics_documents()
    print(f"找到 {len(documents)} 条儿科文档")

    if not documents:
        print("没有找到儿科数据，请先运行爬虫")
        return

    # 检查现有数据
    existing_count = await service._store.get_document_count("pediatrics")
    print(f"\n当前数据库中儿科文档数: {existing_count}")

    if existing_count > 0 and not force:
        if skip_existing:
            print("跳过导入（已有数据）")
            await service.close()
            return
        else:
            # 清除现有数据
            print("清除现有儿科数据...")
            await service._store.delete_by_specialty("pediatrics")
            print("清除完成")

    if force and existing_count > 0:
        print("强制模式：清除现有儿科数据...")
        await service._store.delete_by_specialty("pediatrics")
        print("清除完成")

    # 导入数据
    print("\n开始导入数据...")
    texts = [doc.content for doc in documents]

    # 生成 embeddings
    print(f"生成 {len(texts)} 个向量...")
    embeddings = await service._embedding.encode(texts)
    print("向量生成完成")

    # 添加到存储
    print("添加到向量数据库...")
    await service._store.add_documents(documents, embeddings)
    print("导入完成！")

    # 验证
    new_count = await service._store.get_document_count("pediatrics")
    print(f"\n验证: 数据库中儿科文档数: {new_count}")

    # 获取统计信息
    stats = await service.get_stats()
    print(f"\n知识库统计:")
    print(f"  总文档数: {stats['total_documents']}")
    print(f"  各科室数据:")
    for specialty, count in stats['by_specialty'].items():
        print(f"    {specialty}: {count}")

    # 测试搜索
    print("\n测试搜索...")
    test_queries = [
        "儿童发烧怎么办",
        "新生儿黄疸",
        "小儿哮喘",
    ]

    for query in test_queries:
        print(f"\n查询: {query}")
        results = await service.search(query, specialty="pediatrics", top_k=3)
        for i, r in enumerate(results['results'][:2]):
            name = r['metadata'].get('name', 'N/A')
            score = r['score']
            print(f"  {i+1}. {name} (相似度: {score})")

    await service.close()
    print("\n导入完成！")


if __name__ == "__main__":
    force = "--force" in sys.argv
    skip_existing = "--skip" in sys.argv
    use_mock = "--mock" in sys.argv
    asyncio.run(import_pediatrics_data(force=force, skip_existing=skip_existing, use_qwen=not use_mock))
