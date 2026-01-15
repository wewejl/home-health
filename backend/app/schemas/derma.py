"""
皮肤科智能体API Schema
"""
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime


class DermaQuickOptionSchema(BaseModel):
    """快捷选项"""
    text: str
    value: str
    category: str


class SkinConditionSchema(BaseModel):
    """皮肤病情况"""
    name: str
    confidence: float
    description: str


class SkinAnalysisResultSchema(BaseModel):
    """皮肤分析结果"""
    lesion_description: str
    possible_conditions: List[SkinConditionSchema]
    risk_level: Literal["low", "medium", "high", "emergency"]
    care_advice: str
    need_offline_visit: bool
    visit_urgency: Optional[str] = None
    additional_questions: Optional[List[str]] = []


class ReportIndicatorSchema(BaseModel):
    """报告指标"""
    name: str
    value: str
    reference_range: Optional[str] = None
    status: Literal["normal", "high", "low", "abnormal"]
    explanation: Optional[str] = None


class ReportInterpretationSchema(BaseModel):
    """报告解读结果"""
    report_type: str
    report_date: Optional[str] = None
    indicators: List[ReportIndicatorSchema]
    summary: str
    abnormal_findings: List[str]
    health_advice: List[str]
    need_follow_up: bool
    follow_up_suggestion: Optional[str] = None


# 请求Schema
class StartDermaSessionRequest(BaseModel):
    """开始皮肤科问诊请求"""
    chief_complaint: Optional[str] = ""


class DermaMessageSchema(BaseModel):
    """皮肤科消息"""
    role: Literal["user", "assistant"]
    message: str
    timestamp: Optional[str] = None


class DermaCurrentInputSchema(BaseModel):
    """当前输入"""
    message: Optional[str] = None


class ContinueDermaRequest(BaseModel):
    """
    继续皮肤科问诊请求（统一接口）
    
    支持三种任务类型：
    - conversation: 纯文本问诊对话
    - skin_analysis: 皮肤影像分析（需提供 image_url 或 image_base64）
    - report_interpret: 报告解读（需提供 image_url 或 image_base64，可选 report_type）
    """
    history: List[DermaMessageSchema]
    current_input: DermaCurrentInputSchema
    task_type: Optional[Literal["conversation", "skin_analysis", "report_interpret"]] = "conversation"
    
    # 图像相关字段（用于 skin_analysis 和 report_interpret）
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    
    # 报告解读专用字段
    report_type: Optional[str] = "皮肤科检查报告"


class SkinAnalysisRequest(BaseModel):
    """皮肤影像分析请求"""
    session_id: str
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    additional_info: Optional[str] = ""


class ReportInterpretRequest(BaseModel):
    """报告解读请求"""
    session_id: str
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    report_type: Optional[str] = "皮肤科检查报告"


# 响应Schema
class DermaResponse(BaseModel):
    """皮肤科问诊响应"""
    type: Literal["conversation", "skin_analysis", "report_interpret"]
    session_id: str
    message: str
    quick_options: Optional[List[DermaQuickOptionSchema]] = None
    progress: int
    stage: str
    awaiting_image: bool = False
    
    # 皮肤分析结果
    skin_analysis: Optional[SkinAnalysisResultSchema] = None
    
    # 报告解读结果
    report_interpretation: Optional[ReportInterpretationSchema] = None
    
    # 诊断建议
    risk_level: Optional[str] = None
    need_offline_visit: Optional[bool] = None
    care_advice: Optional[str] = None
    
    # 病历事件关联（对话结束时自动生成）
    event_id: Optional[int] = None
    is_new_event: Optional[bool] = None
    should_show_dossier_prompt: Optional[bool] = None


class DermaSessionSchema(BaseModel):
    """皮肤科会话信息"""
    session_id: str
    stage: str
    progress: int
    chief_complaint: Optional[str] = None
    has_skin_analysis: bool = False
    has_report_interpretation: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DermaSessionListResponse(BaseModel):
    """皮肤科会话列表响应"""
    sessions: List[DermaSessionSchema]
    total: int


class ImageUploadResponse(BaseModel):
    """图片上传响应"""
    success: bool
    image_url: Optional[str] = None
    error: Optional[str] = None
