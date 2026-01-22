from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    title = Column(String(50), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    hospital = Column(String(100), nullable=True)
    specialty = Column(Text, nullable=True)
    intro = Column(Text, nullable=True)
    avatar_url = Column(String(255), nullable=True)

    # 展示字段
    rating = Column(Float, default=5.0)
    monthly_answers = Column(Integer, default=0)
    avg_response_time = Column(String(20), default="5分钟")
    can_prescribe = Column(Boolean, default=False)
    is_top_hospital = Column(Boolean, default=False)

    # AI 分身核心字段
    is_ai = Column(Boolean, default=True, index=True)
    ai_persona_prompt = Column(Text, nullable=True)
    ai_model = Column(String(50), default="qwen-plus")
    ai_temperature = Column(Float, default=0.7)
    ai_max_tokens = Column(Integer, default=500)
    knowledge_base_id = Column(String(100), nullable=True)
    agent_type = Column(String(20), default="simple")  # simple/crewai/custom
    agent_config = Column(JSON, nullable=True)

    # 状态管理
    is_active = Column(Boolean, default=True, index=True)
    verified_by = Column(Integer, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    # 病历分析完成标记
    records_analyzed = Column(Boolean, default=False, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    department = relationship("Department", back_populates="doctors")
