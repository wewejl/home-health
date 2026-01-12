from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean
from sqlalchemy.sql import func
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # 密码哈希，可为空（支持仅验证码登录的老用户）
    nickname = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    gender = Column(String(10), nullable=True)  # male, female, other
    birthday = Column(Date, nullable=True)
    
    # 紧急联系人
    emergency_contact_name = Column(String(50), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(String(20), nullable=True)
    
    # 用户状态
    is_profile_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    @property
    def has_password(self) -> bool:
        """检查用户是否设置了密码"""
        return self.password_hash is not None and len(self.password_hash) > 0
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
