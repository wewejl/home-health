"""
医疗文件模型 - 病历附件文件
"""
import uuid
import enum
from sqlalchemy import Column, String, DateTime, BigInteger, Integer, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class FileType(str, enum.Enum):
    """文件类型枚举"""
    image = "image"
    pdf = "pdf"
    video = "video"
    audio = "audio"
    document = "document"


class MedicalFile(Base):
    """医疗文件 - 病历附件文件"""
    __tablename__ = "medical_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    record_id = Column(UUID(as_uuid=True), ForeignKey("medical_records.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # image, pdf, video, audio, document
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # 字节
    url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    record = relationship("MedicalRecord", back_populates="files")

    @property
    def file_type_enum(self) -> FileType:
        """将字符串 file_type 转换为枚举"""
        return FileType(self.file_type) if self.file_type else FileType.document

    def to_dict(self):
        return {
            "id": str(self.id),
            "record_id": str(self.record_id),
            "user_id": self.user_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
