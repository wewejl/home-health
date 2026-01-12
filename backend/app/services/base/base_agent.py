"""
BaseAgent 基类 - 所有智能体必须实现此接口
"""
from typing import Dict, Type, Any, Optional, Callable, Awaitable
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """智能体基类 - 所有智能体必须实现此接口"""
    
    @abstractmethod
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态"""
        pass
    
    @abstractmethod
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        运行智能体
        
        Args:
            state: 当前会话状态
            user_input: 用户文本输入
            attachments: 附件列表 [{type, url, base64, metadata}]
            action: 动作类型
            on_chunk: 流式输出回调
            
        Returns:
            更新后的状态
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        获取智能体能力配置
        
        Returns:
            {
                "actions": ["conversation", ...],
                "accepts_media": ["image/jpeg", ...],
                "ui_components": ["TextBubble", ...],
                "description": "智能体描述"
            }
        """
        pass
