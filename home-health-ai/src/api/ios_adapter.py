"""
iOS 适配器 - 使用 AutoGen Agent 的真正流式输出

使用 model_client_stream=True 实现真正的增量 token 输出。
"""

import json
import logging
import re
from typing import AsyncGenerator

from src.agents.general_practitioner import create_general_practitioner

logger = logging.getLogger(__name__)


class iOSAdapter:
    """iOS 适配器 - 使用 AutoGen Agent 真正的流式输出"""

    def __init__(self):
        self._agent = None

    def _get_agent(self):
        """延迟初始化 Agent（启用流式输出）"""
        if self._agent is None:
            self._agent = create_general_practitioner(model_client_stream=True)
            logger.info("[iOSAdapter] AutoGen Agent 初始化完成 (model_client_stream=True)")
        return self._agent

    async def stream_to_ios_format(
        self,
        session_id: str,
        his_user_id: str,
        message: str,
        his_patient_id: str = None
    ) -> AsyncGenerator[str, None]:
        """使用 AutoGen Agent 的真正流式输出

        使用 model_client_stream=True，返回 ModelClientStreamingChunkEvent 事件。
        """
        agent = self._get_agent()
        logger.info(f"[iOSAdapter] session_id={session_id}, message={message[:50]}...")

        # 发送 meta 事件
        yield self._format_sse("meta", {
            "session_id": session_id,
            "agent_type": "general"
        })

        full_content = ""
        thinking = None

        try:
            # 使用 run_stream 获取真正的流式输出
            async for event in agent.run_stream(task=message):
                event_type = type(event).__name__

                # 真正的流式 token 事件
                if event_type == "ModelClientStreamingChunkEvent":
                    chunk = event.content
                    full_content += chunk

                    # 实时发送 chunk
                    yield self._format_sse("chunk", {"text": chunk})

                # 最终结果
                elif event_type == "TaskResult":
                    thinking = self._extract_thinking(full_content)
                    logger.info(f"[iOSAdapter] 完成: {len(full_content)} 字符")

            # 发送 complete 事件
            yield self._format_sse("complete", {
                "message": self._remove_thinking_markers(full_content),
                "stage": "completed",
                "progress": 100,
                "quick_options": [],
                "current_thought": thinking,
                "show_thinking": thinking is not None
            })

        except Exception as e:
            logger.error(f"[iOSAdapter] 错误: {e}", exc_info=True)
            yield self._format_sse("error", {"error": str(e)})

    def _format_sse(self, event: str, data: dict) -> str:
        """格式化为 SSE 格式"""
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    def _extract_thinking(self, content: str) -> str:
        """提取深度思考内容"""
        match = re.search(r'深度思考（(.+?)）', content)
        return match.group(1) if match else None

    def _remove_thinking_markers(self, content: str) -> str:
        """移除思考标记，返回纯文本"""
        clean = re.sub(r'深度思考（.+?）\s*', '', content)
        return clean.strip()


# 单例实例
_ios_adapter: iOSAdapter = None


def get_ios_adapter() -> iOSAdapter:
    """获取 iOS 适配器单例"""
    global _ios_adapter
    if _ios_adapter is None:
        _ios_adapter = iOSAdapter()
    return _ios_adapter
