"""
皮肤科智能体适配器 - 包装现有的 DermaAgent
"""
from typing import Dict, Any, Optional, Callable, Awaitable
from ..base import BaseAgent
from .derma_agent import DermaAgent, create_derma_initial_state, DermaTaskType


class DermaAgentWrapper(BaseAgent):
    """皮肤科智能体适配器 - 实现 BaseAgent 接口"""
    
    def __init__(self):
        self._derma_agent = DermaAgent()
    
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态"""
        return create_derma_initial_state(session_id, user_id)
    
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
        # 解析 action 到 task_type
        task_type_mapping = {
            "conversation": DermaTaskType.CONVERSATION,
            "analyze_skin": DermaTaskType.SKIN_ANALYSIS,
            "interpret_report": DermaTaskType.REPORT_INTERPRET
        }
        task_type = task_type_mapping.get(action, DermaTaskType.CONVERSATION)
        
        # 提取图片信息
        image_url = None
        image_base64 = None
        if attachments:
            for att in attachments:
                att_type = att.get("type", "") if isinstance(att, dict) else ""
                if att_type == "image" or att_type.startswith("image/"):
                    image_url = att.get("url")
                    image_base64 = att.get("base64")
                    break
        
        # 调用原有的 DermaAgent
        updated_state = await self._derma_agent.run(
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
            "actions": ["conversation", "analyze_skin", "interpret_report"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
            "ui_components": ["TextBubble", "SkinAnalysisCard", "ReportInterpretationCard"],
            "description": "皮肤科AI智能体，支持皮肤影像分析和报告解读"
        }
