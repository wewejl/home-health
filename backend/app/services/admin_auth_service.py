from datetime import datetime, timedelta
from jose import jwt
import hashlib
from sqlalchemy.orm import Session
from ..models.admin_user import AdminUser
from ..config import get_settings

settings = get_settings()


class AdminAuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

    @staticmethod
    def authenticate_admin(db: Session, username: str, password: str) -> AdminUser | None:
        admin = db.query(AdminUser).filter(
            AdminUser.username == username,
            AdminUser.is_active == True
        ).first()
        
        if not admin:
            return None
        
        if not AdminAuthService.verify_password(password, admin.password_hash):
            return None
        
        # 更新最后登录时间
        admin.last_login_at = datetime.utcnow()
        db.commit()
        
        return admin

    @staticmethod
    def create_admin_token(admin_id: int) -> str:
        expire = datetime.utcnow() + timedelta(hours=settings.ADMIN_JWT_EXPIRE_HOURS)
        payload = {
            "sub": str(admin_id),
            "type": "admin",
            "exp": expire
        }
        return jwt.encode(payload, settings.ADMIN_JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def verify_admin_token(token: str) -> int | None:
        try:
            payload = jwt.decode(token, settings.ADMIN_JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            if payload.get("type") != "admin":
                return None
            return int(payload.get("sub"))
        except Exception:
            return None

    @staticmethod
    def create_admin_user(db: Session, username: str, password: str, email: str = None, role: str = "editor") -> AdminUser:
        admin = AdminUser(
            username=username,
            password_hash=AdminAuthService.hash_password(password),
            email=email,
            role=role
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin

    @staticmethod
    def init_default_admin(db: Session):
        """初始化默认管理员账号"""
        existing = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        if not existing:
            AdminAuthService.create_admin_user(
                db=db,
                username="admin",
                password="admin123",
                email="admin@xinlin.com",
                role="admin"
            )
            print("默认管理员账号已创建: admin / admin123")
