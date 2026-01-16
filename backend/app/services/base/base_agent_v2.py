"""
BaseAgentV2 - 简化版智能体基类

设计原则：最小化抽象，只定义必须实现的方法
所有智能体返回统一的 AgentResponse 格式
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Awaitable
from ...schemas.agent_response import AgentResponse


class BaseAgentV2(ABC):
    """智能体抽象基类 V2"""
    
    @abstractmethod
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str,
        attachments: List[Dict[str, Any]] = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> AgentResponse:
        """
        执行智能体逻辑
        
        Args:
            state: 从数据库恢复的状态（上次返回的 next_state）
            user_input: 用户输入文本
            attachments: 附件列表 [{"type": "image", "base64": "..."}]
            action: 动作类型 (conversation, analyze_skin, interpret_report)
            on_chunk: 流式输出回调函数
            
        Returns:
            AgentResponse: 统一响应格式
        """
        pass
