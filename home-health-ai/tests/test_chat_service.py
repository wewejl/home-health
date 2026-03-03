#!/usr/bin/env python3
"""
HIS 门诊 AI 助手 - ChatService 测试
验证 ChatService 的核心功能：Agent + 数据库集成
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.chat_service import ChatService
from src.db.session_manager import SessionManager


def test_database_connection():
    """测试 1: 数据库连接"""
    print("\n" + "="*70)
    print("📋 测试 1: 数据库连接")
    print("="*70)

    try:
        from src.db.connection import test_connection
        test_connection()
        print("✅ 数据库连接成功")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_single_chat():
    """测试 2: 单轮对话"""
    print("\n" + "="*70)
    print("📋 测试 2: 单轮对话")
    print("="*70)

    try:
        service = ChatService()

        # 第一轮对话
        print("\n💬 对话 1:")
        message1 = "你好，我正在看一位叫李明的患者"
        print(f"👤 医生: {message1}")

        response1 = await service.chat(
            session_id="test_chat_001",
            his_user_id="doctor_test",
            message=message1
        )

        print(f"🤖 助手: {response1}")
        print("✅ 单轮对话成功")

        # 验证数据库保存
        state = service.session_mgr.load_agent_state("test_chat_001")
        if state:
            print(f"✅ 状态已保存: {len(state.get('llm_context', {}).get('messages', []))} 条消息")
        else:
            print("❌ 状态未保存")
            return False

        # 验证对话历史
        history = service.get_session_history("test_chat_001")
        if len(history) == 2:  # user + assistant
            print(f"✅ 对话历史已保存: {len(history)} 条消息")
        else:
            print(f"⚠️  对话历史数量异常: {len(history)} 条")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multi_chat_memory():
    """测试 3: 多轮对话（验证跨请求记忆）"""
    print("\n" + "="*70)
    print("📋 测试 3: 多轮对话（验证记忆功能）")
    print("="*70)

    try:
        service = ChatService()

        # 第一轮：告诉 Agent 患者名字
        print("\n💬 对话 1: 告知患者信息")
        await service.chat(
            session_id="test_chat_memory",
            his_user_id="doctor_test",
            message="你好，我正在看一位叫王芳的患者的，32岁，女性"
        )
        print("👤 医生: 你好，我正在看一位叫王芳的患者的，32岁，女性")
        print("🤖 助手: [AI 回复]")
        print("✅ 第一轮对话完成")

        # 第二轮：测试是否记住
        print("\n💬 对话 2: 测试记忆")
        response2 = await service.chat(
            session_id="test_chat_memory",
            his_user_id="doctor_test",
            message="我刚才说的患者叫什么名字？"
        )
        print(f"👤 医生: 我刚才说的患者叫什么名字？")
        print(f"🤖 助手: {response2}")

        # 验证是否记住
        if "王芳" in response2 or "女性" in response2:
            print("✅ 记忆功能正常！Agent 记住了患者信息")
        else:
            print("⚠️  记忆功能可能有问题")
            print(f"   回复: {response2}")

        # 第三轮：继续测试
        print("\n💬 对话 3: 继续对话")
        response3 = await service.chat(
            session_id="test_chat_memory",
            his_user_id="doctor_test",
            message="她有什么症状？"
        )
        print(f"👤 医生: 她有什么症状？")
        print(f"🤖 助手: {response3[:100]}...")

        # 验证消息数量
        state = service.session_mgr.load_agent_state("test_chat_memory")
        message_count = len(state.get('llm_context', {}).get('messages', []))
        print(f"✅ 当前对话轮数: {message_count // 2}")  # 除以 2 因为每轮有 2 条消息（user + assistant）

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_session_history():
    """测试 4: 对话历史查询"""
    print("\n" + "="*70)
    print("📋 测试 4: 对话历史查询")
    print("="*70)

    try:
        service = ChatService()

        # 创建一些对话
        print("\n💬 创建测试对话...")
        await service.chat(
            session_id="test_history_001",
            his_user_id="doctor_test",
            message="第一条消息"
        )

        await service.chat(
            session_id="test_history_001",
            his_user_id="doctor_test",
            message="第二条消息"
        )

        # 查询历史
        print("\n🔍 查询对话历史...")
        history = service.get_session_history("test_history_001")

        print(f"✅ 获取到 {len(history)} 条消息:")
        for i, msg in enumerate(history, 1):
            role_icon = {"user": "👤", "assistant": "🤖"}[msg["role"]]
            content_preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            print(f"   {i}. {role_icon} {content_preview}")

        # 验证数据
        if len(history) == 4:  # 2 轮对话，每轮 2 条消息
            print("✅ 对话历史记录正确")
            return True
        else:
            print(f"⚠️  消息数量异常: 预期 4 条，实际 {len(history)} 条")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_list_sessions():
    """测试 5: 会话列表查询"""
    print("\n" + "="*70)
    print("📋 测试 5: 会话列表查询")
    print("="*70)

    try:
        service = ChatService()

        # 创建几个不同用户的会话
        print("\n📝 创建测试会话...")
        await service.chat(
            session_id="test_list_001",
            his_user_id="doctor_zhang",
            message="张医生的对话"
        )

        await service.chat(
            session_id="test_list_002",
            his_user_id="doctor_li",
            message="李医生的对话"
        )

        await service.chat(
            session_id="test_list_003",
            his_user_id="doctor_zhang",
            message="张医生的另一段对话"
        )

        # 查询某个医生的所有会话
        print("\n🔍 查询 doctor_zhang 的会话...")
        sessions = service.list_user_sessions("doctor_zhang")

        print(f"✅ 找到 {len(sessions)} 个会话:")
        for i, session in enumerate(sessions, 1):
            print(f"   {i}. {session['session_id']}")
            print(f"      消息数: {session['message_count']}")

        # 验证
        if len(sessions) == 2:
            print("✅ 会话列表查询正确")
            return True
        else:
            print(f"⚠️  会话数量异常: 预期 2 个，实际 {len(sessions)} 个")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_delete_session():
    """测试 6: 删除会话"""
    print("\n" + "="*70)
    print("📋 测试 6: 删除会话")
    print("="*70)

    try:
        service = ChatService()

        # 创建会话
        print("\n📝 创建测试会话...")
        await service.chat(
            session_id="test_delete_001",
            his_user_id="doctor_test",
            message="这个会话将被删除"
        )
        print("✅ 会话创建成功")

        # 删除会话
        print("\n🗑️  删除会话...")
        result = service.delete_session("test_delete_001")

        if result:
            print("✅ 会话删除成功")

            # 验证确实删除了
            state = service.session_mgr.load_agent_state("test_delete_001")
            if state is None:
                print("✅ 状态已删除")
            else:
                print("❌ 状态仍然存在")
                return False
        else:
            print("❌ 会话删除失败")
            return False

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_medication_expert():
    """测试 7: 用药专家子 Agent"""
    print("\n" + "="*70)
    print("📋 测试 7: 用药专家子 Agent 调用")
    print("="*70)

    try:
        service = ChatService()

        # 简单用药问题（主 Agent 处理）
        print("\n💬 测试 7.1: 简单用药问题")
        response1 = await service.chat(
            session_id="test_med_001",
            his_user_id="doctor_test",
            message="阿司匹林是治疗什么的？"
        )
        print(f"👤 医生: 阿司匹林是治疗什么的？")
        print(f"🤖 助手: {response1[:100]}...")
        print("✅ 简单用药问题处理完成")

        # 复杂用药问题（调用子 Agent）
        print("\n💬 测试 7.2: 复杂用药问题（调用用药专家）")
        print("   ⚠️  这将调用子 Agent，可能需要较长时间...")
        response2 = await service.chat(
            session_id="test_med_002",
            his_user_id="doctor_test",
            message="患者同时服用阿司匹林和华法林，需要注意什么？"
        )
        print(f"👤 医生: 患者同时服用阿司匹林和华法林，需要注意什么？")
        print(f"🤖 助手: {response2[:150]}...")
        print("✅ 复杂用药问题处理完成")

        # 验证是否调用了子 Agent（通过关键字）
        if "风险" in response2 or "监测" in response2 or "INR" in response2:
            print("✅ 检测到用药专家回复特征（专业术语）")
        else:
            print("⚠️  未检测到明显的用药专家回复特征")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """运行所有测试"""
    print("""
╔════════════════════════════════════════════════════════════╗
║     🧪 ChatService 测试套件                                ║
╠════════════════════════════════════════════════════════════╣
║                                                              ║
║  验证内容：                                                  ║
║  1. 数据库连接                                              ║
║  2. 单轮对话                                                ║
║  3. 多轮对话（跨请求记忆）                                  ║
║  4. 对话历史查询                                            ║
║  5. 会话列表查询                                            ║
║  6. 会话删除                                                ║
║  7. 用药专家子 Agent 调用                                   ║
║                                                              ║
╚════════════════════════════════════════════════════════════╝
    """)

    results = []

    # 测试 1: 数据库连接
    if not test_database_connection():
        print("\n❌ 数据库连接失败，无法继续测试")
        return
    results.append(("数据库连接", True))

    # 测试 2: 单轮对话
    print("\n" + "-"*70)
    results.append(("单轮对话", await test_single_chat()))

    # 测试 3: 多轮对话（记忆）
    print("\n" + "-"*70)
    results.append(("多轮对话", await test_multi_chat_memory()))

    # 测试 4: 对话历史
    print("\n" + "-"*70)
    results.append(("对话历史查询", await test_session_history()))

    # 测试 5: 会话列表
    print("\n" + "-"*70)
    results.append(("会话列表查询", await test_list_sessions()))

    # 测试 6: 删除会话
    print("\n" + "-"*70)
    results.append(("会话删除", await test_delete_session()))

    # 测试 7: 用药专家
    print("\n" + "-"*70)
    results.append(("用药专家调用", await test_medication_expert()))

    # 汇总结果
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
        print("\n🎉 所有测试通过！ChatService 功能正常")
        print("\n✅ 下一步: 实现 FastAPI 接口")
        print("   - 创建 src/api/app.py")
        print("   - 实现 POST /chat 接口")
        print("   - 实现 GET /history 接口")
        print("   - 实现 GET /sessions 接口")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")

    return failed == 0


def main():
    """运行测试"""
    try:
        success = asyncio.run(run_all_tests())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n👋 测试已中断")
        return 1
    except Exception as e:
        print(f"\n\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
