from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import re
from ..database import get_db
from ..models.admin_user import AdminUser, AuditLog
from ..services.admin_auth_service import AdminAuthService
from ..schemas.admin import (
    AdminLoginRequest, AdminLoginResponse, AdminUserResponse,
    AdminUserCreate, AdminUserUpdate
)
from ..config import get_settings

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])
security = HTTPBearer(auto_error=False)

# 测试模式：从配置文件读取（可通过环境变量 ADMIN_TEST_MODE 关闭）
settings = get_settings()
TEST_MODE = getattr(settings, 'ADMIN_TEST_MODE', settings.TEST_MODE)


# ============ 辅助函数 ============

def validate_password_complexity(password: str) -> tuple[bool, str]:
    """验证密码复杂度
    要求：
    - 最少 8 个字符
    - 至少包含一个小写字母
    - 至少包含一个大写字母
    - 至少包含一个数字
    """
    if len(password) < 8:
        return False, "密码长度至少 8 个字符"
    if not re.search(r'[a-z]', password):
        return False, "密码必须包含至少一个小写字母"
    if not re.search(r'[A-Z]', password):
        return False, "密码必须包含至少一个大写字母"
    if not re.search(r'\d', password):
        return False, "密码必须包含至少一个数字"
    return True, ""


def create_audit_log(
    db: Session,
    admin_user_id: Optional[int],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    changes: Optional[dict] = None,
    ip_address: Optional[str] = None
):
    """创建审计日志"""
    log = AuditLog(
        admin_user_id=admin_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()


def get_client_ip(request: Request) -> Optional[str]:
    """获取客户端 IP 地址"""
    # 检查代理头
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else None


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
    # 测试模式：返回测试医生
    if TEST_MODE:
        test_doctor = db.query(AdminUser).filter(AdminUser.username == "test_doctor").first()
        if not test_doctor:
            test_doctor = AdminUser(
                username="test_doctor",
                email="doctor@example.com",
                role="doctor",
                is_active=True
            )
            test_doctor.password_hash = AdminAuthService.hash_password("test123")
            db.add(test_doctor)
            db.commit()
            db.refresh(test_doctor)
        return test_doctor

    # 生产模式：验证 token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的医生凭证",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = credentials.credentials
    admin_id = AdminAuthService.verify_admin_token(token)

    if admin_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的医生凭证",
            headers={"WWW-Authenticate": "Bearer"}
        )

    doctor = db.query(AdminUser).filter(
        AdminUser.id == admin_id,
        AdminUser.is_active == True,
        AdminUser.role == "doctor"
    ).first()
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要医生权限"
        )

    return doctor


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(
    request: AdminLoginRequest,
    db: Session = Depends(get_db),
    http_request: Request = None
):
    # 密码复杂度检查（仅针对新用户注册时，此处保留用于未来扩展）
    client_ip = get_client_ip(http_request) if http_request else None

    admin = AdminAuthService.authenticate_admin(db, request.username, request.password)

    if not admin:
        # 记录失败的登录尝试
        create_audit_log(
            db=db,
            admin_user_id=None,
            action="login_failed",
            resource_type="auth",
            changes={"username": request.username},
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    token = AdminAuthService.create_admin_token(admin.id)

    # 记录成功的登录
    create_audit_log(
        db=db,
        admin_user_id=admin.id,
        action="login_success",
        resource_type="auth",
        changes={"username": request.username},
        ip_address=client_ip
    )

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
    admin: AdminUser = Depends(require_admin_role),
    http_request: Request = None
):
    # 密码复杂度检查
    is_valid, error_msg = validate_password_complexity(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

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

    # 记录审计日志
    create_audit_log(
        db=db,
        admin_user_id=admin.id,
        action="create",
        resource_type="admin_user",
        resource_id=str(new_admin.id),
        changes={
            "username": request.username,
            "email": request.email,
            "role": request.role
        },
        ip_address=get_client_ip(http_request)
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
