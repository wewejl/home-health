"""
FastAPI 请求和响应模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# =====================================================
# 请求模型
# =====================================================

class ChatRequest(BaseModel):
    """对话请求"""
    session_id: str = Field(..., description="会话 ID（唯一标识）", examples=["session_001"])
    his_user_id: str = Field(..., description="HIS 系统的医生 ID", examples=["doctor_123"])
    message: str = Field(..., description="用户消息内容", examples=["你好，我正在看一位叫李明的患者"])
    his_patient_id: Optional[str] = Field(None, description="HIS 系统的患者 ID（可选）", examples=["patient_001"])


class DeleteSessionRequest(BaseModel):
    """删除会话请求"""
    session_id: str = Field(..., description="要删除的会话 ID", examples=["session_001"])


class iOSMessageRequest(BaseModel):
    """iOS 消息请求 - 兼容 iOS 问诊模块"""
    content: str = Field(..., description="消息内容", examples=["你好，我头痛头晕三天了"])
    action: Optional[str] = Field("conversation", description="动作类型", examples=["conversation"])
    his_user_id: Optional[str] = Field(None, description="HIS 医生 ID（可选）")
    attachments: Optional[List[dict]] = Field(default_factory=list, description="附件列表（可选）")


# =====================================================
# 响应模型
# =====================================================

class ChatMessage(BaseModel):
    """对话消息"""
    id: int
    session_id: str
    his_user_id: str
    role: str  # user | assistant | system
    content: str
    metadata: Optional[dict] = None
    created_at: str


class SessionHistoryResponse(BaseModel):
    """会话历史响应"""
    session_id: str
    messages: List[ChatMessage]
    total_count: int


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    his_user_id: str
    his_patient_id: Optional[str] = None
    message_count: int
    created_at: str
    updated_at: str


class SessionListResponse(BaseModel):
    """会话列表响应"""
    his_user_id: str
    sessions: List[SessionInfo]
    total_count: int


class DeleteSessionResponse(BaseModel):
    """删除会话响应"""
    success: bool
    session_id: str
    message: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str
    database: str


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误详情")
    detail: Optional[str] = Field(None, description="详细错误信息")
