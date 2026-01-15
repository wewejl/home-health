"""
皮肤科 LangGraph Wrapper - 适配 BaseAgent 接口

与 DermaAgentWrapper 完全兼容，用于 A/B 测试和渐进式迁移
"""
from typing import Dict, Any, Optional, Callable, Awaitable

from ..base import BaseAgent
from .derma_langgraph_agent import DermaLangGraphAgent


class DermaLangGraphWrapper(BaseAgent):
    """
    皮肤科 LangGraph 适配器
    
    实现 BaseAgent 接口，内部使用 DermaLangGraphAgent
    """
    
    def __init__(self):
        self._agent = DermaLangGraphAgent()
    
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态"""
        return await self._agent.create_initial_state(session_id, user_id)
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        运行皮肤科智能体
        
        Args:
            state: 当前会话状态
            user_input: 用户文本输入
            attachments: 附件列表 [{type, url, base64, metadata}]
            action: 动作类型 ("conversation", "analyze_skin", "interpret_report")
            on_chunk: 流式输出回调
            
        Returns:
            更新后的状态
        """
        # 处理图片附件
        processed_attachments = []
        if attachments:
            for att in attachments:
                att_type = att.get("type", "") if isinstance(att, dict) else ""
                if att_type == "image" or att_type.startswith("image/"):
                    processed_attachments.append({
                        "type": "image",
                        "url": att.get("url"),
                        "base64": att.get("base64"),
                        "id": att.get("id", ""),
                        "metadata": att.get("metadata", {})
                    })
        
        # 调用 LangGraph Agent
        updated_state = await self._agent.run(
            state=state,
            user_input=user_input,
            attachments=processed_attachments if processed_attachments else None,
            action=action,
            on_chunk=on_chunk
        )
        
        return updated_state
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取能力配置"""
        return self._agent.get_capabilities()
