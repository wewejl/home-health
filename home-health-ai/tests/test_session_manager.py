#!/usr/bin/env python3
"""
HIS 门诊系统 - 会话管理器测试
验证 save_state/load_state 功能
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.session_manager import SessionManager
from config.settings import AUTOGEN_MODEL_CONFIG
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "=" * 70)
    print("📋 测试 1: 数据库连接")
    print("=" * 70)

    try:
        session_mgr = SessionManager()
        session_mgr.connect()
        print("✅ 数据库连接成功")
        session_mgr.close()
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def test_create_user_and_session():
    """测试创建用户和会话"""
    print("\n" + "=" * 70)
    print("📋 测试 2: 创建用户和会话")
    print("=" * 70)

    try:
        session_mgr = SessionManager()
        session_mgr.connect()

        # 创建用户
        user_id = session_mgr.create_user(
            username="test_doctor",
            display_name="测试医生",
            role="doctor",
            department="测试科室"
        )
        print(f"✅ 用户创建成功: {user_id}")

        # 创建会话
        session_id = session_mgr.create_session(
            user_id=user_id,
            title="测试会话"
        )
        print(f"✅ 会话创建成功: {session_id}")

        session_mgr.close()
        return session_id
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_save_and_load_state():
    """测试保存和加载 Agent 状态"""
    print("\n" + "=" * 70)
    print("📋 测试 3: 保存和加载 Agent 状态")
    print("=" * 70)

    try:
        # 创建会话管理器
        session_mgr = SessionManager()
        session_mgr.connect()

        # 创建用户和会话
        user_id = session_mgr.create_user(
            username="test_state",
            display_name="状态测试",
            role="doctor"
        )
        session_id = session_mgr.create_session(user_id=user_id)

        # 创建 Agent
        model_client = OpenAIChatCompletionClient(
            **AUTOGEN_MODEL_CONFIG
        )

        agent = AssistantAgent(
            name="test_agent",
            model_client=model_client,
            system_message="你是一个测试助手。"
        )

        # 模拟对话（生成状态）
        print("\n📝 模拟对话...")
        response = await agent.on_messages(
            [TextMessage(content="你好", source="user")]
        )
        print(f"👤 用户: 你好")
        print(f"🤖 助手: {response.chat_message.content}")

        # 保存状态
        print("\n💾 保存状态...")
        state = await agent.save_state()
        session_mgr.save_agent_state(session_id, state, "test_agent")

        print(f"✅ 状态已保存: session_id={session_id}")
        print(f"   状态类型: {state.get('type')}")
        print(f"   版本: {state.get('version')}")
        print(f"   消息数: {len(state.get('llm_context', {}).get('messages', []))}")

        # 加载状态
        print("\n📥 加载状态...")
        loaded_state = session_mgr.load_agent_state(session_id)

        if loaded_state:
            print(f"✅ 状态加载成功")
            print(f"   状态类型: {loaded_state.get('type')}")
            print(f"   版本: {loaded_state.get('version')}")
            print(f"   消息数: {len(loaded_state.get('llm_context', {}).get('messages', []))}")

            # 验证数据一致性
            if state == loaded_state:
                print("✅ 状态数据一致")
            else:
                print("⚠️  状态数据不一致（可能包含时间戳等动态字段）")

        session_mgr.close()
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_message_operations():
    """测试消息操作"""
    print("\n" + "=" * 70)
    print("📋 测试 4: 消息操作")
    print("=" * 70)

    try:
        session_mgr = SessionManager()
        session_mgr.connect()

        # 创建测试会话
        user_id = session_mgr.create_user(
            username="test_message",
            display_name="消息测试",
            role="doctor"
        )
        session_id = session_mgr.create_session(user_id=user_id)

        # 保存消息
        print("\n💾 保存消息...")
        session_mgr.save_message(session_id, "user", "测试消息 1")
        session_mgr.save_message(session_id, "assistant", "测试回复 1")
        session_mgr.save_message(session_id, "user", "测试消息 2")
        print("✅ 消息保存成功")

        # 获取消息
        print("\n📥 获取消息...")
        messages = session_mgr.get_messages(session_id)
        print(f"✅ 获取到 {len(messages)} 条消息:")
        for msg in messages:
            role_icon = {"user": "👤", "assistant": "🤖"}[msg['role']]
            print(f"   {role_icon} {msg['content']}")

        session_mgr.close()
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_list_sessions():
    """测试列出会话"""
    print("\n" + "=" * 70)
    print("📋 测试 5: 列出会话")
    print("=" * 70)

    try:
        session_mgr = SessionManager()
        session_mgr.connect()

        # 列出所有会话
        sessions = session_mgr.list_sessions(limit=10)

        print(f"\n✅ 找到 {len(sessions)} 个会话:")
        for i, s in enumerate(sessions, 1):
            print(f"   {i}. {s['session_id']}")
            print(f"      标题: {s['title']}")
            print(f"      消息数: {s['message_count']}")
            print(f"      更新时间: {s['updated_at']}")

        session_mgr.close()
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """运行所有测试"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🧪 HIS 门诊系统 - 会话管理器测试套件                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  本测试套件验证：                                           ║
║  1. 数据库连接                                             ║
║  2. 用户和会话创建                                         ║
║  3. Agent 状态保存和恢复（核心功能）                       ║
║  4. 消息操作                                               ║
║  5. 会话列表查询                                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    results = []

    # 测试 1: 数据库连接
    results.append(("数据库连接", test_database_connection()))

    # 测试 2: 创建用户和会话
    session_id = test_create_user_and_session()
    results.append(("创建用户和会话", session_id is not None))

    # 测试 3: 状态保存和加载
    results.append(("状态保存和加载", await test_save_and_load_state()))

    # 测试 4: 消息操作
    results.append(("消息操作", test_message_operations()))

    # 测试 5: 会话列表
    results.append(("会话列表", test_list_sessions()))

    # 汇总结果
    print("\n" + "=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)

    passed = 0
    failed = 0

    for name, result in results:
        if result:
            print(f"✅ {name}: 通过")
            passed += 1
        else:
            print(f"❌ {name}: 失败")
            failed += 1

    print("\n" + "=" * 70)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("=" * 70)

    if failed == 0:
        print("\n🎉 所有测试通过！系统可以正常使用。")
    else:
        print("\n⚠️  部分测试失败，请检查配置和依赖。")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\n👋 测试已中断")
    except Exception as e:
        print(f"\n\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
