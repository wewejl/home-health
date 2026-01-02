from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
from ..database import get_db
from ..models.department import Department
from ..models.doctor import Doctor
from ..models.session import Session as SessionModel
from ..models.message import Message
from ..models.knowledge_base import KnowledgeDocument
from ..models.feedback import SessionFeedback
from ..models.admin_user import AdminUser, AuditLog
from ..schemas.stats import OverviewStats, DailyStats, TrendStats, DoctorStats
from .admin_auth import get_current_admin

router = APIRouter(prefix="/admin/stats", tags=["admin-stats"])


@router.get("/overview", response_model=OverviewStats)
def get_overview_stats(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    total_departments = db.query(Department).count()
    total_doctors = db.query(Doctor).count()
    active_ai_doctors = db.query(Doctor).filter(
        Doctor.is_ai == True,
        Doctor.is_active == True
    ).count()
    
    total_sessions = db.query(SessionModel).count()
    total_messages = db.query(Message).count()
    
    today_sessions = db.query(SessionModel).filter(
        SessionModel.created_at >= today_start
    ).count()
    today_messages = db.query(Message).filter(
        Message.created_at >= today_start
    ).count()
    
    pending_documents = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.status == "pending"
    ).count()
    pending_feedbacks = db.query(SessionFeedback).filter(
        SessionFeedback.status == "pending"
    ).count()
    
    return OverviewStats(
        total_departments=total_departments,
        total_doctors=total_doctors,
        active_ai_doctors=active_ai_doctors,
        total_sessions=total_sessions,
        total_messages=total_messages,
        today_sessions=today_sessions,
        today_messages=today_messages,
        pending_documents=pending_documents,
        pending_feedbacks=pending_feedbacks
    )


@router.get("/trends", response_model=TrendStats)
def get_trend_stats(
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    daily_stats = []
    today = datetime.utcnow().date()
    
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        
        sessions = db.query(SessionModel).filter(
            SessionModel.created_at >= date_start,
            SessionModel.created_at <= date_end
        ).count()
        
        messages = db.query(Message).filter(
            Message.created_at >= date_start,
            Message.created_at <= date_end
        ).count()
        
        daily_stats.append(DailyStats(
            date=date.isoformat(),
            sessions=sessions,
            messages=messages
        ))
    
    return TrendStats(daily_stats=daily_stats)


@router.get("/doctors/{doctor_id}", response_model=DoctorStats)
def get_doctor_stats(
    doctor_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="医生不存在")
    
    total_sessions = db.query(SessionModel).filter(
        SessionModel.doctor_id == doctor_id
    ).count()
    
    total_messages = db.query(Message).join(SessionModel).filter(
        SessionModel.doctor_id == doctor_id
    ).count()
    
    # 计算平均评分
    avg_rating_result = db.query(func.avg(SessionFeedback.rating)).join(
        SessionModel, SessionFeedback.session_id == SessionModel.id
    ).filter(
        SessionModel.doctor_id == doctor_id,
        SessionFeedback.rating != None
    ).scalar()
    
    feedback_count = db.query(SessionFeedback).join(
        SessionModel, SessionFeedback.session_id == SessionModel.id
    ).filter(SessionModel.doctor_id == doctor_id).count()
    
    return DoctorStats(
        doctor_id=doctor_id,
        doctor_name=doctor.name,
        total_sessions=total_sessions,
        total_messages=total_messages,
        avg_rating=float(avg_rating_result) if avg_rating_result else None,
        feedback_count=feedback_count
    )


@router.get("/departments/{dept_id}")
def get_department_stats(
    dept_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="科室不存在")
    
    doctor_ids = [d.id for d in dept.doctors] if dept.doctors else []
    
    total_doctors = len(doctor_ids)
    active_doctors = db.query(Doctor).filter(
        Doctor.department_id == dept_id,
        Doctor.is_active == True
    ).count()
    
    total_sessions = db.query(SessionModel).filter(
        SessionModel.doctor_id.in_(doctor_ids)
    ).count() if doctor_ids else 0
    
    total_messages = db.query(Message).join(SessionModel).filter(
        SessionModel.doctor_id.in_(doctor_ids)
    ).count() if doctor_ids else 0
    
    return {
        "department_id": dept_id,
        "department_name": dept.name,
        "total_doctors": total_doctors,
        "active_doctors": active_doctors,
        "total_sessions": total_sessions,
        "total_messages": total_messages
    }


@router.get("/logs")
def get_audit_logs(
    admin_user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    query = db.query(AuditLog)
    
    if admin_user_id:
        query = query.filter(AuditLog.admin_user_id == admin_user_id)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return [{
        "id": log.id,
        "admin_user_id": log.admin_user_id,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "changes": log.changes,
        "ip_address": log.ip_address,
        "created_at": log.created_at.isoformat() if log.created_at else None
    } for log in logs]
