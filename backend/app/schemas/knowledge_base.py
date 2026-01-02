from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class KnowledgeBaseCreate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    kb_type: str = "vector"
    vector_store_config: Optional[dict] = None
    embedding_model: str = "text-embedding-v1"


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    kb_type: Optional[str] = None
    vector_store_config: Optional[dict] = None
    embedding_model: Optional[str] = None
    is_active: Optional[bool] = None


class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    kb_type: str = "vector"
    vector_store_config: Optional[Any] = None
    embedding_model: str = "text-embedding-v1"
    total_documents: int = 0
    total_chunks: int = 0
    last_indexed_at: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KnowledgeDocumentCreate(BaseModel):
    title: str
    content: str
    doc_type: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    doc_metadata: Optional[dict] = None


class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    doc_type: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    doc_metadata: Optional[dict] = None


class KnowledgeDocumentResponse(BaseModel):
    id: int
    knowledge_base_id: str
    title: str
    content: str
    doc_type: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    doc_metadata: Optional[Any] = None
    status: str = "pending"
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    is_indexed: bool = False
    chunk_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentApproveRequest(BaseModel):
    approved: bool
    review_notes: Optional[str] = None
