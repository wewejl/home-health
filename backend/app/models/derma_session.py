"""
皮肤科AI问诊会话模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class DermaSession(Base):
    """皮肤科AI问诊会话"""
    __tablename__ = "derma_sessions"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 问诊状态
    stage = Column(String(20), default="greeting")  # greeting, collecting, analyzing, diagnosis, completed
    progress = Column(Integer, default=0)  # 0-100
    questions_asked = Column(Integer, default=0)
    
    # 收集的信息
    chief_complaint = Column(Text, nullable=True)  # 主诉
    symptoms = Column(JSON, default=list)  # 症状列表
    symptom_details = Column(JSON, default=dict)  # 症状详情
    skin_location = Column(String(100), nullable=True)  # 皮损部位
    duration = Column(String(100), nullable=True)  # 持续时间
    
    # 对话历史
    messages = Column(JSON, default=list)  # [{role, content, timestamp, task_type}]
    
    # 当前AI生成内容
    current_response = Column(Text, nullable=True)
    quick_options = Column(JSON, default=list)  # [{text, value, category}]
    
    # 皮肤分析结果
    skin_analyses = Column(JSON, default=list)  # 历史分析记录
    latest_analysis = Column(JSON, nullable=True)  # 最新分析结果
    
    # 报告解读结果
    report_interpretations = Column(JSON, default=list)  # 历史解读记录
    latest_interpretation = Column(JSON, nullable=True)  # 最新解读结果
    
    # 诊断结果
    possible_conditions = Column(JSON, default=list)  # [{name, confidence, description}]
    risk_level = Column(String(20), default="low")  # low, medium, high, emergency
    care_advice = Column(Text, nullable=True)  # 护理建议
    need_offline_visit = Column(Boolean, default=False)  # 是否需要线下就医
    
    # ReAct Agent 增强字段
    advice_history = Column(JSON, default=list)  # 中间建议历史 [{id, title, content, evidence, timestamp}]
    diagnosis_card = Column(JSON, nullable=True)  # 诊断卡片 {summary, conditions, risk_level, care_plan, references}
    knowledge_refs = Column(JSON, default=list)  # 知识引用 [{id, title, snippet, source, link}]
    reasoning_steps = Column(JSON, default=list)  # 推理步骤 [string]
    
    # 控制标志
    current_task = Column(String(20), default="conversation")  # conversation, skin_analysis, report_interpret
    awaiting_image = Column(Boolean, default=False)  # 是否等待图片上传
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
