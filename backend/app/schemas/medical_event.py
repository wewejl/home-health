"""
病历事件 API Schema
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ============= 枚举类型 =============
EventStatusType = Literal["active", "completed", "archived", "exported"]
RiskLevelType = Literal["low", "medium", "high", "emergency"]
AgentTypeValue = Literal["cardio", "derma", "ortho", "neuro", "general", "endo", "gastro", "respiratory"]
AttachmentTypeValue = Literal["image", "report", "voice"]
ExportTypeValue = Literal["pdf", "share_link", "json"]


# ============= AI分析相关 =============
class TimelineEventSchema(BaseModel):
    """时间轴事件"""
    time: str
    event: str
    type: Optional[str] = None


class AIAnalysisSchema(BaseModel):
    """AI分析结果"""
    symptoms: List[str] = []
    possible_diagnosis: List[str] = []
    recommendations: List[str] = []
    follow_up_reminders: List[str] = []
    timeline: List[TimelineEventSchema] = []


class SessionRecordSchema(BaseModel):
    """会话记录摘要"""
    session_id: str
    session_type: str
    timestamp: str
    summary: Optional[str] = None


# ============= 附件相关 =============
class AttachmentMetadataSchema(BaseModel):
    """附件元数据"""
    width: Optional[int] = None
    height: Optional[int] = None
    report_type: Optional[str] = None
    ocr_text: Optional[str] = None
    voice_duration: Optional[int] = None


class AttachmentSchema(BaseModel):
    """附件信息"""
    id: str
    type: AttachmentTypeValue
    url: str
    thumbnail_url: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    metadata: Optional[AttachmentMetadataSchema] = None
    description: Optional[str] = None
    is_important: bool = False
    upload_time: datetime

    class Config:
        from_attributes = True


class AttachmentCreateRequest(BaseModel):
    """创建附件请求"""
    type: AttachmentTypeValue
    url: str
    thumbnail_url: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    metadata: Optional[dict] = None
    description: Optional[str] = None


# ============= 备注相关 =============
class NoteSchema(BaseModel):
    """用户备注"""
    id: str
    content: str
    is_important: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NoteCreateRequest(BaseModel):
    """创建备注请求"""
    content: str = Field(..., min_length=1, max_length=2000)
    is_important: bool = False


class NoteUpdateRequest(BaseModel):
    """更新备注请求"""
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    is_important: Optional[bool] = None


# ============= 病历事件相关 =============
class MedicalEventCreateRequest(BaseModel):
    """创建病历事件请求"""
    title: str = Field(..., min_length=1, max_length=200)
    department: str = Field(..., min_length=1, max_length=50)
    agent_type: AgentTypeValue
    chief_complaint: Optional[str] = None
    risk_level: RiskLevelType = "low"


class MedicalEventUpdateRequest(BaseModel):
    """更新病历事件请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[EventStatusType] = None
    risk_level: Optional[RiskLevelType] = None
    chief_complaint: Optional[str] = None
    summary: Optional[str] = None


class MedicalEventSummarySchema(BaseModel):
    """病历事件摘要（列表用）"""
    id: str
    title: str
    department: str
    agent_type: str
    status: str
    risk_level: str
    start_time: datetime
    end_time: Optional[datetime] = None
    summary: Optional[str] = None
    chief_complaint: Optional[str] = None
    attachment_count: int = 0
    session_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MedicalEventDetailSchema(BaseModel):
    """病历事件详情"""
    id: str
    title: str
    department: str
    agent_type: str
    status: str
    risk_level: str
    start_time: datetime
    end_time: Optional[datetime] = None
    summary: Optional[str] = None
    chief_complaint: Optional[str] = None
    ai_analysis: Optional[AIAnalysisSchema] = None
    sessions: List[SessionRecordSchema] = []
    attachments: List[AttachmentSchema] = []
    notes: List[NoteSchema] = []
    attachment_count: int = 0
    session_count: int = 0
    export_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MedicalEventListResponse(BaseModel):
    """病历事件列表响应"""
    events: List[MedicalEventSummarySchema]
    total: int
    page: int
    page_size: int


# ============= 导出相关 =============
class ExportOptionsSchema(BaseModel):
    """导出选项"""
    include_full_conversation: bool = False
    include_user_notes: bool = True
    include_ai_analysis: bool = True
    include_attachments: bool = True
    include_personal_info: bool = True
    template: str = "standard"


class ExportCreateRequest(BaseModel):
    """创建导出请求"""
    event_ids: List[str] = Field(..., min_items=1)
    export_type: ExportTypeValue = "pdf"
    options: Optional[ExportOptionsSchema] = None
    share_password: Optional[str] = Field(None, min_length=4, max_length=20)
    expires_in_days: Optional[int] = Field(7, ge=1, le=30)
    max_views: Optional[int] = Field(None, ge=1, le=100)


class ExportRecordSchema(BaseModel):
    """导出记录"""
    id: str
    export_type: str
    file_url: Optional[str] = None
    share_token: Optional[str] = None
    has_password: bool = False
    expires_at: Optional[datetime] = None
    view_count: int = 0
    max_views: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    event_ids: List[str] = []

    class Config:
        from_attributes = True


class ExportResponse(BaseModel):
    """导出响应"""
    export_id: str
    export_type: str
    file_url: Optional[str] = None
    share_url: Optional[str] = None
    share_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: str


class ShareLinkAccessRequest(BaseModel):
    """访问共享链接请求"""
    token: str
    password: Optional[str] = None


class ShareLinkResponse(BaseModel):
    """共享链接内容响应"""
    events: List[MedicalEventDetailSchema]
    export_info: ExportRecordSchema
    accessed_at: datetime


# ============= 聚合相关 =============
class AggregateSessionRequest(BaseModel):
    """聚合会话请求"""
    session_id: str
    session_type: Literal["derma", "diagnosis"]


class AggregateResponse(BaseModel):
    """聚合响应"""
    event_id: str
    message: str
    is_new_event: bool = False


class GenerateSummaryRequest(BaseModel):
    """生成摘要请求"""
    event_id: str
    force_regenerate: bool = False


class GenerateSummaryResponse(BaseModel):
    """生成摘要响应"""
    event_id: str
    summary: str
    ai_analysis: AIAnalysisSchema
    message: str


# ============= 搜索筛选 =============
class EventSearchParams(BaseModel):
    """事件搜索参数"""
    keyword: Optional[str] = None
    department: Optional[str] = None
    agent_type: Optional[AgentTypeValue] = None
    status: Optional[EventStatusType] = None
    risk_level: Optional[RiskLevelType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    has_exports: Optional[bool] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: Literal["created_at", "updated_at", "start_time"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"
