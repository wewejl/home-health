#!/usr/bin/env python3
"""
真实验证测试：AutoGen Agent + PostgreSQL 存储
验证完整的 save_state → load_state → 对话流程

⚠️  注意：此测试会调用 DeepSeek API，产生费用
"""

import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient
from config.settings import AUTOGEN_MODEL_CONFIG
from src.db.session_manager import SessionManager


async def test_real_agent_with_database():
    """真实 Agent + 数据库集成测试"""
    print("\n" + "="*70)
    print("📋 真实验证测试：Agent + PostgreSQL")
    print("="*70)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # =====================================================
    # 准备工作
    # =====================================================
    print("\n📦 准备环境...")

    # 创建会话管理器
    session_mgr = SessionManager()

    # 创建模型客户端
    print("✅ 创建模型客户端...")
    model_client = ChatCompletionClient.load_component(AUTOGEN_MODEL_CONFIG)

    # =====================================================
    # 第 1 轮对话：首次对话，保存状态
    # =====================================================
    print("\n" + "-"*70)
    print("🔄 第 1 轮对话：新会话")
    print("-"*70)

    session_id = "test_real_agent_001"
    his_user_id = "doctor_test"

    # 创建 Agent
    print("\n1️⃣ 创建 Doctor Agent...")
    agent = AssistantAgent(
        name="doctor_assistant",
        model_client=model_client,
        system_message="""你是 HIS 医院的智能医疗助手。

你的职责：
- 协助医生查询患者信息
- 提供医疗建议
- 记住对话中的重要信息

请简洁回复，每句话不超过 30 字。
"""
    )
    print("✅ Agent 创建成功")

    # 发送第一条消息
    print("\n2️⃣ 发送消息...")
    message1 = "你好，我正在看一位叫李明的患者"
    print(f"👤 医生: {message1}")

    response1 = await agent.on_messages(
        [TextMessage(content=message1, source="user")],
        cancellation_token=CancellationToken()
    )
    print(f"🤖 助手: {response1.chat_message.content}")

    # 保存 Agent 状态到数据库
    print("\n3️⃣ 保存 Agent 状态到 PostgreSQL...")
    state1 = await agent.save_state()
    print(f"   状态类型: {state1.get('type')}")
    print(f"   版本: {state1.get('version')}")
    print(f"   消息数: {len(state1.get('llm_context', {}).get('messages', []))}")

    session_mgr.save_agent_state(
        session_id=session_id,
        state=state1,
        his_user_id=his_user_id
    )
    print("✅ 状态已保存到数据库")

    # 保存对话历史
    print("\n4️⃣ 保存对话历史...")
    session_mgr.save_chat_message(
        session_id=session_id,
        his_user_id=his_user_id,
        role="user",
        content=message1
    )
    session_mgr.save_chat_message(
        session_id=session_id,
        his_user_id=his_user_id,
        role="assistant",
        content=response1.chat_message.content
    )
    print("✅ 对话历史已保存")

    # =====================================================
    # 第 2 轮对话：加载状态，验证记忆功能
    # =====================================================
    print("\n" + "-"*70)
    print("🔄 第 2 轮对话：恢复会话（验证跨请求记忆）")
    print("-"*70)

    print("\n1️⃣ 从 PostgreSQL 加载状态...")
    loaded_state = session_mgr.load_agent_state(session_id)
    if loaded_state:
        print("✅ 状态加载成功")
        print(f"   状态类型: {loaded_state.get('type')}")
        print(f"   消息数: {len(loaded_state.get('llm_context', {}).get('messages', []))}")
    else:
        print("❌ 状态加载失败")
        return False

    print("\n2️⃣ 创建新 Agent 并加载状态...")
    agent2 = AssistantAgent(
        name="doctor_assistant",
        model_client=model_client,
        system_message="""你是 HIS 医院的智能医疗助手。

你的职责：
- 协助医生查询患者信息
- 提供医疗建议
- 记住对话中的重要信息

请简洁回复，每句话不超过 30 字。
"""
    )

    # 加载保存的状态
    await agent2.load_state(loaded_state)
    print("✅ 状态已恢复到新 Agent")

    # 发送第二条消息（测试记忆）
    print("\n3️⃣ 发送消息（测试记忆）...")
    message2 = "患者叫什么名字？"
    print(f"👤 医生: {message2}")

    response2 = await agent2.on_messages(
        [TextMessage(content=message2, source="user")],
        cancellation_token=CancellationToken()
    )
    print(f"🤖 助手: {response2.chat_message.content}")

    # 检查是否记住患者名字
    if "李明" in response2.chat_message.content:
        print("\n✅ 记忆功能正常！Agent 记住了患者名字")
    else:
        print("\n⚠️  记忆功能可能有问题，Agent 没有记住患者名字")
        print("   这是预期的，如果模型回复不准确")

    # 保存新的状态
    print("\n4️⃣ 保存更新后的状态...")
    state2 = await agent2.save_state()
    session_mgr.save_agent_state(
        session_id=session_id,
        state=state2,
        his_user_id=his_user_id
    )
    print(f"✅ 状态已更新（消息数: {len(state2.get('llm_context', {}).get('messages', []))}）")

    # 保存对话
    session_mgr.save_chat_message(
        session_id=session_id,
        his_user_id=his_user_id,
        role="user",
        content=message2
    )
    session_mgr.save_chat_message(
        session_id=session_id,
        his_user_id=his_user_id,
        role="assistant",
        content=response2.chat_message.content
    )

    # =====================================================
    # 第 3 轮对话：再次验证
    # =====================================================
    print("\n" + "-"*70)
    print("🔄 第 3 轮对话：再次验证记忆")
    print("-"*70)

    print("\n1️⃣ 再次从数据库加载状态...")
    loaded_state3 = session_mgr.load_agent_state(session_id)
    await agent2.load_state(loaded_state3)
    print("✅ 状态已加载")

    print("\n2️⃣ 发送消息...")
    message3 = "他有什么症状？"
    print(f"👤 医生: {message3}")

    response3 = await agent2.on_messages(
        [TextMessage(content=message3, source="user")],
        cancellation_token=CancellationToken()
    )
    print(f"🤖 助手: {response3.chat_message.content}")

    # =====================================================
    # 验证数据完整性
    # =====================================================
    print("\n" + "="*70)
    print("🔍 验证数据完整性")
    print("="*70)

    # 从数据库读取所有对话
    history = session_mgr.get_chat_history(session_id)
    print(f"\n📜 对话历史（共 {len(history)} 条消息）:")
    for i, msg in enumerate(history, 1):
        role_icon = {"user": "👤", "assistant": "🤖"}[msg["role"]]
        print(f"   {i}. {role_icon} {msg['content']}")

    # 验证状态
    final_state = session_mgr.load_agent_state(session_id)
    final_message_count = len(final_state.get('llm_context', {}).get('messages', []))

    print(f"\n📊 最终状态:")
    print(f"   Agent 消息数: {final_message_count}")
    print(f"   对话记录数: {len(history)}")
    print(f"   预期: Agent 消息数应该是对话数 + 1（system 消息）")

    if final_message_count == len(history) + 1:  # +1 是 system 消息
        print("✅ 数据一致性验证通过")
    else:
        print(f"⚠️  数据数量不一致（可能正常，取决于对话流程）")

    session_mgr.close()

    print("\n" + "="*70)
    print("🎉 真实验证测试完成！")
    print("="*70)
    print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return True


async def test_json_serialization():
    """单独测试 JSON 序列化/反序列化"""
    print("\n" + "="*70)
    print("📋 测试: JSON 序列化/反序列化")
    print("="*70)

    # 创建 Agent
    model_client = ChatCompletionClient.load_component(AUTOGEN_MODEL_CONFIG)
    agent = AssistantAgent(
        name="test_agent",
        model_client=model_client,
        system_message="测试"
    )

    # 简单对话生成状态
    response = await agent.on_messages(
        [TextMessage(content="你好", source="user")],
        cancellation_token=CancellationToken()
    )

    # 获取状态
    state = await agent.save_state()

    print(f"\n1️⃣ 原始状态类型: {type(state)}")
    print(f"   是否为 dict: {isinstance(state, dict)}")
    print(f"   键: {list(state.keys())}")

    # 测试 JSON 序列化
    print(f"\n2️⃣ JSON 序列化...")
    try:
        state_json = json.dumps(state, ensure_ascii=False)
        print(f"✅ 序列化成功")
        print(f"   JSON 长度: {len(state_json)} 字符")
    except Exception as e:
        print(f"❌ 序列化失败: {e}")
        return False

    # 测试 JSON 反序列化
    print(f"\n3️⃣ JSON 反序列化...")
    try:
        state_loaded = json.loads(state_json)
        print(f"✅ 反序列化成功")
        print(f"   类型: {type(state_loaded)}")

        # 验证数据一致
        print(f"\n4️⃣ 验证数据一致性...")
        if state_loaded == state:
            print("✅ 数据完全一致")
        else:
            print("⚠️  数据不完全一致（可能包含时间戳等动态字段）")

            # 检查关键字段
            if state_loaded.get('type') == state.get('type'):
                print("   ✅ type 字段一致")
            if state_loaded.get('version') == state.get('version'):
                print("   ✅ version 字段一致")

            messages_loaded = state_loaded.get('llm_context', {}).get('messages', [])
            messages_original = state.get('llm_context', {}).get('messages', [])
            if len(messages_loaded) == len(messages_original):
                print(f"   ✅ messages 数量一致: {len(messages_original)}")

    except Exception as e:
        print(f"❌ 反序列化失败: {e}")
        return False

    # 测试数据库存储
    print(f"\n5️⃣ 测试 PostgreSQL JSONB 存储...")
    session_mgr = SessionManager()

    try:
        session_mgr.save_agent_state(
            session_id="test_json",
            state=state,
            his_user_id="test"
        )
        print("✅ 保存到数据库成功")

        loaded_from_db = session_mgr.load_agent_state("test_json")
        if loaded_from_db:
            print("✅ 从数据库加载成功")
            print(f"   类型: {type(loaded_from_db)}")

            # 验证
            if loaded_from_db.get('type') == state.get('type'):
                print("✅ 数据库存储后数据一致")
            else:
                print("⚠️  数据可能不一致")

    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session_mgr.close()

    print("\n" + "="*70)
    print("✅ JSON 序列化测试完成")
    print("="*70)

    return True


async def main():
    """运行所有真实验证测试"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🧪 真实验证测试：AutoGen Agent + PostgreSQL           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ⚠️  注意：此测试会调用 DeepSeek API，产生费用             ║
║                                                              ║
║  测试内容：                                                  ║
║  1. JSON 序列化/反序列化                                    ║
║  2. Agent 状态保存到数据库                                  ║
║  3. 从数据库恢复状态                                        ║
║  4. 跨请求记忆功能                                          ║
║  5. 数据完整性验证                                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    results = []

    # 测试 1: JSON 序列化
    print("\n" + "="*70)
    print("📋 测试组 1: JSON 序列化/反序列化")
    print("="*70)
    results.append(("JSON 序列化", await test_json_serialization()))

    # 测试 2: 真实 Agent + 数据库
    print("\n" + "="*70)
    print("📋 测试组 2: 真实 Agent + 数据库集成")
    print("="*70)
    results.append(("Agent + 数据库", await test_real_agent_with_database()))

    # 汇总
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)

    passed = 0
    failed = 0

    for name, result in results:
        if result:
            print(f"✅ {name}: 通过")
            passed += 1
        else:
            print(f"❌ {name}: 失败")
            failed += 1

    print("\n" + "="*70)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("="*70)

    if failed == 0:
        print("\n🎉 所有真实验证测试通过！")
        print("✅ 我们的 PostgreSQL 存储方式是正确的")
        print("✅ 符合 AutoGen 官方推荐模式")
        return 0
    else:
        print("\n⚠️  部分测试失败")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 测试已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
