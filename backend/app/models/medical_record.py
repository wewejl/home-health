"""
病历记录模型 - 医疗档案记录
"""
import uuid
import enum
from sqlalchemy import Column, String, DateTime, Text, Date, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class MedicalRecord(Base):
    """病历记录 - 单条医疗档案记录"""
    __tablename__ = "medical_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("medical_folders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    record_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    folder = relationship("MedicalFolder", back_populates="records")
    files = relationship("MedicalFile", back_populates="record", cascade="all, delete-orphan")

    def to_dict(self, include_files=False):
        result = {
            "id": str(self.id),
            "folder_id": str(self.folder_id),
            "user_id": self.user_id,
            "title": self.title,
            "record_date": self.record_date.isoformat() if self.record_date else None,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "file_count": len(self.files) if self.files else 0,
        }
        if include_files and self.files:
            result["files"] = [file.to_dict() for file in self.files]
        return result
