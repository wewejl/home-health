"""
医嘱执行监督系统 Pydantic Schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import date, time, datetime


# ========== 请求 Schemas ==========

class MedicalOrderCreateRequest(BaseModel):
    """创建医嘱请求"""
    order_type: str = Field(..., description="医嘱类型")
    title: str = Field(..., max_length=200, description="医嘱标题")
    description: Optional[str] = Field(None, description="详细说明")
    schedule_type: str = Field(..., description="调度类型")
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    frequency: Optional[str] = Field(None, max_length=50, description="频次")
    reminder_times: Optional[List[str]] = Field(default_factory=list, description="提醒时间")
    ai_generated: bool = Field(False, description="是否AI生成")
    ai_session_id: Optional[str] = Field(None, description="关联的问诊会话ID")


class MedicalOrderUpdateRequest(BaseModel):
    """更新医嘱请求"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    end_date: Optional[date] = None
    frequency: Optional[str] = None
    reminder_times: Optional[List[str]] = None


class ActivateOrderRequest(BaseModel):
    """激活医嘱请求"""
    confirm: bool = Field(..., description="确认激活")


class CompletionRecordRequest(BaseModel):
    """打卡记录请求"""
    task_instance_id: int = Field(..., description="任务实例ID")
    completion_type: str = Field(..., description="打卡类型")
    value: Optional[Dict[str, Any]] = Field(None, description="监测值")
    photo_url: Optional[str] = Field(None, max_length=500, description="照片URL")
    notes: Optional[str] = Field(None, description="备注")


# ========== 响应 Schemas ==========

class MedicalOrderResponse(BaseModel):
    """医嘱响应"""
    id: int
    patient_id: int
    doctor_id: Optional[int]
    order_type: str
    title: str
    description: Optional[str]
    schedule_type: str
    start_date: date
    end_date: Optional[date]
    frequency: Optional[str]
    reminder_times: List[str]
    ai_generated: bool
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskInstanceResponse(BaseModel):
    """任务实例响应"""
    id: int
    order_id: int
    patient_id: int
    scheduled_date: date
    scheduled_time: time
    status: str
    completed_at: Optional[datetime]
    completion_notes: Optional[str]

    # 关联医嘱信息
    order_title: Optional[str] = None
    order_type: Optional[str] = None

    class Config:
        from_attributes = True


class CompletionRecordResponse(BaseModel):
    """打卡记录响应"""
    id: int
    task_instance_id: int
    completed_by: int
    completion_type: str
    value: Optional[Dict[str, Any]]
    photo_url: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ComplianceResponse(BaseModel):
    """依从性响应"""
    date: Optional[str]
    total: int
    completed: int
    overdue: int
    pending: int
    rate: float


class WeeklyComplianceResponse(BaseModel):
    """周依从性响应"""
    daily_rates: List[float]
    average_rate: float
    dates: List[str]


class TaskListResponse(BaseModel):
    """任务列表响应"""
    date: str
    pending: List[TaskInstanceResponse]
    completed: List[TaskInstanceResponse]
    overdue: List[TaskInstanceResponse]
    summary: ComplianceResponse


class FamilyBondCreateRequest(BaseModel):
    """创建家属关系请求"""
    patient_id: int
    family_member_phone: str = Field(..., description="家属手机号")
    relationship: str = Field(..., max_length=50, description="关系")
    notification_level: str = Field("all", description="通知级别")


class FamilyBondResponse(BaseModel):
    """家属关系响应"""
    id: int
    patient_id: int
    family_member_id: int
    relationship_type: str
    notification_level: str
    family_member_name: Optional[str] = None
    family_member_phone: Optional[str] = None
    patient_name: Optional[str] = None

    class Config:
        from_attributes = True
