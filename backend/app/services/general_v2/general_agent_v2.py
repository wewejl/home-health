"""
通用智能体 V2 - 基于新架构
"""
from ..base.base_agent_v2 import BaseAgentV2
from ...schemas.agent_response import AgentResponse
from typing import Dict, Any, List, Optional, Callable, Awaitable


class GeneralAgentV2(BaseAgentV2):
    """通用智能体 V2"""
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str,
        attachments: List[Dict[str, Any]] = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> AgentResponse:
        """执行通用问诊流程"""
        
        stage = state.get("stage", "greeting")
        
        if stage == "greeting":
            message = "您好，我是全科AI医生。请描述您的症状或问题。"
            new_stage = "collecting"
        else:
            message = f"我了解到您说：{user_input}。请继续描述或提供更多信息。"
            new_stage = "collecting"
        
        if on_chunk:
            await on_chunk(message)
        
        return AgentResponse(
            message=message,
            stage=new_stage,
            progress=20,
            quick_options=["继续描述", "换个问题"],
            next_state={
                "stage": new_stage,
                "history": state.get("history", []) + [user_input] if user_input else []
            }
        )
