#!/usr/bin/env python3
"""
ChatService - 对话服务

连接 Agent 和数据库，提供完整的对话功能。

职责：
    - Agent 生命周期管理
    - 状态持久化（保存/加载）
    - 对话历史记录
    - 审计日志
    - AutoGen 流式输出（Agent 级别）

使用示例：
    >>> from src.services.chat_service import ChatService
    >>>
    >>> service = ChatService()
    >>> response = await service.chat(
    ...     session_id="session_001",
    ...     his_user_id="doctor_123",
    ...     message="你好，我叫张三"
    ... )
    >>> print(response)
"""

import json
import logging
import dataclasses
from datetime import datetime
from typing import Optional, AsyncGenerator

from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from src.agents.general_practitioner import create_general_practitioner
from src.db.session_manager import SessionManager

logger = logging.getLogger(__name__)


class ChatService:
    """对话服务

    提供 Agent 和数据库的集成，管理完整的对话流程。

    Attributes:
        session_mgr: SessionManager 实例，用于数据库操作
    """

    def __init__(self):
        """初始化对话服务"""
        self.session_mgr = SessionManager()
        logger.info("ChatService 初始化成功")

    # =====================================================
    # 核心方法：处理对话
    # =====================================================

    async def chat_stream_autogen(
        self,
        session_id: str,
        his_user_id: str,
        message: str,
        his_patient_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """AutoGen 流式对话"""
        logger.info(f"[{session_id}] 收到 AutoGen 流式对话请求: user={his_user_id}")

        # 1. 创建 Agent
        agent = create_general_practitioner()

        # 2. 从数据库加载历史状态（静默失败）
        try:
            state = self.session_mgr.load_agent_state(session_id)
            if state:
                await agent.load_state(state)
                logger.info(f"[{session_id}] 已加载历史状态")
            else:
                logger.info(f"[{session_id}] 新会话，无历史状态")
        except Exception as e:
            logger.warning(f"[{session_id}] 数据库不可用，继续无状态对话: {e}")

        # 3. 保存用户消息（静默失败）
        try:
            self.session_mgr.save_chat_message(
                session_id=session_id,
                his_user_id=his_user_id,
                role="user",
                content=message
            )
        except Exception as e:
            logger.warning(f"[{session_id}] 无法保存用户消息: {e}")

        # 4. 使用 AutoGen 流式
        logger.info(f"[{session_id}] 开始 AutoGen 流式处理...")

        # 构建包含上下文的消息
        contextual_message = message

        # 添加患者ID和医生ID到消息上下文
        context_parts = []
        if his_patient_id:
            context_parts.append(f"[当前患者ID: {his_patient_id}]")
        context_parts.append(f"[当前医生ID: {his_user_id}]")

        if context_parts:
            contextual_message = " ".join(context_parts) + "\n\n" + message
            logger.info(f"[{session_id}] 已添加患者ID和医生ID上下文到消息")

        try:
            final_response = None
            final_content = ""

            async for event in agent.on_messages_stream(
                [TextMessage(content=contextual_message, source="user")],
                cancellation_token=CancellationToken()
            ):
                event_type = type(event).__name__
                logger.info(f"[{session_id}] 事件: {event_type}")

                # 序列化事件
                event_data = serialize_event(event)
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                # 保存 Response
                if event_type == 'Response':
                    final_response = event
                    final_content = event.chat_message.content

            # 5. 保存 AI 回复（静默失败）
            try:
                self.session_mgr.save_chat_message(
                    session_id=session_id,
                    his_user_id=his_user_id,
                    role="assistant",
                    content=final_content
                )
            except Exception as e:
                logger.warning(f"[{session_id}] 无法保存AI回复: {e}")

            # 6. 保存状态（静默失败）
            try:
                new_state = await agent.save_state()
                self.session_mgr.save_agent_state(
                    session_id=session_id,
                    state=new_state,
                    his_user_id=his_user_id,
                    his_patient_id=his_patient_id
                )
            except Exception as e:
                logger.warning(f"[{session_id}] 无法保存状态: {e}")

            # 7. 发送完成标记
            yield f"data: {json.dumps({'event_type': 'done'}, ensure_ascii=False)}\n\n"

            logger.info(f"[{session_id}] AutoGen 流式完成")

        except Exception as e:
            logger.error(f"[{session_id}] 错误: {e}", exc_info=True)
            yield f"data: {json.dumps({'event_type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"

    # =====================================================
    # 辅助方法
    # =====================================================

    def get_session_history(self, session_id: str) -> list:
        """获取会话的对话历史

        Args:
            session_id: 会话 ID

        Returns:
            list: 对话历史列表，按时间正序排列

        Example:
            >>> service = ChatService()
            >>> history = service.get_session_history("session_001")
            >>> for msg in history:
            ...     print(f"{msg['role']}: {msg['content']}")
        """
        return self.session_mgr.get_chat_history(session_id)

    def list_user_sessions(self, his_user_id: str, limit: int = 20) -> list:
        """列出用户的所有会话

        Args:
            his_user_id: HIS 医生 ID
            limit: 返回的最大数量

        Returns:
            list: 会话列表
        """
        return self.session_mgr.list_sessions(his_user_id, limit)

    def delete_session(self, session_id: str) -> bool:
        """删除会话及其所有数据

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否删除成功
        """
        return self.session_mgr.delete_session(session_id)


# =====================================================
# 工具函数
# =====================================================

def _serialize_value(obj):
    """递归序列化任意值（辅助函数）

    处理：
    - None
    - 基本类型 (str, int, float, bool)
    - datetime
    - dataclass
    - list
    - dict
    - 带有 __dict__ 的对象
    - 其他对象
    """
    # 处理 None
    if obj is None:
        return None

    # 处理基本类型
    if isinstance(obj, (str, int, float, bool)):
        return obj

    # 处理 datetime
    if isinstance(obj, datetime):
        return obj.isoformat()

    # 处理 dataclass
    if dataclasses.is_dataclass(obj):
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name, None)
            result[field_name] = _serialize_value(value)
        return result

    # 处理 list
    if isinstance(obj, list):
        return [_serialize_value(item) for item in obj]

    # 处理 dict
    if isinstance(obj, dict):
        return {k: _serialize_value(v) for k, v in obj.items()}

    # 处理带有 __dict__ 的对象
    if hasattr(obj, '__dict__'):
        return _serialize_value(obj.__dict__)

    # 其他对象：转换为字符串表示
    return {'_type': type(obj).__name__, '_str': str(obj)}


def serialize_event(obj):
    """序列化 AutoGen 事件对象

    将 AutoGen 的事件对象（通常是 dataclass）转换为可 JSON 序列化的字典。
    返回结构：{'event_type': 'TypeName', 'data': {...}}

    Args:
        obj: AutoGen 事件对象

    Returns:
        dict: 包含 event_type 和 data 的字典，可直接 JSON 序列化
    """
    return {
        'event_type': type(obj).__name__,
        'data': _serialize_value(obj)
    }


# =====================================================
# 导出的类
# =====================================================

__all__ = ['ChatService']
