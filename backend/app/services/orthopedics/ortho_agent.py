"""
骨科AI智能体 - 基于CrewAI的多智能体骨科问诊系统
支持：骨科症状问诊、X光片解读

架构说明：
- 完全基于 CrewAI 多智能体架构实现
- 通过 ortho_crew_service 协调各专业 Agent 完成任务
- 对外接口保持统一，确保与 AgentRouter 兼容
"""
from typing import TypedDict, List, Optional, Literal, Callable, Awaitable, Dict, Any
from enum import Enum


class OrthoTaskType(str, Enum):
    """骨科任务类型"""
    CONVERSATION = "conversation"       # 普通对话问诊
    INTERPRET_XRAY = "interpret_xray"   # X光片解读


class OrthoQuickOption(TypedDict):
    """快捷选项"""
    text: str
    value: str
    category: str


class OrthoState(TypedDict):
    """骨科问诊状态"""
    session_id: str
    user_id: int
    
    # 对话历史
    messages: List[dict]
    
    # 症状信息
    chief_complaint: str          # 主诉
    symptoms: List[str]           # 症状列表
    symptom_details: dict         # 症状详情
    pain_location: str            # 疼痛部位
    duration: str                 # 持续时间
    injury_history: str           # 外伤史
    
    # 既往史和其他信息
    medical_history: List[str]    # 既往病史
    mobility_limitation: str      # 活动受限情况
    
    # X光解读结果
    xray_interpretations: List[dict]
    latest_xray_interpretation: Optional[dict]
    
    # 问诊进度
    stage: Literal["greeting", "collecting", "summary", "completed"]
    progress: int
    questions_asked: int
    
    # AI生成内容
    current_response: str
    quick_options: List[OrthoQuickOption]
    
    # 风险等级
    risk_level: Literal["low", "medium", "high", "emergency"]
    need_urgent_care: bool
    
    # 诊断相关
    possible_conditions: List[dict]
    care_advice: str
    
    # 控制标志
    current_task: OrthoTaskType


def create_ortho_initial_state(session_id: str, user_id: int) -> OrthoState:
    """创建骨科问诊初始状态"""
    return OrthoState(
        session_id=session_id,
        user_id=user_id,
        messages=[],
        chief_complaint="",
        symptoms=[],
        symptom_details={},
        pain_location="",
        duration="",
        injury_history="",
        medical_history=[],
        mobility_limitation="",
        xray_interpretations=[],
        latest_xray_interpretation=None,
        stage="greeting",
        progress=0,
        questions_asked=0,
        current_response="",
        quick_options=[],
        risk_level="low",
        need_urgent_care=False,
        possible_conditions=[],
        care_advice="",
        current_task=OrthoTaskType.CONVERSATION
    )


class OrthoAgent:
    """
    骨科AI智能体 - 基于 CrewAI 多智能体架构
    
    功能：
    - 对话编排 Agent：管理问诊流程，收集骨科症状信息
    - X光解读 Agent：分析X光片，识别异常
    """
    
    def __init__(self):
        """初始化 OrthoAgent"""
        from .ortho_crew_service import OrthoCrewService
        self._crew_service = OrthoCrewService()
        print("[OrthoAgent] Initialized with CrewAI architecture")
    
    async def run(
        self,
        state: OrthoState,
        user_input: str = None,
        image_url: str = None,
        image_base64: str = None,
        task_type: OrthoTaskType = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> OrthoState:
        """
        运行骨科智能体
        
        Args:
            state: 当前会话状态
            user_input: 用户文本输入
            image_url: X光片图片 URL
            image_base64: X光片图片 Base64
            task_type: 任务类型
            on_chunk: 流式输出回调
            
        Returns:
            更新后的状态
        """
        # 转换 task_type 为字符串
        task_type_str = None
        if task_type:
            task_type_str = task_type.value if isinstance(task_type, OrthoTaskType) else task_type
        
        # 委托给 CrewService 处理
        updated_state = await self._crew_service.run(
            state=state,
            user_input=user_input,
            image_url=image_url,
            image_base64=image_base64,
            task_type=task_type_str,
            on_chunk=on_chunk
        )
        
        return updated_state
    
    async def interpret_xray(
        self,
        state: OrthoState,
        xray_description: str = None,
        image_url: str = None,
        image_base64: str = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> OrthoState:
        """
        解读X光片
        
        Args:
            state: 当前会话状态
            xray_description: X光片文字描述或报告内容
            image_url: X光片图片 URL
            image_base64: X光片图片 Base64
            on_chunk: 流式输出回调
            
        Returns:
            更新后的状态（包含解读结果）
        """
        return await self._crew_service.run(
            state=state,
            user_input=xray_description,
            image_url=image_url,
            image_base64=image_base64,
            task_type="interpret_xray",
            on_chunk=on_chunk
        )


# 全局实例
ortho_agent = OrthoAgent()
