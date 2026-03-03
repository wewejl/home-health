#!/usr/bin/env python3
"""
HIS 门诊 AI 助手 - 数据库基础测试
验证第一步：数据库基础搭建
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.connection import test_connection, get_connection
from src.db.session_manager import SessionManager


def test_database_connection():
    """测试 1: 数据库连接"""
    print("\n" + "="*70)
    print("📋 测试 1: 数据库连接")
    print("="*70)

    success = test_connection()
    return success


def test_agent_state_operations():
    """测试 2: Agent 状态保存和加载"""
    print("\n" + "="*70)
    print("📋 测试 2: Agent 状态保存和加载")
    print("="*70)

    try:
        mgr = SessionManager()

        # 模拟 AutoGen save_state() 返回的状态
        test_state = {
            "type": "AssistantAgentState",
            "version": "1.0.0",
            "llm_context": {
                "messages": [
                    {"source": "system", "content": "You are a helpful assistant."},
                    {"source": "user", "content": "你好，我叫张三"},
                    {"source": "assistant", "content": "你好张三！有什么可以帮助你的？"}
                ]
            }
        }

        # 测试保存
        print("\n💾 保存 Agent 状态...")
        mgr.save_agent_state(
            session_id="test_db_001",
            state=test_state,
            his_user_id="doctor_test",
            his_patient_id="patient_001"
        )
        print("✅ 状态保存成功")

        # 测试加载
        print("\n📥 加载 Agent 状态...")
        loaded_state = mgr.load_agent_state("test_db_001")

        if loaded_state == test_state:
            print("✅ 状态加载成功")
            print(f"   状态类型: {loaded_state.get('type')}")
            print(f"   版本: {loaded_state.get('version')}")
            print(f"   消息数: {len(loaded_state.get('llm_context', {}).get('messages', []))}")
        else:
            print("❌ 状态不一致")
            mgr.close()
            return False

        # 测试更新
        print("\n🔄 测试状态更新...")
        test_state["llm_context"]["messages"].append(
            {"source": "user", "content": "我今年30岁"}
        )
        mgr.save_agent_state("test_db_001", test_state, "doctor_test")

        updated_state = mgr.load_agent_state("test_db_001")
        if len(updated_state["llm_context"]["messages"]) == 4:
            print("✅ 状态更新成功")
            print(f"   新消息数: {len(updated_state['llm_context']['messages'])}")
        else:
            print("❌ 更新失败")
            mgr.close()
            return False

        mgr.close()
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chat_history_operations():
    """测试 3: 对话历史保存和查询"""
    print("\n" + "="*70)
    print("📋 测试 3: 对话历史保存和查询")
    print("="*70)

    try:
        mgr = SessionManager()

        # 保存对话
        print("\n💾 保存对话消息...")
        mgr.save_chat_message(
            session_id="test_db_002",
            his_user_id="doctor_test",
            role="user",
            content="这个患者有什么建议？"
        )
        mgr.save_chat_message(
            session_id="test_db_002",
            his_user_id="doctor_test",
            role="assistant",
            content="我需要先了解患者的具体情况。"
        )
        print("✅ 对话保存成功")

        # 查询对话
        print("\n📥 查询对话历史...")
        history = mgr.get_chat_history("test_db_002")

        if len(history) == 2:
            print("✅ 对话历史加载成功")
            for msg in history:
                role_icon = {"user": "👤", "assistant": "🤖", "system": "⚙️"}[msg["role"]]
                print(f"   {role_icon} {msg['content']}")
        else:
            print(f"❌ 消息数不正确: {len(history)}")
            mgr.close()
            return False

        mgr.close()
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_audit_log_operations():
    """测试 4: 审计日志"""
    print("\n" + "="*70)
    print("📋 测试 4: 审计日志")
    print("="*70)

    try:
        mgr = SessionManager()

        print("\n💾 保存审计日志...")
        mgr.save_audit_log(
            session_id="test_db_003",
            his_user_id="doctor_test",
            event_type="chat",
            event_data={"message_count": 2}
        )

        mgr.save_audit_log(
            session_id="test_db_003",
            his_user_id="doctor_test",
            event_type="tool_call",
            event_data={"tool": "get_patient_info", "patient_id": "123"}
        )

        print("✅ 审计日志保存成功")

        # 验证日志保存（通过查询数据库）
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM audit_logs WHERE session_id = %s", ("test_db_003",))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()

        if count == 2:
            print(f"✅ 审计日志验证成功: {count} 条记录")
        else:
            print(f"❌ 审计日志数量不正确: {count}")
            mgr.close()
            return False

        mgr.close()
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cross_table_consistency():
    """测试 5: 跨表一致性验证"""
    print("\n" + "="*70)
    print("📋 测试 5: 跨表一致性验证")
    print("="*70)

    try:
        mgr = SessionManager()

        # 模拟完整对话流程
        session_id = "test_db_full"

        print("\n🔄 模拟完整对话流程...")

        # 1. 保存对话
        mgr.save_chat_message(session_id, "doctor_test", "user", "你好")
        mgr.save_chat_message(session_id, "doctor_test", "assistant", "你好！")

        # 2. 保存 Agent 状态
        state = {
            "type": "AssistantAgentState",
            "version": "1.0.0",
            "llm_context": {
                "messages": [
                    {"source": "system", "content": "You are a helpful assistant."},
                    {"source": "user", "content": "你好"},
                    {"source": "assistant", "content": "你好！"}
                ]
            }
        }
        mgr.save_agent_state(session_id, state, "doctor_test", "patient_123")

        # 3. 保存审计日志
        mgr.save_audit_log(session_id, "doctor_test", "chat")

        print("✅ 数据保存完成")

        # 4. 验证数据一致性
        print("\n🔍 验证数据一致性...")

        conn = get_connection()
        cur = conn.cursor()

        # 检查 agent_states
        cur.execute("SELECT message_count FROM agent_states WHERE session_id = %s", (session_id,))
        msg_count = cur.fetchone()[0]
        print(f"   agent_states.message_count: {msg_count}")

        # 检查 chat_history
        cur.execute("SELECT COUNT(*) FROM chat_history WHERE session_id = %s", (session_id,))
        chat_count = cur.fetchone()[0]
        print(f"   chat_history 条数: {chat_count}")

        # 检查 audit_logs
        cur.execute("SELECT COUNT(*) FROM audit_logs WHERE session_id = %s", (session_id,))
        audit_count = cur.fetchone()[0]
        print(f"   audit_logs 条数: {audit_count}")

        cur.close()
        conn.close()

        if msg_count == 3 and chat_count == 2 and audit_count == 1:
            print("✅ 数据一致性验证成功")
            mgr.close()
            return True
        else:
            print("❌ 数据不一致")
            mgr.close()
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🧪 HIS 门诊 AI 助手 - 数据库基础测试套件               ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  验证内容：                                                  ║
║  1. 数据库连接                                              ║
║  2. Agent 状态保存和加载（核心功能）                        ║
║  3. 对话历史保存和查询                                      ║
║  4. 审计日志记录                                            ║
║  5. 跨表数据一致性                                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    results = []

    # 运行测试
    results.append(("数据库连接", test_database_connection()))
    results.append(("Agent 状态操作", test_agent_state_operations()))
    results.append(("对话历史操作", test_chat_history_operations()))
    results.append(("审计日志操作", test_audit_log_operations()))
    results.append(("跨表一致性", test_cross_table_consistency()))

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
        print("\n🎉 所有测试通过！数据库基础搭建完成。")
        print("\n✅ 第一步验收合格，可以进行下一步：单 Agent 实现")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置和依赖。")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 测试已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
