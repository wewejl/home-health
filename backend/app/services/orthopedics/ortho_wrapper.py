"""
骨科智能体适配器 - 包装 OrthoAgent 以实现 BaseAgent 接口
"""
from typing import Dict, Any, Optional, Callable, Awaitable
from ..base import BaseAgent
from .ortho_agent import OrthoAgent, create_ortho_initial_state, OrthoTaskType


class OrthoAgentWrapper(BaseAgent):
    """骨科智能体适配器 - 实现 BaseAgent 接口"""
    
    def __init__(self):
        self._ortho_agent = OrthoAgent()
    
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态"""
        return create_ortho_initial_state(session_id, user_id)
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        运行骨科智能体
        
        Args:
            state: 当前会话状态
            user_input: 用户文本输入
            attachments: 附件列表 [{type, url, base64, metadata}]
            action: 动作类型 ("conversation", "interpret_xray")
            on_chunk: 流式输出回调
            
        Returns:
            更新后的状态
        """
        # 解析 action 到 task_type
        task_type_mapping = {
            "conversation": OrthoTaskType.CONVERSATION,
            "interpret_xray": OrthoTaskType.INTERPRET_XRAY,
        }
        task_type = task_type_mapping.get(action, OrthoTaskType.CONVERSATION)
        
        # 提取图片信息（用于X光片解读）
        image_url = None
        image_base64 = None
        if attachments:
            for att in attachments:
                att_type = att.get("type", "") if isinstance(att, dict) else ""
                if att_type == "image" or att_type.startswith("image/"):
                    image_url = att.get("url")
                    image_base64 = att.get("base64")
                    break
        
        # 调用 OrthoAgent
        updated_state = await self._ortho_agent.run(
            state=state,
            user_input=user_input,
            image_url=image_url,
            image_base64=image_base64,
            task_type=task_type,
            on_chunk=on_chunk
        )
        
        return updated_state
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取能力配置"""
        return {
            "actions": ["conversation", "interpret_xray"],
            "accepts_media": ["image/jpeg", "image/png"],
            "ui_components": ["TextBubble", "XRayInterpretationCard"],
            "description": "骨科AI智能体，支持骨科症状问诊和X光片解读"
        }
