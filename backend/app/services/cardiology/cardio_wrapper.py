"""
心血管内科智能体适配器 - 包装 CardioAgent 以实现 BaseAgent 接口
"""
from typing import Dict, Any, Optional, Callable, Awaitable
from ..base import BaseAgent
from .cardio_agent import CardioAgent, create_cardio_initial_state, CardioTaskType


class CardioAgentWrapper(BaseAgent):
    """心血管内科智能体适配器 - 实现 BaseAgent 接口"""
    
    def __init__(self):
        self._cardio_agent = CardioAgent()
    
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态"""
        return create_cardio_initial_state(session_id, user_id)
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        运行心血管内科智能体
        
        Args:
            state: 当前会话状态
            user_input: 用户文本输入
            attachments: 附件列表 [{type, url, base64, metadata}]
            action: 动作类型 ("conversation", "interpret_ecg", "risk_assessment")
            on_chunk: 流式输出回调
            
        Returns:
            更新后的状态
        """
        # 解析 action 到 task_type
        task_type_mapping = {
            "conversation": CardioTaskType.CONVERSATION,
            "interpret_ecg": CardioTaskType.INTERPRET_ECG,
            "risk_assessment": CardioTaskType.RISK_ASSESSMENT
        }
        task_type = task_type_mapping.get(action, CardioTaskType.CONVERSATION)
        
        # 提取图片信息（用于心电图解读）
        image_url = None
        image_base64 = None
        if attachments:
            for att in attachments:
                att_type = att.get("type", "") if isinstance(att, dict) else ""
                if att_type == "image" or att_type.startswith("image/"):
                    image_url = att.get("url")
                    image_base64 = att.get("base64")
                    break
        
        # 调用 CardioAgent
        updated_state = await self._cardio_agent.run(
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
            "actions": ["conversation", "interpret_ecg", "risk_assessment"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
            "ui_components": ["TextBubble", "ECGInterpretationCard", "RiskAssessmentCard"],
            "description": "心血管内科AI智能体，支持心血管症状问诊、心电图解读和风险评估"
        }
