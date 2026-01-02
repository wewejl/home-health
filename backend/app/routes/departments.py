from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.department import DepartmentResponse
from ..schemas.doctor import DoctorResponse
from ..models.department import Department
from ..models.doctor import Doctor

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=List[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).order_by(Department.sort_order).all()
    return [DepartmentResponse.model_validate(d) for d in departments]


@router.get("/{department_id}/doctors", response_model=List[DoctorResponse])
def get_doctors_by_department(department_id: int, db: Session = Depends(get_db)):
    doctors = db.query(Doctor).filter(Doctor.department_id == department_id).all()
    return [DoctorResponse.model_validate(d) for d in doctors]
