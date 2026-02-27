"""
测试独立知识库服务客户端
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_knowledge_client():
    """测试知识库客户端"""
    print("=" * 60)
    print("测试独立知识库服务客户端")
    print("=" * 60)

    try:
        from app.services.knowledge.client import get_knowledge_client
        print("\n✓ 客户端导入成功")
    except ImportError as e:
        print(f"\n✗ 导入失败: {e}")
        return False

    # 获取客户端
    client = get_knowledge_client()
    print(f"✓ 客户端初始化成功")
    print(f"  - 服务地址: {client.base_url}")
    print(f"  - 超时时间: {client.timeout}s")

    # 测试连接
    print("\n--- 测试连接 ---")
    try:
        health = await client.health_check()
        print(f"健康检查结果: {health}")
        if health.get("status") == "healthy":
            print("✓ 服务健康")
        else:
            print("⚠ 服务未就绪，继续测试...")
    except Exception as e:
        print(f"⚠ 健康检查失败: {e}")
        print("提示: 请先启动知识库服务")
        return False

    # 测试搜索
    print("\n--- 测试搜索 ---")
    try:
        result = await client.search(
            query="湿疹的症状",
            specialty="dermatology",
            top_k=3
        )

        print(f"搜索结果:")
        print(f"  - 找到: {result.get('count', 0)} 条")
        print(f"  - 查询: {result.get('query_used', 'N/A')}")

        if result.get("results"):
            print(f"\n第一条结果:")
            first = result["results"][0]
            content = first.get("content", "")
            print(f"  {content[:200]}...")

    except Exception as e:
        print(f"✗ 搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 测试 stats
    print("\n--- 测试统计 ---")
    try:
        stats = await client.get_stats()
        print(f"知识库统计:")
        print(f"  - 总文档数: {stats.get('total_documents', 0)}")
        print(f"  - 按科室分布: {stats.get('by_specialty', {})}")
    except Exception as e:
        print(f"⚠ 获取统计失败: {e}")

    # 关闭客户端
    await client.close()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_knowledge_client())
    sys.exit(0 if success else 1)
