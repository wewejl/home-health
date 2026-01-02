from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from ..database import get_db
from ..models.doctor import Doctor
from ..models.department import Department
from ..models.admin_user import AdminUser, AuditLog
from ..schemas.doctor import DoctorCreate, DoctorUpdate, DoctorDetailResponse, DoctorResponse
from ..services.qwen_service import QwenService
from ..services.knowledge_service import KnowledgeService
from .admin_auth import get_current_admin

router = APIRouter(prefix="/admin/doctors", tags=["admin-doctors"])


@router.get("", response_model=List[DoctorDetailResponse])
def list_doctors(
    department_id: Optional[int] = None,
    is_ai: Optional[bool] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    query = db.query(Doctor)
    
    if department_id is not None:
        query = query.filter(Doctor.department_id == department_id)
    if is_ai is not None:
        query = query.filter(Doctor.is_ai == is_ai)
    if is_active is not None:
        query = query.filter(Doctor.is_active == is_active)
    
    doctors = query.order_by(Doctor.id.desc()).offset(skip).limit(limit).all()
    return [DoctorDetailResponse.model_validate(d) for d in doctors]


@router.post("", response_model=DoctorDetailResponse)
def create_doctor(
    request: DoctorCreate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    # 验证科室存在
    dept = db.query(Department).filter(Department.id == request.department_id).first()
    if not dept:
        raise HTTPException(status_code=400, detail="科室不存在")
    
    doctor = Doctor(**request.model_dump())
    db.add(doctor)
    
    # 记录审计日志
    log = AuditLog(
        admin_user_id=admin.id,
        action="create",
        resource_type="doctor",
        resource_id=str(doctor.id) if doctor.id else "new",
        changes=request.model_dump()
    )
    db.add(log)
    
    db.commit()
    db.refresh(doctor)
    
    # 更新日志中的 resource_id
    log.resource_id = str(doctor.id)
    db.commit()
    
    return DoctorDetailResponse.model_validate(doctor)


@router.get("/{doctor_id}", response_model=DoctorDetailResponse)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    return DoctorDetailResponse.model_validate(doctor)


@router.put("/{doctor_id}", response_model=DoctorDetailResponse)
def update_doctor(
    doctor_id: int,
    request: DoctorUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(doctor, key, value)
    
    # 记录审计日志
    log = AuditLog(
        admin_user_id=admin.id,
        action="update",
        resource_type="doctor",
        resource_id=str(doctor_id),
        changes=update_data
    )
    db.add(log)
    
    db.commit()
    db.refresh(doctor)
    return DoctorDetailResponse.model_validate(doctor)


@router.delete("/{doctor_id}")
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    
    # 记录审计日志
    log = AuditLog(
        admin_user_id=admin.id,
        action="delete",
        resource_type="doctor",
        resource_id=str(doctor_id)
    )
    db.add(log)
    
    db.delete(doctor)
    db.commit()
    return {"message": "删除成功"}


@router.put("/{doctor_id}/activate")
def toggle_doctor_active(
    doctor_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    
    doctor.is_active = is_active
    if is_active and not doctor.verified_at:
        doctor.verified_by = admin.id
        doctor.verified_at = datetime.utcnow()
    
    db.commit()
    return {"message": "状态已更新", "is_active": is_active}


@router.post("/{doctor_id}/test")
async def test_doctor_ai(
    doctor_id: int,
    message: str = Query(..., description="测试消息"),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    
    # 获取 RAG 上下文
    rag_context = ""
    if doctor.knowledge_base_id:
        rag_context = KnowledgeService.get_context_for_query(
            db, doctor.knowledge_base_id, message
        )
    
    # 调用 AI
    response = await QwenService.get_ai_response(
        user_message=message,
        doctor_name=doctor.name,
        doctor_title=doctor.title or "主治医师",
        specialty=doctor.specialty or "全科医学",
        persona_prompt=doctor.ai_persona_prompt,
        rag_context=rag_context,
        model=doctor.ai_model,
        temperature=doctor.ai_temperature,
        max_tokens=doctor.ai_max_tokens
    )
    
    return {
        "question": message,
        "answer": response,
        "rag_context": rag_context[:500] if rag_context else None,
        "model": doctor.ai_model,
        "temperature": doctor.ai_temperature
    }
