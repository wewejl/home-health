"""
远程查房系统 Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


# ============================================
# 患者卡片响应
# ============================================

class PatientCardResponse(BaseModel):
    """患者卡片响应"""
    id: int
    name: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    last_seen: str  # "10分钟前"
    last_consultation: str  # "2小时前"
    completion_rate: int  # 今日完成率 0-100
    total_tasks: int
    completed_tasks: int
    status: str  # "danger" | "warning" | "success"
    alerts: List[str] = []
    risk_level: Optional[str] = None  # "high" | "medium" | "low"

    class Config:
        from_attributes = True


# ============================================
# 患者列表响应
# ============================================

class PatientListResponse(BaseModel):
    """患者列表响应"""
    patients: List[PatientCardResponse]
    stats: Dict[str, int]


# ============================================
# 对话消息响应
# ============================================

class ChatMessageResponse(BaseModel):
    """对话消息响应"""
    id: int
    content: str
    is_ai: bool
    time: str  # "HH:MM"
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# 医嘱任务响应
# ============================================

class RoundingTaskResponse(BaseModel):
    """医嘱任务响应"""
    id: int
    title: str
    order_type: str  # "medication" | "monitoring" | "behavior" | "followup"
    scheduled_time: str  # "HH:MM"
    status: str  # "pending" | "completed" | "overdue"
    completed_at: Optional[str] = None
    value: Optional[Dict[str, Any]] = None  # 监测数值，如 {"value": 7.8, "unit": "mmol/L"}
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# 患者详情响应
# ============================================

class PatientDetailResponse(BaseModel):
    """患者详情响应"""
    # 基本信息
    id: int
    name: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    condition: Optional[str] = None  # 患者类型标签，如"2型糖尿病患者"

    # 时间信息
    last_seen: str
    last_consultation: str

    # 预警信息
    alerts: List[Dict[str, str]] = []

    # 今日统计
    total_tasks: int
    completed_tasks: int
    completion_rate: int

    # 最近对话（最近5条）
    recent_messages: List[ChatMessageResponse]

    # 今日医嘱
    today_tasks: List[RoundingTaskResponse]

    # 依从性数据
    compliance_rate: int  # 近7天平均完成率
    daily_compliance: List[Dict[str, Any]]  # 每日完成率 [{"date": "01-17", "rate": 75}, ...]

    class Config:
        from_attributes = True
