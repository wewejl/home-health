from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Dict
from datetime import datetime


# ========== Phase 0: 医生属性验证 Schema ==========
class DoctorAttributes(BaseModel):
    """医生专属属性验证"""
    title: Optional[str] = Field(None, max_length=50, description="职称，如：主治医师、副主任医师")
    specialty: Optional[str] = Field(None, max_length=50, description="专科")
    license_no: Optional[str] = Field(None, max_length=50, description="执业医师证号")
    hospital: Optional[str] = Field(None, max_length=100, description="医院名称")

    class Config:
        extra = "allow"  # 允许额外字段以支持未来扩展


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: "AdminUserResponse"


class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str = "editor"
    permissions: Optional[Any] = None
    is_active: bool = True
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    # ========== Phase 0 新增字段 ==========
    department_id: Optional[int] = None
    doctor_attributes: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "editor"
    permissions: Optional[dict] = None
    # ========== Phase 0 新增字段 ==========
    department_id: Optional[int] = None
    doctor_attributes: Optional[DoctorAttributes] = None


class AdminUserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[dict] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    # ========== Phase 0 新增字段 ==========
    department_id: Optional[int] = None
    doctor_attributes: Optional[Dict[str, Any]] = None


class AuditLogResponse(BaseModel):
    id: int
    admin_user_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    changes: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


AdminLoginResponse.model_rebuild()
