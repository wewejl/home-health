"""
简单的 SDK 测试脚本
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_knowledge_service.sdk import KnowledgeClient
from medical_knowledge_service.core import KnowledgeConfig, EmbeddingConfig, VectorStoreConfig
from medical_knowledge_service.knowledge_service import KnowledgeService


async def test_service():
    """测试服务"""
    print("=" * 50)
    print("医学知识库服务测试")
    print("=" * 50)

    # 测试导入
    print("\n1. 测试模块导入...")
    try:
        from medical_knowledge_service import (
            KnowledgeClient,
            KnowledgeService,
            VectorStore,
            Document
        )
        print("   ✓ 模块导入成功")
    except ImportError as e:
        print(f"   ✗ 导入失败: {e}")
        return False

    # 测试配置
    print("\n2. 测试配置创建...")
    try:
        config = KnowledgeConfig(
            embedding=EmbeddingConfig(
                provider="mock",
                dimension=1024
            ),
            vector_store=VectorStoreConfig(
                provider="pgvector",
                connection_string="postgresql://postgres:postgres@localhost:5432/test"
            )
        )
        print("   ✓ 配置创建成功")
    except Exception as e:
        print(f"   ✗ 配置创建失败: {e}")
        return False

    # 测试客户端
    print("\n3. 测试 SDK 客户端...")
    try:
        client = KnowledgeClient(
            base_url="http://localhost:8200",
            api_key="test-key"
        )
        print("   ✓ SDK 客户端创建成功")
        print(f"   - base_url: {client.base_url}")
        print(f"   - timeout: {client.timeout}")
    except Exception as e:
        print(f"   ✗ SDK 客户端创建失败: {e}")
        return False

    # 测试数据加载器
    print("\n4. 测试数据加载器...")
    try:
        from medical_knowledge_service.loaders import load_icd10_documents
        documents = load_icd10_documents()
        print(f"   ✓ 数据加载成功，共 {len(documents)} 条")

        # 统计各科室
        specialty_count = {}
        for doc in documents:
            specialty_count[doc.specialty] = specialty_count.get(doc.specialty, 0) + 1

        print(f"   - 科室分布:")
        for specialty, count in specialty_count.items():
            print(f"     * {specialty}: {count} 条")

    except Exception as e:
        print(f"   ✗ 数据加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 50)
    print("所有测试通过！")
    print("=" * 50)

    return True


if __name__ == "__main__":
    success = asyncio.run(test_service())
    sys.exit(0 if success else 1)
