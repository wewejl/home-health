from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class DiagnosisSession(Base):
    """AI诊室问诊会话"""
    __tablename__ = "diagnosis_sessions"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 问诊状态
    stage = Column(String(20), default="greeting")  # greeting, collecting, deep_inquiry, diagnosis, completed
    progress = Column(Integer, default=0)  # 0-100
    questions_asked = Column(Integer, default=0)
    
    # 收集的信息
    chief_complaint = Column(Text, nullable=True)  # 主诉
    symptoms = Column(JSON, default=list)  # 症状列表
    symptom_details = Column(JSON, default=dict)  # 症状详情
    
    # 对话历史
    messages = Column(JSON, default=list)  # [{role, content, timestamp, quick_options}]
    
    # 当前AI生成内容
    current_question = Column(Text, nullable=True)
    quick_options = Column(JSON, default=list)  # [{text, value, category}]
    reasoning = Column(Text, nullable=True)
    
    # 诊断结果
    possible_diseases = Column(JSON, default=list)  # [{name, probability, description}]
    risk_level = Column(String(20), nullable=True)  # low, medium, high, emergency
    recommendations = Column(JSON, default=dict)  # {department, urgency, lifestyle, ...}
    
    # 控制标志
    can_conclude = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
