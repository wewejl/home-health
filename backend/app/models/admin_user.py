from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

if TYPE_CHECKING:
    from .department import Department


__all__ = ["AdminUser", "AuditLog", "AdminRole"]


# 角色常量（用于代码提示和验证）
class AdminRole:
    """AdminUser 角色常量

    使用方式:
        from app.models.admin_user import AdminUser, AdminRole

        user = AdminUser(role=AdminRole.DOCTOR)
        if user.role == AdminRole.DOCTOR:
            # 处理医生角色逻辑
            pass
    """
    ADMIN = "admin"          # 系统管理员
    DOCTOR = "doctor"        # 医生
    EDITOR = "editor"        # 内容编辑
    REVIEWER = "reviewer"    # 审核员


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    role = Column(String(20), default="editor")  # admin/editor/reviewer/doctor
    permissions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ========== Phase 0 新增字段 ==========

    # 科室关联（医生角色用于关联 AI 分身）
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department", back_populates="admin_users")

    # 医生专属属性
    doctor_attributes = Column(JSON, nullable=True)
    # {
    #   "title": "主治医师",
    #   "specialty": "皮肤科",
    #   "license_no": "执业医师证号",
    #   "hospital": "医院名称"
    # }


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, nullable=True)
    action = Column(String(50), nullable=False)  # create/update/delete/approve
    resource_type = Column(String(50), nullable=True)  # doctor/knowledge_base/document
    resource_id = Column(String(100), nullable=True)
    changes = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
