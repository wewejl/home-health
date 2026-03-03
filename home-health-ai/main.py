#!/usr/bin/env python3
"""
全科医生智能体系统 - 主程序
基于 Microsoft AutoGen 0.7.5 官方 API

官方文档: https://github.com/microsoft/autogen
"""

import asyncio
import sys
import uuid
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from src.db.session_manager import SessionManager
from src.agents.general_practitioner import create_general_practitioner


# ============================================
# 主应用程序
# ============================================

class GeneralPractitionerApp:
    """全科医生智能体应用"""

    def __init__(self):
        self.session_mgr = SessionManager()
        self.agent = None
        self.current_session_id = None
        self.current_user_id = "doctor_zhang"  # 简化：固定用户ID

    async def initialize(self):
        """初始化应用"""
        print("=" * 70)
        print("🏥 全科医生智能体系统 (AutoGen 0.7.5)")
        print("=" * 70)

        # 显示历史会话
        sessions = self.session_mgr.list_sessions(self.current_user_id, limit=5)

        if sessions:
            print("\n💡 发现历史会话:")
            for i, s in enumerate(sessions, 1):
                print(f"   {i}. {s['session_id']} ({s['message_count']} 条消息, {s['updated_at']})")
            print(f"   使用命令: /resume {sessions[0]['session_id']}")

        # 创建新会话 ID
        self.current_session_id = f"session_{uuid.uuid4().hex[:12]}"

        print(f"\n💾 当前会话 ID: {self.current_session_id}")

        # 创建全科医生智能体
        self.agent = create_general_practitioner()

        # 尝试加载历史状态
        state = self.session_mgr.load_agent_state(self.current_session_id)

        if state:
            print("📜 检测到历史对话，正在恢复...")
            await self.agent.load_state(state)
            print("✅ 对话历史已恢复")
        else:
            print("🆕 新会话已创建")

        print("\n" + "=" * 70)
        print("💬 输入消息开始对话（输入 /help 查看命令）")
        print("=" * 70 + "\n")

    async def run(self):
        """运行主循环"""
        await self.initialize()

        while True:
            try:
                # 读取用户输入
                user_input = input("👤 您: ").strip()

                if not user_input:
                    continue

                # 处理命令
                if await self.handle_command(user_input):
                    continue

                # 保存用户消息
                self.session_mgr.save_chat_message(
                    session_id=self.current_session_id,
                    his_user_id=self.current_user_id,
                    role="user",
                    content=user_input
                )

                # 调用全科医生智能体
                print("\n🤖 全科医生响应中...\n")

                response = await self.agent.run(
                    task=user_input,
                )

                # 获取最终回复
                final_message = response.messages[-1]
                assistant_response = final_message.content

                print(f"🤖 全科医生: {assistant_response}\n")

                # 保存助手回复
                self.session_mgr.save_chat_message(
                    session_id=self.current_session_id,
                    his_user_id=self.current_user_id,
                    role="assistant",
                    content=assistant_response
                )

                # 保存智能体状态
                state = await self.agent.save_state()
                self.session_mgr.save_agent_state(
                    session_id=self.current_session_id,
                    state=state,
                    his_user_id=self.current_user_id
                )

            except KeyboardInterrupt:
                print("\n\n👋 程序已退出")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}\n")
                import traceback
                traceback.print_exc()

    async def handle_command(self, user_input: str) -> bool:
        """
        处理命令

        Args:
            user_input: 用户输入

        Returns:
            是否是命令（已处理）
        """
        if user_input == "/quit":
            print("\n👋 再见！所有对话已保存到数据库。")
            print(f"💾 您的会话 ID: {self.current_session_id}")
            print(f"💡 下次使用 /resume {self.current_session_id} 恢复对话\n")
            self.session_mgr.close()
            raise KeyboardInterrupt

        elif user_input == "/help":
            print("""
📖 可用命令:
  /help      - 显示帮助信息
  /new       - 创建新会话
  /sessions  - 查看所有会话
  /resume <session_id> - 恢复指定会话
  /history   - 查看当前会话历史
  /save      - 手动保存会话
  /quit      - 退出程序
""")
            return True

        elif user_input == "/new":
            self.current_session_id = f"session_{uuid.uuid4().hex[:12]}"
            print(f"\n💾 新会话 ID: {self.current_session_id}\n")
            return True

        elif user_input == "/sessions":
            sessions = self.session_mgr.list_sessions(self.current_user_id)
            print("\n📋 所有会话:")
            for i, s in enumerate(sessions, 1):
                print(f"   {i}. {s['session_id']} ({s['message_count']} 条, {s['updated_at']})")
            print()
            return True

        elif user_input.startswith("/resume "):
            old_session_id = user_input.split(" ", 1)[1]
            state = self.session_mgr.load_agent_state(old_session_id)

            if state:
                self.current_session_id = old_session_id
                print(f"\n✅ 会话已恢复: {old_session_id}")

                # 重新加载智能体状态
                await self.agent.load_state(state)

                # 显示历史
                messages = self.session_mgr.get_chat_history(old_session_id)
                if messages:
                    print("\n📜 对话历史:")
                    for msg in messages[-5:]:  # 只显示最近 5 条
                        role_icon = {"user": "👤 您", "assistant": "🤖 AI"}[msg['role']]
                        print(f"{role_icon}: {msg['content']}")
                print()

            return True

        elif user_input == "/history":
            messages = self.session_mgr.get_chat_history(self.current_session_id)
            print("\n📜 当前会话历史:")
            for msg in messages:
                role_icon = {"user": "👤 您", "assistant": "🤖 AI"}[msg['role']]
                print(f"{role_icon}: {msg['content']}")
            print()
            return True

        elif user_input == "/save":
            if self.agent:
                state = await self.agent.save_state()
                self.session_mgr.save_agent_state(
                    session_id=self.current_session_id,
                    state=state,
                    his_user_id=self.current_user_id
                )
                print("\n✅ 会话已保存\n")
            return True

        return False


# ============================================
# 程序入口
# ============================================

async def main():
    """主函数"""
    app = GeneralPractitionerApp()
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
