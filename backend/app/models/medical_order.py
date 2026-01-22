"""
医嘱执行监督系统数据模型

包含：
- MedicalOrder: 医嘱主表
- TaskInstance: 任务实例表
- CompletionRecord: 打卡记录表
- FamilyBond: 患者家属关系表
"""
import enum
from datetime import date, datetime, time
from sqlalchemy import Column, Integer, String, Date, Time, DateTime, Text, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class OrderType(str, enum.Enum):
    """医嘱类型"""
    MEDICATION = "medication"    # 用药任务
    MONITORING = "monitoring"    # 监测任务
    BEHAVIOR = "behavior"        # 行为任务
    FOLLOWUP = "followup"        # 复诊任务


class ScheduleType(str, enum.Enum):
    """调度类型"""
    ONCE = "once"               # 一次性
    DAILY = "daily"             # 每日
    WEEKLY = "weekly"           # 每周
    CUSTOM = "custom"           # 自定义


class OrderStatus(str, enum.Enum):
    """医嘱状态"""
    DRAFT = "draft"             # 草稿
    ACTIVE = "active"           # 进行中
    COMPLETED = "completed"     # 已完成
    STOPPED = "stopped"         # 已停用


class TaskStatus(str, enum.Enum):
    """任务状态"""
    PENDING = "pending"         # 待完成
    COMPLETED = "completed"     # 已完成
    OVERDUE = "overdue"         # 已超时
    SKIPPED = "skipped"         # 已跳过


class NotificationLevel(str, enum.Enum):
    """通知级别"""
    ALL = "all"                 # 全部通知
    ABNORMAL = "abnormal"       # 仅异常
    SUMMARY = "summary"         # 仅摘要
    NONE = "none"               # 不通知


class CompletionType(str, enum.Enum):
    """打卡类型"""
    CHECK = "check"              # 打卡确认
    PHOTO = "photo"              # 照片证明
    VALUE = "value"              # 数值录入
    MEDICATION = "medication"    # 用药记录


class TaskInstance(Base):
    """任务实例表 - 系统根据医嘱自动生成的每日任务"""
    __tablename__ = "task_instances"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("medical_orders.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 调度信息
    scheduled_date = Column(Date, nullable=False, index=True)
    scheduled_time = Column(Time, nullable=False)

    # 状态
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)

    # 完成信息
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_notes = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    order = relationship("MedicalOrder", back_populates="task_instances")
    completion_records = relationship("CompletionRecord", back_populates="task_instance", cascade="all, delete-orphan")
    patient_rel = relationship("User", foreign_keys=[patient_id])


class MedicalOrder(Base):
    """医嘱主表 - 医生审核后生效"""
    __tablename__ = "medical_orders"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True, index=True)

    # 医嘱基本信息
    order_type = Column(SQLEnum(OrderType), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 调度信息
    schedule_type = Column(SQLEnum(ScheduleType), nullable=False, default=ScheduleType.DAILY)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    frequency = Column(String(50), nullable=True)
    reminder_times = Column(JSON, nullable=True, default=list)  # ["08:00", "12:00", "18:00"]

    # AI 生成标记
    ai_generated = Column(Boolean, default=False)
    ai_session_id = Column(String(100), nullable=True, index=True)  # 关联的问诊会话

    # 状态
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.DRAFT, index=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    task_instances = relationship("TaskInstance", back_populates="order", cascade="all, delete-orphan")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("AdminUser", foreign_keys=[doctor_id])


class CompletionRecord(Base):
    """打卡记录表 - 执行时的详细数据记录"""
    __tablename__ = "completion_records"

    id = Column(Integer, primary_key=True, index=True)
    task_instance_id = Column(Integer, ForeignKey("task_instances.id"), nullable=False, index=True)
    completed_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 打卡类型和数据
    completion_type = Column(SQLEnum(CompletionType), nullable=False)
    value = Column(JSON, nullable=True, default=dict)  # 监测值，如 {"value": 7.8, "unit": "mmol/L"}
    photo_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    task_instance = relationship("TaskInstance", back_populates="completion_records")
    completed_by_user = relationship("User", foreign_keys=[completed_by])


class FamilyBond(Base):
    """患者家属关系表"""
    __tablename__ = "family_bonds"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    family_member_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    relationship_type = Column(String(50), nullable=False)  # 父母/子女/配偶等
    notification_level = Column(SQLEnum(NotificationLevel), default=NotificationLevel.ALL)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    patient = relationship("User", foreign_keys=[patient_id])
    family_member = relationship("User", foreign_keys=[family_member_id])
