from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class SessionFeedback(Base):
    __tablename__ = "session_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 反馈内容
    rating = Column(Integer, nullable=True)  # 1-5
    feedback_type = Column(String(20), nullable=True)  # helpful/unhelpful/unsafe/inaccurate
    feedback_text = Column(Text, nullable=True)
    
    # 处理状态
    status = Column(String(20), default="pending")  # pending/reviewed/resolved
    handled_by = Column(Integer, nullable=True)
    handled_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session")
    message = relationship("Message")
    user = relationship("User")
