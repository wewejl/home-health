"""
ReAct Agent 状态定义

基于 LangGraph ReAct 模式的皮肤科智能体状态
"""
from typing import List, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class DermaReActState(TypedDict):
    """皮肤科 ReAct Agent 状态"""
    # === 会话标识 ===
    session_id: str
    user_id: int
    
    # === 对话历史（LangGraph 自动管理）===
    messages: Annotated[List[BaseMessage], add_messages]
    
    # === 医学信息（LLM 提取并累积）===
    chief_complaint: str
    skin_location: str
    symptoms: List[str]
    duration: str
    
    # === 分析结果 ===
    skin_analyses: List[dict]
    knowledge_refs: List[dict]
    possible_conditions: List[dict]
    
    # === 输出控制 ===
    current_response: str
    quick_options: List[dict]
    
    # === 待处理附件 ===
    pending_attachments: List[dict]
    
    # === 诊断相关 ===
    risk_level: str
    care_advice: str
    need_offline_visit: bool
    
    # === 新增：诊断展示增强 ===
    advice_history: List[dict]  # [{id, title, content, evidence, timestamp}]
    diagnosis_card: Optional[dict]  # 结构化诊断结果
    reasoning_steps: List[str]  # ["收集症状", "检索文献", "鉴别诊断"]


def create_react_initial_state(session_id: str, user_id: int) -> DermaReActState:
    """创建 ReAct Agent 初始状态"""
    return DermaReActState(
        session_id=session_id,
        user_id=user_id,
        messages=[],
        chief_complaint="",
        skin_location="",
        symptoms=[],
        duration="",
        skin_analyses=[],
        knowledge_refs=[],
        possible_conditions=[],
        current_response="",
        quick_options=[],
        pending_attachments=[],
        risk_level="low",
        care_advice="",
        need_offline_visit=False,
        advice_history=[],
        diagnosis_card=None,
        reasoning_steps=[]
    )
