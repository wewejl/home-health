"""
皮肤科AI智能体 - 基于CrewAI的多智能体皮肤科问诊系统
支持：皮肤影像分析、报告解读、智能问诊对话

架构说明：
- 完全基于 CrewAI 多智能体架构实现
- 通过 derma_crew_service 协调各专业 Agent 完成任务
- 对外接口保持不变，确保与现有路由兼容
"""
from typing import TypedDict, List, Optional, Literal, Callable, Awaitable
from enum import Enum


class DermaTaskType(str, Enum):
    """皮肤科任务类型"""
    CONVERSATION = "conversation"      # 普通对话问诊
    SKIN_ANALYSIS = "skin_analysis"    # 皮肤影像分析
    REPORT_INTERPRET = "report_interpret"  # 报告解读


class DermaQuickOption(TypedDict):
    """快捷选项"""
    text: str
    value: str
    category: str


class DermaState(TypedDict):
    """皮肤科问诊状态"""
    session_id: str
    user_id: int
    
    # 对话历史
    messages: List[dict]
    
    # 症状信息
    chief_complaint: str
    symptoms: List[str]
    symptom_details: dict
    skin_location: str  # 皮损部位
    duration: str       # 持续时间
    
    # 图像分析结果
    skin_analyses: List[dict]  # 皮肤分析历史
    latest_analysis: Optional[dict]
    
    # 报告解读结果
    report_interpretations: List[dict]
    latest_interpretation: Optional[dict]
    
    # 问诊进度
    stage: Literal["greeting", "collecting", "analyzing", "diagnosis", "completed"]
    progress: int
    questions_asked: int
    
    # AI生成内容
    current_response: str
    quick_options: List[DermaQuickOption]
    
    # 诊断结果
    possible_conditions: List[dict]
    risk_level: Literal["low", "medium", "high", "emergency"]
    care_advice: str
    need_offline_visit: bool
    
    # 控制标志
    current_task: DermaTaskType
    awaiting_image: bool  # 是否等待用户上传图片


def create_derma_initial_state(session_id: str, user_id: int) -> DermaState:
    """创建皮肤科问诊初始状态"""
    return DermaState(
        session_id=session_id,
        user_id=user_id,
        messages=[],
        chief_complaint="",
        symptoms=[],
        symptom_details={},
        skin_location="",
        duration="",
        skin_analyses=[],
        latest_analysis=None,
        report_interpretations=[],
        latest_interpretation=None,
        stage="greeting",
        progress=0,
        questions_asked=0,
        current_response="",
        quick_options=[],
        possible_conditions=[],
        risk_level="low",
        care_advice="",
        need_offline_visit=False,
        current_task=DermaTaskType.CONVERSATION,
        awaiting_image=False
    )


class DermaAgent:
    """
    皮肤科AI智能体 - 基于 CrewAI 多智能体架构
    
    通过 derma_crew_service 协调多个专业 Agent 完成皮肤科问诊任务：
    - 对话编排 Agent：管理问诊流程
    - 皮肤分析 Agent：分析皮肤图像
    - 报告解读 Agent：解读医学报告
    - 安全检查 Agent：风险评估
    
    对外接口保持不变，确保与现有路由兼容
    """
    
    def __init__(self):
        """初始化 DermaAgent，直接使用 CrewAI 服务"""
        from .derma_crew_service import derma_crew_service
        self._crew_service = derma_crew_service
        print("[DermaAgent] Initialized with CrewAI multi-agent architecture")
    
    async def run(
        self,
        state: DermaState,
        user_input: str = None,
        image_url: str = None,
        image_base64: str = None,
        task_type: DermaTaskType = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        on_step: Optional[Callable[[str, str], Awaitable[None]]] = None
    ) -> DermaState:
        """
        运行皮肤科智能体
        
        Args:
            state: 当前会话状态
            user_input: 用户文本输入
            image_url: 图像URL
            image_base64: 图像Base64编码
            task_type: 任务类型
            on_chunk: 流式输出回调
            on_step: 思考步骤回调
            
        Returns:
            更新后的状态
        """
        return await self._crew_service.run(
            state=state,
            user_input=user_input,
            image_url=image_url,
            image_base64=image_base64,
            task_type=task_type,
            on_chunk=on_chunk,
            on_step=on_step
        )
    
    async def analyze_skin_image(
        self,
        state: DermaState,
        image_url: str = None,
        image_base64: str = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> DermaState:
        """分析皮肤图像"""
        return await self._crew_service._handle_skin_analysis(
            state=state,
            image_url=image_url,
            image_base64=image_base64,
            on_chunk=on_chunk
        )
    
    async def interpret_report(
        self,
        state: DermaState,
        image_url: str = None,
        image_base64: str = None,
        report_type: str = "皮肤科检查报告",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> DermaState:
        """解读医学报告"""
        return await self._crew_service._handle_report_interpret(
            state=state,
            image_url=image_url,
            image_base64=image_base64,
            report_type=report_type,
            on_chunk=on_chunk
        )
    
    async def guide_image_upload(
        self,
        state: DermaState,
        task_type: DermaTaskType,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> DermaState:
        """引导用户上传图片"""
        return await self._crew_service._guide_image_upload(
            state=state,
            task_type=task_type,
            on_chunk=on_chunk
        )
    
    async def process_conversation(
        self,
        state: DermaState,
        user_input: str,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        on_step: Optional[Callable[[str, str], Awaitable[None]]] = None
    ) -> DermaState:
        """处理对话"""
        return await self._crew_service._handle_conversation(
            state=state,
            user_input=user_input,
            on_chunk=on_chunk,
            on_step=on_step
        )


# 全局实例
derma_agent = DermaAgent()
