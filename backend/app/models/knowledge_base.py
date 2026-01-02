from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(String(100), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    # 知识库配置
    kb_type = Column(String(20), default="vector")  # vector/document/hybrid
    vector_store_config = Column(JSON, nullable=True)
    embedding_model = Column(String(50), default="text-embedding-v1")
    
    # 统计
    total_documents = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    last_indexed_at = Column(DateTime(timezone=True), nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    doctor = relationship("Doctor", backref="knowledge_base")
    department = relationship("Department")
    documents = relationship("KnowledgeDocument", back_populates="knowledge_base", cascade="all, delete-orphan")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(String(100), ForeignKey("knowledge_bases.id"), nullable=False)
    
    # 文档信息
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    doc_type = Column(String(20), nullable=True)  # case/faq/guideline/sop
    source = Column(String(100), nullable=True)
    
    # 元数据
    tags = Column(JSON, nullable=True)  # 存储为 JSON 数组
    doc_metadata = Column(JSON, nullable=True)
    
    # 审核状态
    status = Column(String(20), default="pending")  # pending/approved/rejected
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # 向量化状态
    is_indexed = Column(Boolean, default=False)
    chunk_count = Column(Integer, default=0)
    embedding_data = Column(JSON, nullable=True)  # 存储 embedding 向量
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
