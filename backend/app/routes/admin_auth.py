from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.admin_user import AdminUser
from ..services.admin_auth_service import AdminAuthService
from ..schemas.admin import (
    AdminLoginRequest, AdminLoginResponse, AdminUserResponse,
    AdminUserCreate, AdminUserUpdate
)

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])
security = HTTPBearer(auto_error=False)

# 测试模式：禁用所有认证检查
TEST_MODE = True


def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """测试模式：直接返回测试管理员，无需认证"""
    # 测试模式：返回测试管理员
    if TEST_MODE:
        test_admin = db.query(AdminUser).filter(AdminUser.username == "test_admin").first()
        if not test_admin:
            test_admin = AdminUser(
                username="test_admin",
                email="test@example.com",
                role="admin",
                is_active=True
            )
            test_admin.password_hash = AdminAuthService.hash_password("test123")
            db.add(test_admin)
            db.commit()
            db.refresh(test_admin)
        return test_admin

    # 生产模式：验证 token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的管理员凭证",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = credentials.credentials
    admin_id = AdminAuthService.verify_admin_token(token)

    if admin_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的管理员凭证",
            headers={"WWW-Authenticate": "Bearer"}
        )

    admin = db.query(AdminUser).filter(AdminUser.id == admin_id, AdminUser.is_active == True).first()
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员不存在或已禁用"
        )

    return admin


def require_admin_role(admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
    # 测试模式下直接返回
    if TEST_MODE:
        return admin
    if admin.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return admin


def get_current_doctor(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """获取当前登录的医生（role 必须为 'doctor'）"""
    admin = get_current_admin(credentials, db)

    # 验证角色
    if admin.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要医生权限"
        )

    return admin


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = AdminAuthService.authenticate_admin(db, request.username, request.password)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    token = AdminAuthService.create_admin_token(admin.id)
    
    return AdminLoginResponse(
        access_token=token,
        admin=AdminUserResponse.model_validate(admin)
    )


@router.get("/me", response_model=AdminUserResponse)
def get_current_admin_info(admin: AdminUser = Depends(get_current_admin)):
    return AdminUserResponse.model_validate(admin)


@router.post("/logout")
def admin_logout():
    return {"message": "已登出"}


@router.post("/users", response_model=AdminUserResponse)
def create_admin_user(
    request: AdminUserCreate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin_role)
):
    existing = db.query(AdminUser).filter(AdminUser.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 处理医生属性（将 Pydantic model 转为 dict）
    doctor_attrs = None
    if request.doctor_attributes:
        doctor_attrs = request.doctor_attributes.model_dump(exclude_none=True)

    new_admin = AdminAuthService.create_admin_user(
        db=db,
        username=request.username,
        password=request.password,
        email=request.email,
        role=request.role,
        department_id=request.department_id,
        doctor_attributes=doctor_attrs
    )
    return AdminUserResponse.model_validate(new_admin)


@router.get("/users", response_model=list[AdminUserResponse])
def list_admin_users(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin_role)
):
    users = db.query(AdminUser).all()
    return [AdminUserResponse.model_validate(u) for u in users]


@router.put("/users/{user_id}", response_model=AdminUserResponse)
def update_admin_user(
    user_id: int,
    request: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin_role)
):
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if request.email is not None:
        user.email = request.email
    if request.role is not None:
        user.role = request.role
    if request.permissions is not None:
        user.permissions = request.permissions
    if request.is_active is not None:
        user.is_active = request.is_active
    if request.password:
        user.password_hash = AdminAuthService.hash_password(request.password)
    # Phase 0 新增字段
    if request.department_id is not None:
        user.department_id = request.department_id
    if request.doctor_attributes is not None:
        user.doctor_attributes = request.doctor_attributes

    db.commit()
    db.refresh(user)
    return AdminUserResponse.model_validate(user)
