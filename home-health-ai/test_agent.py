#!/usr/bin/env python3
"""
测试全科医生智能体（不依赖数据库）
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.general_practitioner import create_general_practitioner


async def test_agent():
    """测试全科医生智能体"""
    print("=" * 70)
    print("🏥 全科医生智能体测试 (AutoGen 0.7.5)")
    print("=" * 70)
    print()

    # 创建智能体
    print("📦 创建全科医生智能体...")
    agent = create_general_practitioner()
    print(f"✅ 智能体创建成功: {agent.name}")
    print()

    # 测试对话列表
    test_questions = [
        "你好，我是新来的患者",
        "我最近感觉头痛头晕，已经三天了",
        "高血压患者平时需要注意什么？",
        "阿司匹林有什么作用？怎么吃？",
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'─' * 70}")
        print(f"👤 患者 {i}: {question}")
        print(f"{'─' * 70}")

        try:
            # 调用智能体
            response = await agent.run(task=question)

            # 获取回复
            final_message = response.messages[-1]
            answer = final_message.content

            print(f"\n🤖 全科医生: {answer}")

        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 70)
    print("✅ 测试完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_agent())
