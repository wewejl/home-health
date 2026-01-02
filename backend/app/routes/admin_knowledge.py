from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from ..database import get_db
from ..models.knowledge_base import KnowledgeBase, KnowledgeDocument
from ..models.admin_user import AdminUser, AuditLog
from ..schemas.knowledge_base import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse,
    KnowledgeDocumentCreate, KnowledgeDocumentUpdate, KnowledgeDocumentResponse,
    DocumentApproveRequest
)
from ..services.knowledge_service import KnowledgeService
from .admin_auth import get_current_admin

router = APIRouter(prefix="/admin/knowledge-bases", tags=["admin-knowledge"])


@router.get("", response_model=List[KnowledgeBaseResponse])
def list_knowledge_bases(
    doctor_id: Optional[int] = None,
    department_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    query = db.query(KnowledgeBase)
    
    if doctor_id is not None:
        query = query.filter(KnowledgeBase.doctor_id == doctor_id)
    if department_id is not None:
        query = query.filter(KnowledgeBase.department_id == department_id)
    if is_active is not None:
        query = query.filter(KnowledgeBase.is_active == is_active)
    
    kbs = query.all()
    return [KnowledgeBaseResponse.model_validate(kb) for kb in kbs]


@router.post("", response_model=KnowledgeBaseResponse)
def create_knowledge_base(
    request: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    existing = db.query(KnowledgeBase).filter(KnowledgeBase.id == request.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="知识库ID已存在")
    
    kb = KnowledgeBase(**request.model_dump())
    db.add(kb)
    
    log = AuditLog(
        admin_user_id=admin.id,
        action="create",
        resource_type="knowledge_base",
        resource_id=request.id,
        changes=request.model_dump()
    )
    db.add(log)
    
    db.commit()
    db.refresh(kb)
    return KnowledgeBaseResponse.model_validate(kb)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return KnowledgeBaseResponse.model_validate(kb)


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
def update_knowledge_base(
    kb_id: str,
    request: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(kb, key, value)
    
    db.commit()
    db.refresh(kb)
    return KnowledgeBaseResponse.model_validate(kb)


@router.delete("/{kb_id}")
def delete_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    db.delete(kb)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{kb_id}/reindex")
def reindex_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 更新统计
    KnowledgeService.update_kb_stats(db, kb_id)
    kb.last_indexed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "重新索引完成", "total_documents": kb.total_documents}


# 文档管理
@router.get("/{kb_id}/documents", response_model=List[KnowledgeDocumentResponse])
def list_documents(
    kb_id: str,
    status: Optional[str] = None,
    doc_type: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    query = db.query(KnowledgeDocument).filter(KnowledgeDocument.knowledge_base_id == kb_id)
    
    if status:
        query = query.filter(KnowledgeDocument.status == status)
    if doc_type:
        query = query.filter(KnowledgeDocument.doc_type == doc_type)
    
    docs = query.order_by(KnowledgeDocument.created_at.desc()).all()
    return [KnowledgeDocumentResponse.model_validate(d) for d in docs]


@router.post("/{kb_id}/documents", response_model=KnowledgeDocumentResponse)
def create_document(
    kb_id: str,
    request: KnowledgeDocumentCreate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    doc = KnowledgeService.add_document(
        db=db,
        knowledge_base_id=kb_id,
        title=request.title,
        content=request.content,
        doc_type=request.doc_type,
        source=request.source,
        tags=request.tags,
        metadata=request.metadata
    )
    return KnowledgeDocumentResponse.model_validate(doc)


# 单独的文档路由
documents_router = APIRouter(prefix="/admin/documents", tags=["admin-documents"])


@documents_router.get("/{doc_id}", response_model=KnowledgeDocumentResponse)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return KnowledgeDocumentResponse.model_validate(doc)


@documents_router.put("/{doc_id}", response_model=KnowledgeDocumentResponse)
def update_document(
    doc_id: int,
    request: KnowledgeDocumentUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(doc, key, value)
    
    doc.status = "pending"  # 修改后重新进入审核
    doc.is_indexed = False
    
    db.commit()
    db.refresh(doc)
    return KnowledgeDocumentResponse.model_validate(doc)


@documents_router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    kb_id = doc.knowledge_base_id
    db.delete(doc)
    db.commit()
    
    # 更新知识库统计
    KnowledgeService.update_kb_stats(db, kb_id)
    
    return {"message": "删除成功"}


@documents_router.post("/{doc_id}/approve", response_model=KnowledgeDocumentResponse)
def approve_document(
    doc_id: int,
    request: DocumentApproveRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    doc = KnowledgeService.approve_document(
        db=db,
        doc_id=doc_id,
        approved=request.approved,
        reviewed_by=admin.id,
        review_notes=request.review_notes
    )
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 更新知识库统计
    KnowledgeService.update_kb_stats(db, doc.knowledge_base_id)
    
    return KnowledgeDocumentResponse.model_validate(doc)
