"""
ReAct Agent API 适配层

实现 BaseAgent 接口，保持与现有 API 兼容
"""
from typing import Dict, Any, Optional, Callable, Awaitable, List
from langchain_core.messages import HumanMessage, AIMessage

from ..base import BaseAgent
from .react_state import create_react_initial_state
from .react_agent import get_derma_react_graph
from .quick_options import generate_quick_options


def _serialize_messages(messages: list) -> List[dict]:
    """序列化消息为 JSON 格式"""
    serialized = []
    for msg in messages:
        if isinstance(msg, dict):
            serialized.append(msg)
        elif hasattr(msg, "content"):
            role = "assistant" if getattr(msg, "type", "") == "ai" else "user"
            if hasattr(msg, "type") and msg.type == "system":
                continue  # 跳过 system 消息
            if hasattr(msg, "type") and msg.type == "tool":
                continue  # 跳过 tool 消息
            serialized.append({
                "role": role,
                "content": msg.content
            })
    return serialized


class DermaReActWrapper(BaseAgent):
    """
    皮肤科 ReAct Agent 适配器
    
    实现 BaseAgent 接口，内部使用 ReAct 模式
    """
    
    def __init__(self):
        self._graph = get_derma_react_graph()
    
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态"""
        state = create_react_initial_state(session_id, user_id)
        # 转换为普通 dict
        return dict(state)
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """运行智能体"""
        
        # 添加用户消息
        if user_input:
            state["messages"].append(HumanMessage(content=user_input))
        
        # 处理附件（图片）
        if attachments:
            for att in attachments:
                att_type = att.get("type", "")
                if att_type == "image" or att_type.startswith("image/"):
                    state["pending_attachments"].append(att)
        
        # 运行状态图
        if on_chunk:
            final_state = await self._run_with_stream(state, on_chunk)
        else:
            final_state = await self._graph.ainvoke(state)
        
        # 提取最后的 AI 回复
        ai_response = ""
        for msg in reversed(final_state.get("messages", [])):
            if hasattr(msg, "type") and msg.type == "ai":
                ai_response = msg.content
                break
            elif isinstance(msg, AIMessage):
                ai_response = msg.content
                break
        
        final_state["current_response"] = ai_response
        
        # 生成快捷选项
        if ai_response:
            final_state["quick_options"] = generate_quick_options(ai_response)
        
        # 序列化消息
        final_state["messages"] = _serialize_messages(final_state.get("messages", []))
        
        return final_state
    
    async def _run_with_stream(
        self,
        state: Dict[str, Any],
        on_chunk: Callable[[str], Awaitable[None]]
    ) -> Dict[str, Any]:
        """流式输出运行"""
        final_state = state.copy()
        
        async for event in self._graph.astream_events(state, version="v2"):
            if event.get("event") == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    await on_chunk(chunk.content)
            elif event.get("event") == "on_chain_end":
                output = event.get("data", {}).get("output")
                if isinstance(output, dict):
                    final_state = output
        
        return final_state
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取能力配置"""
        return {
            "actions": ["conversation", "analyze_skin", "interpret_report"],
            "accepts_media": ["image/jpeg", "image/png"],
            "ui_components": ["TextBubble", "SkinAnalysisCard"],
            "description": "皮肤科 ReAct AI 智能体"
        }
