"""
皮肤科智能体状态定义

继承 BaseAgentState，添加皮肤科特有字段
"""
from typing import List, Optional, Literal, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

from ..base.langgraph_base import BaseAgentState


class DermaState(TypedDict):
    """
    皮肤科专用状态
    
    包含 BaseAgentState 所有字段 + 皮肤科特有字段
    """
    # === 会话标识（继承自 BaseAgentState）===
    session_id: str
    user_id: int
    agent_type: str
    
    # === 对话历史 ===
    messages: Annotated[List[dict], add_messages]
    
    # === 问诊进度 ===
    stage: Literal["greeting", "collecting", "analyzing", "diagnosis", "completed"]
    questions_asked: int
    
    # === 核心医学信息 ===
    chief_complaint: str
    symptoms: List[str]
    duration: str
    
    # === AI 输出 ===
    current_response: str
    quick_options: List[dict]
    
    # === 流程控制 ===
    next_node: str
    should_stream: bool
    
    # === 附件处理 ===
    pending_attachments: List[dict]
    processed_results: List[dict]
    
    # === 错误处理 ===
    error: Optional[str]
    
    # === 皮肤科特有字段 ===
    skin_location: str
    skin_analyses: List[dict]
    latest_analysis: Optional[dict]
    
    # === 诊断相关 ===
    possible_conditions: List[dict]
    risk_level: Literal["low", "medium", "high", "emergency"]
    care_advice: str
    need_offline_visit: bool


def create_derma_initial_state(session_id: str, user_id: int) -> DermaState:
    """
    创建皮肤科初始状态
    
    Args:
        session_id: 会话 ID
        user_id: 用户 ID
        
    Returns:
        初始化的 DermaState
    """
    return DermaState(
        # 会话标识
        session_id=session_id,
        user_id=user_id,
        agent_type="dermatology",
        
        # 对话历史
        messages=[],
        
        # 问诊进度
        stage="greeting",
        questions_asked=0,
        
        # 核心医学信息
        chief_complaint="",
        symptoms=[],
        duration="",
        
        # AI 输出
        current_response="",
        quick_options=[],
        
        # 流程控制
        next_node="router",
        should_stream=False,
        
        # 附件处理
        pending_attachments=[],
        processed_results=[],
        
        # 错误处理
        error=None,
        
        # 皮肤科特有
        skin_location="",
        skin_analyses=[],
        latest_analysis=None,
        
        # 诊断相关
        possible_conditions=[],
        risk_level="low",
        care_advice="",
        need_offline_visit=False
    )
