from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..schemas.department import DepartmentResponse
from ..schemas.doctor import DoctorResponse
from ..models.department import Department
from ..models.doctor import Doctor

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=List[DepartmentResponse])
def get_departments(
    primary_only: Optional[bool] = Query(False, description="只返回主要科室（用于问医生页面）"),
    db: Session = Depends(get_db)
):
    """获取科室列表

    - primary_only=true: 只返回 12 个主要科室（问医生页面使用）
    - primary_only=false: 返回所有科室（问疾病页面使用）
    """
    query = db.query(Department).order_by(Department.sort_order)

    if primary_only:
        query = query.filter(Department.is_primary == True)

    departments = query.all()
    return [DepartmentResponse.model_validate(d) for d in departments]


@router.get("/{department_id}/doctors", response_model=List[DoctorResponse])
def get_doctors_by_department(department_id: int, db: Session = Depends(get_db)):
    doctors = db.query(Doctor).filter(Doctor.department_id == department_id).all()
    return [DoctorResponse.model_validate(d) for d in doctors]
