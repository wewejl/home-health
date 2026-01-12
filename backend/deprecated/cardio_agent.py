"""
心血管内科AI智能体 - 基于CrewAI的多智能体心血管问诊系统
支持：心血管症状问诊、心电图解读、风险评估

架构说明：
- 完全基于 CrewAI 多智能体架构实现
- 通过 cardio_crew_service 协调各专业 Agent 完成任务
- 对外接口保持统一，确保与 AgentRouter 兼容
"""
from typing import TypedDict, List, Optional, Literal, Callable, Awaitable
from enum import Enum


class CardioTaskType(str, Enum):
    """心血管内科任务类型"""
    CONVERSATION = "conversation"           # 普通对话问诊
    INTERPRET_ECG = "interpret_ecg"         # 心电图解读
    RISK_ASSESSMENT = "risk_assessment"     # 风险评估


class CardioQuickOption(TypedDict):
    """快捷选项"""
    text: str
    value: str
    category: str


class CardioState(TypedDict):
    """心血管内科问诊状态"""
    session_id: str
    user_id: int
    
    # 对话历史
    messages: List[dict]
    
    # 症状信息
    chief_complaint: str          # 主诉
    symptoms: List[str]           # 症状列表
    symptom_details: dict         # 症状详情
    symptom_location: str         # 症状部位
    duration: str                 # 持续时间
    triggers: List[str]           # 诱因
    relieving_factors: List[str]  # 缓解因素
    
    # 风险因素
    risk_factors: List[str]       # 风险因素列表
    medical_history: List[str]    # 既往病史
    family_history: str           # 家族史
    lifestyle: dict               # 生活方式（吸烟、饮酒、运动等）
    
    # 心电图解读结果
    ecg_interpretations: List[dict]
    latest_ecg_interpretation: Optional[dict]
    
    # 风险评估结果
    risk_assessments: List[dict]
    latest_risk_assessment: Optional[dict]
    
    # 问诊进度
    stage: Literal["greeting", "collecting", "risk_assessment", "summary", "completed"]
    progress: int
    questions_asked: int
    
    # AI生成内容
    current_response: str
    quick_options: List[CardioQuickOption]
    
    # 风险等级
    risk_level: Literal["low", "medium", "high", "emergency"]
    need_urgent_care: bool
    
    # 诊断相关
    possible_conditions: List[dict]
    care_advice: str
    
    # 控制标志
    current_task: CardioTaskType


def create_cardio_initial_state(session_id: str, user_id: int) -> CardioState:
    """创建心血管内科问诊初始状态"""
    return CardioState(
        session_id=session_id,
        user_id=user_id,
        messages=[],
        chief_complaint="",
        symptoms=[],
        symptom_details={},
        symptom_location="",
        duration="",
        triggers=[],
        relieving_factors=[],
        risk_factors=[],
        medical_history=[],
        family_history="",
        lifestyle={},
        ecg_interpretations=[],
        latest_ecg_interpretation=None,
        risk_assessments=[],
        latest_risk_assessment=None,
        stage="greeting",
        progress=0,
        questions_asked=0,
        current_response="",
        quick_options=[],
        risk_level="low",
        need_urgent_care=False,
        possible_conditions=[],
        care_advice="",
        current_task=CardioTaskType.CONVERSATION
    )


class CardioAgent:
    """
    心血管内科AI智能体 - 基于 CrewAI 多智能体架构
    
    通过 cardio_crew_service 协调多个专业 Agent 完成心血管内科问诊任务：
    - 对话编排 Agent：管理问诊流程，识别紧急情况
    - 心电图解读 Agent：分析心电图报告
    - 风险评估 Agent：综合心血管风险评估
    
    对外接口保持统一，确保与 AgentRouter 兼容
    """
    
    def __init__(self):
        """初始化 CardioAgent，使用 CrewAI 服务"""
        from .cardio_crew_service import cardio_crew_service
        self._crew_service = cardio_crew_service
        print("[CardioAgent] Initialized with CrewAI multi-agent architecture")
    
    async def run(
        self,
        state: CardioState,
        user_input: str = None,
        image_url: str = None,
        image_base64: str = None,
        task_type: CardioTaskType = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> CardioState:
        """
        运行心血管内科智能体
        
        Args:
            state: 当前会话状态
            user_input: 用户文本输入
            image_url: 心电图图像URL
            image_base64: 心电图图像Base64编码
            task_type: 任务类型
            on_chunk: 流式输出回调
            
        Returns:
            更新后的状态
        """
        # 确定任务类型
        effective_task_type = task_type
        if effective_task_type is None:
            effective_task_type = CardioTaskType.CONVERSATION
        
        # 更新当前任务
        state["current_task"] = effective_task_type
        
        return await self._crew_service.run(
            state=state,
            user_input=user_input,
            image_url=image_url,
            image_base64=image_base64,
            task_type=effective_task_type.value if isinstance(effective_task_type, CardioTaskType) else effective_task_type,
            on_chunk=on_chunk
        )
    
    async def interpret_ecg(
        self,
        state: CardioState,
        ecg_description: str = None,
        image_url: str = None,
        image_base64: str = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> CardioState:
        """解读心电图"""
        return await self._crew_service.run(
            state=state,
            user_input=ecg_description,
            image_url=image_url,
            image_base64=image_base64,
            task_type="interpret_ecg",
            on_chunk=on_chunk
        )
    
    async def assess_risk(
        self,
        state: CardioState,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> CardioState:
        """进行心血管风险评估"""
        return await self._crew_service.run(
            state=state,
            task_type="risk_assessment",
            on_chunk=on_chunk
        )
    
    async def process_conversation(
        self,
        state: CardioState,
        user_input: str,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> CardioState:
        """处理对话"""
        return await self._crew_service.run(
            state=state,
            user_input=user_input,
            task_type="conversation",
            on_chunk=on_chunk
        )


# 全局实例
cardio_agent = CardioAgent()
