"""
医疗事件模型 - 病历资料夹核心数据结构
"""
import enum
import secrets
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class EventStatus(str, enum.Enum):
    """事件状态"""
    active = "active"
    completed = "completed"
    exported = "exported"
    archived = "archived"


class RiskLevel(str, enum.Enum):
    """风险等级"""
    low = "low"
    medium = "medium"
    high = "high"
    emergency = "emergency"


class AgentType(str, enum.Enum):
    """科室智能体类型"""
    cardio = "cardio"
    derma = "derma"
    ortho = "ortho"
    neuro = "neuro"
    general = "general"
    endo = "endo"
    gastro = "gastro"
    respiratory = "respiratory"


class AttachmentType(str, enum.Enum):
    """附件类型"""
    image = "image"
    report = "report"
    voice = "voice"


class MedicalEvent(Base):
    """医疗事件 - 病历资料夹核心实体"""
    __tablename__ = "medical_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    title = Column(String(200), nullable=False)
    department = Column(String(50), nullable=False)
    agent_type = Column(SQLEnum(AgentType), default=AgentType.general)
    status = Column(SQLEnum(EventStatus), default=EventStatus.active)
    
    chief_complaint = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.low)
    
    ai_analysis = Column(JSON, nullable=True, default=dict)
    sessions = Column(JSON, nullable=True, default=list)
    
    session_count = Column(Integer, default=0)
    attachment_count = Column(Integer, default=0)
    export_count = Column(Integer, default=0)
    
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    attachments = relationship("EventAttachment", back_populates="event", cascade="all, delete-orphan")
    notes = relationship("EventNote", back_populates="event", cascade="all, delete-orphan")
    export_records = relationship("ExportRecord", back_populates="event", cascade="all, delete-orphan")


class EventAttachment(Base):
    """事件附件"""
    __tablename__ = "event_attachments"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("medical_events.id"), nullable=False, index=True)
    
    type = Column(SQLEnum(AttachmentType), nullable=False)
    url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    filename = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_metadata = Column(JSON, nullable=True, default=dict)
    description = Column(Text, nullable=True)
    is_important = Column(Boolean, default=False)
    
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    
    event = relationship("MedicalEvent", back_populates="attachments")


class EventNote(Base):
    """事件备注"""
    __tablename__ = "event_notes"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("medical_events.id"), nullable=False, index=True)
    
    content = Column(Text, nullable=False)
    is_important = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    event = relationship("MedicalEvent", back_populates="notes")


class ExportRecord(Base):
    """导出记录"""
    __tablename__ = "export_records"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("medical_events.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    export_type = Column(String(20), nullable=False, default="pdf")
    event_ids = Column(JSON, nullable=True, default=list)
    export_options = Column(JSON, nullable=True, default=dict)
    
    file_url = Column(String(500), nullable=True)
    share_token = Column(String(100), nullable=True, unique=True, index=True)
    share_password = Column(String(100), nullable=True)
    
    expires_at = Column(DateTime(timezone=True), nullable=True)
    max_views = Column(Integer, nullable=True)
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    event = relationship("MedicalEvent", back_populates="export_records")
    access_logs = relationship("ExportAccessLog", back_populates="export_record", cascade="all, delete-orphan")
    
    @staticmethod
    def generate_share_token():
        return secrets.token_urlsafe(32)


class ExportAccessLog(Base):
    """导出访问日志"""
    __tablename__ = "export_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    export_id = Column(Integer, ForeignKey("export_records.id"), nullable=False, index=True)
    
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    export_record = relationship("ExportRecord", back_populates="access_logs")
