"""
医嘱执行监督系统 Pydantic Schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import date, time, datetime


# ========== 请求 Schemas ==========

class OrderItemCreate(BaseModel):
    """医嘱项目创建（药品/检查）"""
    item_type: str = Field(..., description="项目类型: drug/examination")
    drug_id: Optional[int] = Field(None, description="药品ID（药品类型时必填）")
    name: str = Field(..., description="药品/检查名称")
    dosage: Optional[str] = Field(None, max_length=50, description="用法用量")
    frequency: Optional[str] = Field(None, max_length=50, description="用药频率")
    duration: Optional[str] = Field(None, max_length=50, description="用药时长")
    notes: Optional[str] = Field(None, description="备注")
    sort_order: int = Field(0, ge=0, description="排序")


class MedicalOrderCreateRequest(BaseModel):
    """创建医嘱请求"""
    patient_id: int = Field(..., description="患者ID")
    order_type: str = Field(..., description="医嘱类型")
    title: str = Field(..., max_length=200, description="医嘱标题")
    description: Optional[str] = Field(None, description="详细说明")
    schedule_type: str = Field(..., description="调度类型")
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    frequency: Optional[str] = Field(None, max_length=50, description="频次")
    reminder_times: Optional[List[str]] = Field(default_factory=list, description="提醒时间")
    weekdays: Optional[List[int]] = Field(default_factory=list, description="每周调度：星期几 [0-6]，0=周日")
    ai_generated: bool = Field(False, description="是否AI生成")
    ai_session_id: Optional[str] = Field(None, description="关联的问诊会话ID")
    items: Optional[List[OrderItemCreate]] = Field(None, description="医嘱项目列表（药品、检查等）")


class MedicalOrderUpdateRequest(BaseModel):
    """更新医嘱请求"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    end_date: Optional[date] = None
    items: Optional[List[OrderItemCreate]] = Field(None, description="医嘱项目列表")
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
    weekdays: List[int] = []
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


# ============================================================================
# 药品相关 Schema
# ============================================================================

class DrugSearchResponse(BaseModel):
    """药品搜索响应"""
    id: int
    name: str
    generic_name: Optional[str] = None
    specification: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    stock_count: Optional[int] = None


# ============================================================================
# 医嘱模板 Schema
# ============================================================================

class OrderTemplate(BaseModel):
    """医嘱模板"""
    id: int
    name: str
    description: Optional[str] = None
    order_type: str
    template_data: Dict[str, Any]  # 包含 items 和其他字段


class OrderTemplateCreate(BaseModel):
    """创建医嘱模板"""
    name: str = Field(..., max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板说明")
    order_type: str = Field(..., description="医嘱类型")
    template_data: Dict[str, Any] = Field(..., description="模板数据")


class OrderTemplateResponse(BaseModel):
    """医嘱模板响应"""
    id: int
    name: str
    description: Optional[str]
    order_type: str
    template_data: Dict[str, Any]
    is_active: bool
    created_at: datetime


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
