from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .services.auth_service import AuthService
from .services.admin_auth_service import AdminAuthService
from .models.user import User
from .models.admin_user import AdminUser

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    user_id = AuthService.verify_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    return user


def get_current_user_or_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    允许普通用户或管理员访问
    如果是管理员token，创建一个临时的User对象用于测试
    """
    token = credentials.credentials
    
    # 先尝试验证普通用户token
    user_id = AuthService.verify_token(token)
    if user_id is not None:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user
    
    # 尝试验证管理员token
    admin_id = AdminAuthService.verify_admin_token(token)
    if admin_id is not None:
        admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
        if admin:
            # 创建一个临时User对象用于测试（使用管理员ID作为user_id）
            # 检查是否已有对应的测试用户
            test_user = db.query(User).filter(User.phone == f"admin_{admin.id}").first()
            if not test_user:
                # 创建测试用户
                test_user = User(
                    phone=f"admin_{admin.id}",
                    nickname=f"管理员测试_{admin.username}",
                    is_active=True
                )
                db.add(test_user)
                db.commit()
                db.refresh(test_user)
            return test_user
    
    # 都不是有效token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"}
    )
