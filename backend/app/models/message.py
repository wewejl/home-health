from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base


class SenderType(str, enum.Enum):
    user = "user"
    ai = "ai"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    sender = Column(Enum(SenderType), nullable=False)
    content = Column(Text, nullable=False)
    attachment_url = Column(String(255), nullable=True)
    
    # 扩展字段：支持多模态消息
    message_type = Column(String(50), default="text")  # text, image, structured_result
    attachments = Column(JSON, nullable=True)  # [{type, url, base64, metadata}]
    structured_data = Column(JSON, nullable=True)  # 结构化数据（分析结果、报告解读等）
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="messages")
