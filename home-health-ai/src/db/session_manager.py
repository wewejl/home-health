#!/usr/bin/env python3
"""
会话管理器 - 管理 Agent 状态和对话历史
参考 AutoGen 官方示例的文件存储方式，改为 PostgreSQL 存储
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from .connection import get_connection
except ImportError:
    from src.db.connection import get_connection

logger = logging.getLogger(__name__)


class SessionManager:
    """管理 Agent 状态和对话历史"""

    def __init__(self):
        """初始化会话管理器"""
        self._connection = None

    def _get_connection(self):
        """获取数据库连接（懒加载）"""
        if self._connection is None:
            self._connection = get_connection()
        return self._connection

    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None

    # =====================================================
    # Agent 状态管理（核心功能）
    # =====================================================

    def save_agent_state(
        self,
        session_id: str,
        state: Dict[str, Any],
        his_user_id: str,
        his_patient_id: Optional[str] = None
    ) -> None:
        """保存 Agent 状态

        对应官方示例的文件存储：
        ```python
        state = await agent.save_state()
        async with aiofiles.open(state_path, "w") as file:
            await file.write(json.dumps(state))
        ```

        Args:
            session_id: 会话 ID
            state: AutoGen save_state() 返回的完整状态
            his_user_id: HIS 系统的用户 ID
            his_patient_id: HIS 系统的患者 ID（可选）
        """
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            # 计算 message_count
            message_count = len(state.get("llm_context", {}).get("messages", []))

            # 使用 UPSERT（插入或更新）
            cur.execute("""
                INSERT INTO agent_states (session_id, his_user_id, his_patient_id, state_json, message_count)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (session_id) DO UPDATE
                SET his_user_id = EXCLUDED.his_user_id,
                    his_patient_id = EXCLUDED.his_patient_id,
                    state_json = EXCLUDED.state_json,
                    message_count = EXCLUDED.message_count,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                session_id,
                his_user_id,
                his_patient_id,
                json.dumps(state, ensure_ascii=False),
                message_count
            ))

            conn.commit()
            logger.debug(f"保存 Agent 状态: session_id={session_id}, messages={message_count}")

        except Exception as e:
            conn.rollback()
            logger.error(f"保存状态失败: {e}")
            raise

    def load_agent_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载 Agent 状态

        对应官方示例的文件读取：
        ```python
        async with aiofiles.open(state_path, "r") as file:
            state = json.loads(await file.read())
        await agent.load_state(state)
        ```

        Args:
            session_id: 会话 ID

        Returns:
            Agent 状态字典，如果不存在返回 None
        """
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT state_json
                FROM agent_states
                WHERE session_id = %s
            """, (session_id,))

            row = cur.fetchone()

            if row:
                # PostgreSQL JSONB 已经解析为 Python 对象
                state = row[0] if isinstance(row[0], dict) else json.loads(row[0])
                logger.debug(f"加载 Agent 状态: session_id={session_id}")
                return state
            else:
                logger.debug(f"Agent 状态不存在: session_id={session_id}")
                return None

        except Exception as e:
            logger.error(f"加载状态失败: {e}")
            raise

    # =====================================================
    # 对话历史管理
    # =====================================================

    def save_chat_message(
        self,
        session_id: str,
        his_user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """保存对话消息

        Args:
            session_id: 会话 ID
            his_user_id: HIS 用户 ID
            role: 角色（user/assistant/system）
            content: 消息内容
            metadata: 额外信息（工具调用等）
        """
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO chat_history (session_id, his_user_id, role, content, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                session_id,
                his_user_id,
                role,
                content,
                json.dumps(metadata) if metadata else None
            ))

            conn.commit()
            logger.debug(f"保存对话消息: session_id={session_id}, role={role}")

        except Exception as e:
            conn.rollback()
            logger.error(f"保存消息失败: {e}")
            raise

    def get_chat_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取对话历史

        Args:
            session_id: 会话 ID
            limit: 限制返回条数

        Returns:
            对话历史列表（按时间正序）
        """
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            query = """
                SELECT id, session_id, his_user_id, role, content, metadata, created_at
                FROM chat_history
                WHERE session_id = %s
                ORDER BY created_at ASC
            """

            if limit:
                query += f" LIMIT {limit}"

            cur.execute(query, (session_id,))
            rows = cur.fetchall()

            history = [
                {
                    "id": row[0],
                    "session_id": row[1],
                    "his_user_id": row[2],
                    "role": row[3],
                    "content": row[4],
                    "metadata": row[5] if isinstance(row[5], (dict, type(None))) else (json.loads(row[5]) if row[5] else None),
                    "created_at": row[6].isoformat()
                }
                for row in rows
            ]

            return history

        except Exception as e:
            logger.error(f"获取历史失败: {e}")
            raise

    # =====================================================
    # 审计日志管理
    # =====================================================

    def save_audit_log(
        self,
        session_id: str,
        his_user_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """保存审计日志

        Args:
            session_id: 会话 ID
            his_user_id: HIS 用户 ID
            event_type: 事件类型（chat/tool_call/tool_result/error/state_save）
            event_data: 事件详细数据
        """
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO audit_logs (session_id, his_user_id, event_type, event_data)
                VALUES (%s, %s, %s, %s)
            """, (
                session_id,
                his_user_id,
                event_type,
                json.dumps(event_data) if event_data else None
            ))

            conn.commit()
            logger.debug(f"保存审计日志: session_id={session_id}, type={event_type}")

        except Exception as e:
            conn.rollback()
            logger.error(f"保存日志失败: {e}")
            raise

    # =====================================================
    # 辅助方法
    # =====================================================

    def list_sessions(
        self,
        his_user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """列出会话

        Args:
            his_user_id: 筛选用户（可选）
            limit: 限制返回条数

        Returns:
            会话列表
        """
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            query = """
                SELECT session_id, his_user_id, his_patient_id, message_count, created_at, updated_at
                FROM agent_states
                WHERE 1=1
            """

            params = []

            if his_user_id:
                query += " AND his_user_id = %s"
                params.append(his_user_id)

            query += " ORDER BY updated_at DESC LIMIT %s"
            params.append(limit)

            cur.execute(query, params)
            rows = cur.fetchall()

            sessions = [
                {
                    "session_id": row[0],
                    "his_user_id": row[1],
                    "his_patient_id": row[2],
                    "message_count": row[3],
                    "created_at": row[4].isoformat(),
                    "updated_at": row[5].isoformat()
                }
                for row in rows
            ]

            return sessions

        except Exception as e:
            logger.error(f"列出会话失败: {e}")
            raise

    def delete_session(self, session_id: str) -> bool:
        """删除会话（级联删除相关数据）

        Args:
            session_id: 会话 ID

        Returns:
            是否删除成功
        """
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            # 删除 chat_history（对话历史）
            cur.execute("DELETE FROM chat_history WHERE session_id = %s", (session_id,))

            # 删除 audit_logs（审计日志）
            cur.execute("DELETE FROM audit_logs WHERE session_id = %s", (session_id,))

            # 删除 agent_states（Agent 状态）
            cur.execute("DELETE FROM agent_states WHERE session_id = %s", (session_id,))

            conn.commit()
            logger.info(f"删除会话: session_id={session_id}")
            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"删除会话失败: {e}")
            return False


# =====================================================
# 测试代码
# =====================================================

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG)

    print("\n" + "="*70)
    print("📋 测试: SessionManager")
    print("="*70)

    mgr = SessionManager()

    # 测试 1: 模拟 Agent 状态
    print("\n1️⃣ 测试: 保存和加载 Agent 状态")

    mock_state = {
        "type": "AssistantAgentState",
        "version": "1.0.0",
        "llm_context": {
            "messages": [
                {"source": "system", "content": "You are a helpful assistant."},
                {"source": "user", "content": "你好"},
                {"source": "assistant", "content": "你好！有什么可以帮助你的？"}
            ]
        }
    }

    try:
        mgr.save_agent_state(
            session_id="test_001",
            state=mock_state,
            his_user_id="doctor_123"
        )
        print("✅ 保存状态成功")

        loaded_state = mgr.load_agent_state("test_001")
        if loaded_state == mock_state:
            print("✅ 加载状态成功")
            print(f"   消息数: {len(loaded_state['llm_context']['messages'])}")
        else:
            print("❌ 状态不一致")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)

    # 测试 2: 对话历史
    print("\n2️⃣ 测试: 对话历史")

    try:
        mgr.save_chat_message(
            session_id="test_001",
            his_user_id="doctor_123",
            role="user",
            content="你好"
        )
        mgr.save_chat_message(
            session_id="test_001",
            his_user_id="doctor_123",
            role="assistant",
            content="你好！有什么可以帮助你的？"
        )
        print("✅ 保存对话成功")

        history = mgr.get_chat_history("test_001")
        print(f"✅ 加载历史成功: {len(history)} 条消息")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)

    # 测试 3: 审计日志
    print("\n3️⃣ 测试: 审计日志")

    try:
        mgr.save_audit_log(
            session_id="test_001",
            his_user_id="doctor_123",
            event_type="chat",
            event_data={"message": "测试对话"}
        )
        print("✅ 保存审计日志成功")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)

    mgr.close()

    print("\n" + "="*70)
    print("🎉 SessionManager 所有测试通过！")
    print("="*70)
