"""
医生-患者关联关系模型

用于管理真实医生（admin_users）与患者（users）之间的关联关系。
支持医生"管理"或"关注"特定患者，用于医生工作台功能。

关联方式：
- 通过科室自动关联（AdminUser.department_id → Doctor.department_id）
- 通过本表手动关联（医生直接关注特定患者）

使用场景：
1. 医生可以查看自己科室内 AI 分身接待过的患者（通过科室关联）
2. 医生可以手动关注特定患者，即使该患者不属于本科室（通过本表）
3. 支持患者转诊场景（将患者从一个医生转给另一个医生）
"""
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

if TYPE_CHECKING:
    from .admin_user import AdminUser
    from .user import User


__all__ = ["DoctorPatientRelationship", "RelationshipType"]


class RelationshipType:
    """关联类型常量"""
    PRIMARY = "primary"       # 主治医生
    CONSULTING = "consulting" # 会诊
    TEMPORARY = "temporary"   # 临时


class DoctorPatientRelationship(Base):
    """
    医生-患者关联关系表

    记录真实医生（admin_users）与患者（users）之间的关联关系。

    属性:
        id: 主键
        doctor_id: 医生 ID（指向 admin_users.id）
        patient_id: 患者 ID（指向 users.id）
        relationship_type: 关联类型（primary/consulting/temporary）
        is_active: 关联是否有效
        assigned_at: 关联建立时间
        assigned_by: 创建人 ID
        notes: 备注信息
        created_at: 创建时间
        updated_at: 更新时间
    """
    __tablename__ = "doctor_patient_relationships"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 外键关联
    doctor_id = Column(
        Integer,
        ForeignKey("admin_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    patient_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 关联类型
    relationship_type = Column(
        String(20),
        nullable=False,
        default=RelationshipType.TEMPORARY,
        index=True
    )

    # 关联状态
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True
    )

    # 关联建立信息
    assigned_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    assigned_by = Column(Integer, ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)

    # 备注信息
    notes = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # 关系
    doctor = relationship("AdminUser", back_populates="patient_relationships", foreign_keys=[doctor_id])
    patient = relationship("User", back_populates="doctor_relationships")
    assigner = relationship("AdminUser", foreign_keys=[assigned_by])

    # 复合索引（提升查询性能）
    __table_args__ = (
        Index("idx_doctor_patient_active", "doctor_id", "patient_id", "is_active"),
        Index("idx_patient_doctor_active", "patient_id", "doctor_id", "is_active"),
    )

    def __repr__(self):
        return (
            f"<DoctorPatientRelationship("
            f"doctor_id={self.doctor_id}, "
            f"patient_id={self.patient_id}, "
            f"type={self.relationship_type}, "
            f"active={self.is_active})>"
        )

    def activate(self):
        """激活关联"""
        self.is_active = True

    def deactivate(self):
        """停用关联"""
        self.is_active = False
