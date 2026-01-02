from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from ..database import get_db
from ..models.department import Department
from ..models.admin_user import AdminUser, AuditLog
from ..schemas.department import DepartmentResponse
from .admin_auth import get_current_admin

router = APIRouter(prefix="/admin/departments", tags=["admin-departments"])


class DepartmentCreate(BaseModel):
    name: str
    description: str = None
    icon: str = None
    sort_order: int = 0
    is_active: bool = True


class DepartmentUpdate(BaseModel):
    name: str = None
    description: str = None
    icon: str = None
    sort_order: int = None
    is_active: bool = None


class DepartmentDetailResponse(BaseModel):
    id: int
    name: str
    description: str = None
    icon: str = None
    sort_order: int = 0
    is_active: bool = True
    doctor_count: int = 0

    class Config:
        from_attributes = True


@router.get("", response_model=List[DepartmentDetailResponse])
def list_departments(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    departments = db.query(Department).order_by(Department.sort_order).all()
    result = []
    for dept in departments:
        doctor_count = len(dept.doctors) if dept.doctors else 0
        result.append(DepartmentDetailResponse(
            id=dept.id,
            name=dept.name,
            description=dept.description,
            icon=dept.icon,
            sort_order=dept.sort_order,
            is_active=getattr(dept, 'is_active', True),
            doctor_count=doctor_count
        ))
    return result


@router.post("", response_model=DepartmentDetailResponse)
def create_department(
    request: DepartmentCreate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    dept = Department(
        name=request.name,
        description=request.description,
        icon=request.icon,
        sort_order=request.sort_order
    )
    db.add(dept)
    
    log = AuditLog(
        admin_user_id=admin.id,
        action="create",
        resource_type="department",
        changes=request.model_dump()
    )
    db.add(log)
    
    db.commit()
    db.refresh(dept)
    
    log.resource_id = str(dept.id)
    db.commit()
    
    return DepartmentDetailResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        icon=dept.icon,
        sort_order=dept.sort_order,
        is_active=True,
        doctor_count=0
    )


@router.get("/{dept_id}", response_model=DepartmentDetailResponse)
def get_department(
    dept_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="科室不存在")
    
    doctor_count = len(dept.doctors) if dept.doctors else 0
    return DepartmentDetailResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        icon=dept.icon,
        sort_order=dept.sort_order,
        is_active=getattr(dept, 'is_active', True),
        doctor_count=doctor_count
    )


@router.put("/{dept_id}", response_model=DepartmentDetailResponse)
def update_department(
    dept_id: int,
    request: DepartmentUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="科室不存在")
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(dept, key):
            setattr(dept, key, value)
    
    db.commit()
    db.refresh(dept)
    
    doctor_count = len(dept.doctors) if dept.doctors else 0
    return DepartmentDetailResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        icon=dept.icon,
        sort_order=dept.sort_order,
        is_active=getattr(dept, 'is_active', True),
        doctor_count=doctor_count
    )


@router.delete("/{dept_id}")
def delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="科室不存在")
    
    if dept.doctors and len(dept.doctors) > 0:
        raise HTTPException(status_code=400, detail="科室下还有医生，无法删除")
    
    db.delete(dept)
    db.commit()
    return {"message": "删除成功"}
