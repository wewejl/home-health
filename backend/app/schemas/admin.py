from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


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

    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "editor"
    permissions: Optional[dict] = None


class AdminUserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[dict] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


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
