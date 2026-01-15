"""
心血管内科智能体适配器 - 包装 CardioAgent 以实现 BaseAgent 接口
"""
from typing import Dict, Any, Optional, Callable, Awaitable
from ..base import BaseAgent


class CardioAgentWrapper(BaseAgent):
    """心血管内科智能体适配器 - 实现 BaseAgent 接口"""
    
    def __init__(self):
        self._cardio_agent = None  # 延迟初始化
    
    def _ensure_agent(self):
        """确保 Agent 已初始化（延迟加载）"""
        if self._cardio_agent is None:
            from .cardio_agent import CardioAgent
            self._cardio_agent = CardioAgent()
        return self._cardio_agent
    
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态"""
        from .cardio_agent import create_cardio_initial_state
        return create_cardio_initial_state(session_id, user_id)
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str,
        attachments: Optional[list] = None,
        action: Optional[str] = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        on_step: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """运行智能体"""
        from .cardio_agent import CardioTaskType
        
        agent = self._ensure_agent()  # 延迟初始化
        
        # 映射 action 到 CardioTaskType
        task_type = CardioTaskType.CONVERSATION
        if action:
            action_map = {
                "conversation": CardioTaskType.CONVERSATION,
                "ecg_analysis": CardioTaskType.ECG_ANALYSIS,
                "report_interpretation": CardioTaskType.REPORT_INTERPRETATION,
            }
            task_type = action_map.get(action, CardioTaskType.CONVERSATION)
        
        # 提取图片信息
        image_base64 = None
        if attachments:
            for att in attachments:
                if att.get("type") == "image":
                    image_base64 = att.get("base64")
                    break
        
        # 调用原有的 CardioAgent
        updated_state = await agent.run(
            state=state,
            user_input=user_input,
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
