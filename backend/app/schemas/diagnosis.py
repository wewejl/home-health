from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime


class QuickOptionSchema(BaseModel):
    """快捷选项"""
    text: str
    value: str
    category: str


class DiseaseSchema(BaseModel):
    """疾病信息"""
    name: str
    probability: str
    description: str


class RecommendationsSchema(BaseModel):
    """诊断建议"""
    summary: Optional[str] = None
    risk_warning: Optional[str] = None
    department: Optional[str] = None
    urgency: Optional[str] = None
    lifestyle: Optional[List[str]] = []


class DiagnosisMessageSchema(BaseModel):
    """问诊消息"""
    role: str
    content: str
    timestamp: Optional[str] = None
    quick_options: Optional[List[QuickOptionSchema]] = None
    is_diagnosis: Optional[bool] = False


# 请求Schema
class StartDiagnosisRequest(BaseModel):
    """开始问诊请求"""
    chief_complaint: Optional[str] = ""


class HistoryMessageSchema(BaseModel):
    """前端传入的历史消息"""
    role: Literal["user", "assistant"]
    message: str
    timestamp: Optional[str] = None


class CurrentInputSchema(BaseModel):
    """当前输入内容"""
    message: str


class ContinueDiagnosisRequest(BaseModel):
    """统一请求体（history + current_input）"""
    history: List[HistoryMessageSchema]
    current_input: CurrentInputSchema
    force_conclude: bool = False


# 响应Schema
class DiagnosisQuestionResponse(BaseModel):
    """问诊问题响应"""
    type: Literal["question"] = "question"
    consultation_id: str
    message: str
    quick_options: List[QuickOptionSchema]
    progress: int
    stage: str
    can_conclude: bool
    reasoning: Optional[str] = None


class DiagnosisResultResponse(BaseModel):
    """诊断结果响应"""
    type: Literal["diagnosis"] = "diagnosis"
    consultation_id: str
    message: str
    summary: str
    diseases: List[DiseaseSchema]
    risk_level: str
    risk_warning: Optional[str] = None
    recommendations: RecommendationsSchema
    progress: int = 100


class DiagnosisResponse(BaseModel):
    """统一问诊响应"""
    type: Literal["question", "diagnosis"]
    consultation_id: str
    message: str
    quick_options: Optional[List[QuickOptionSchema]] = None
    progress: int
    stage: str
    can_conclude: Optional[bool] = None
    reasoning: Optional[str] = None
    # 诊断结果字段
    summary: Optional[str] = None
    diseases: Optional[List[DiseaseSchema]] = None
    risk_level: Optional[str] = None
    risk_warning: Optional[str] = None
    recommendations: Optional[RecommendationsSchema] = None


class DiagnosisSessionSchema(BaseModel):
    """问诊会话信息"""
    consultation_id: str
    stage: str
    progress: int
    chief_complaint: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DiagnosisSessionListResponse(BaseModel):
    """问诊会话列表响应"""
    sessions: List[DiagnosisSessionSchema]
    total: int
