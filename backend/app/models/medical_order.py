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
