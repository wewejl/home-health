from typing import TYPE_CHECKING, List
from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from ..database import Base

if TYPE_CHECKING:
    from .admin_user import AdminUser
    from .doctor import Doctor
    from .disease import Disease


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False, nullable=False)

    # 现有关系
    doctors = relationship("Doctor", back_populates="department")
    diseases = relationship("Disease", back_populates="department")

    # ========== Phase 0 新增反向关系 ==========
    admin_users = relationship("AdminUser", back_populates="department")
