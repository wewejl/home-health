from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from ..database import get_db
from ..models.feedback import SessionFeedback
from ..models.admin_user import AdminUser
from ..schemas.feedback import FeedbackResponse, FeedbackHandleRequest
from .admin_auth import get_current_admin

router = APIRouter(prefix="/admin/feedbacks", tags=["admin-feedbacks"])


@router.get("", response_model=List[FeedbackResponse])
def list_feedbacks(
    status: Optional[str] = None,
    feedback_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    query = db.query(SessionFeedback)
    
    if status:
        query = query.filter(SessionFeedback.status == status)
    if feedback_type:
        query = query.filter(SessionFeedback.feedback_type == feedback_type)
    
    feedbacks = query.order_by(SessionFeedback.created_at.desc()).offset(skip).limit(limit).all()
    return [FeedbackResponse.model_validate(f) for f in feedbacks]


@router.get("/{feedback_id}", response_model=FeedbackResponse)
def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    feedback = db.query(SessionFeedback).filter(SessionFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    return FeedbackResponse.model_validate(feedback)


@router.put("/{feedback_id}/handle", response_model=FeedbackResponse)
def handle_feedback(
    feedback_id: int,
    request: FeedbackHandleRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    feedback = db.query(SessionFeedback).filter(SessionFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    feedback.status = request.status
    feedback.resolution_notes = request.resolution_notes
    feedback.handled_by = admin.id
    feedback.handled_at = datetime.utcnow()
    
    db.commit()
    db.refresh(feedback)
    return FeedbackResponse.model_validate(feedback)


@router.get("/stats/summary")
def get_feedback_stats(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    total = db.query(SessionFeedback).count()
    pending = db.query(SessionFeedback).filter(SessionFeedback.status == "pending").count()
    reviewed = db.query(SessionFeedback).filter(SessionFeedback.status == "reviewed").count()
    resolved = db.query(SessionFeedback).filter(SessionFeedback.status == "resolved").count()
    
    # 按类型统计
    helpful = db.query(SessionFeedback).filter(SessionFeedback.feedback_type == "helpful").count()
    unhelpful = db.query(SessionFeedback).filter(SessionFeedback.feedback_type == "unhelpful").count()
    unsafe = db.query(SessionFeedback).filter(SessionFeedback.feedback_type == "unsafe").count()
    inaccurate = db.query(SessionFeedback).filter(SessionFeedback.feedback_type == "inaccurate").count()
    
    return {
        "total": total,
        "by_status": {
            "pending": pending,
            "reviewed": reviewed,
            "resolved": resolved
        },
        "by_type": {
            "helpful": helpful,
            "unhelpful": unhelpful,
            "unsafe": unsafe,
            "inaccurate": inaccurate
        }
    }
