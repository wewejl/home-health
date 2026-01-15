"""
骨科智能体适配器 - 包装 OrthoAgent 以实现 BaseAgent 接口
"""
from typing import Dict, Any, Optional, Callable, Awaitable
from ..base import BaseAgent


class OrthoAgentWrapper(BaseAgent):
    """骨科智能体适配器 - 实现 BaseAgent 接口"""
    
    def __init__(self):
        self._ortho_agent = None  # 延迟初始化
    
    def _ensure_agent(self):
        """确保 Agent 已初始化（延迟加载）"""
        if self._ortho_agent is None:
            from .ortho_agent import OrthoAgent
            self._ortho_agent = OrthoAgent()
        return self._ortho_agent
    
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态"""
        from .ortho_agent import create_ortho_initial_state
        return create_ortho_initial_state(session_id, user_id)
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str,
        attachments: Optional[list] = None,
        action: Optional[str] = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        on_step: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        运行骨科智能体
        
        Args:
            state: 当前会话状态
            user_input: 用户文本输入
            attachments: 附件列表 [{type, url, base64, metadata}]
            action: 动作类型 ("conversation", "interpret_xray")
            on_chunk: 流式输出回调
            on_step: 步骤回调
            
        Returns:
            更新后的状态
        """
        from .ortho_agent import OrthoTaskType
        
        agent = self._ensure_agent()  # 延迟初始化
        
        # 映射 action 到 task_type
        task_type = OrthoTaskType.CONVERSATION
        if action:
            action_map = {
                "conversation": OrthoTaskType.CONVERSATION,
                "interpret_xray": OrthoTaskType.INTERPRET_XRAY,
            }
            task_type = action_map.get(action, OrthoTaskType.CONVERSATION)
        
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
        updated_state = await agent.run(
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
