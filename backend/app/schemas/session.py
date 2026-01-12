from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


class SessionCreate(BaseModel):
    """创建会话请求（兼容旧版）"""
    doctor_id: Optional[int] = None


class EnhancedSessionCreate(BaseModel):
    """创建会话请求（增强版）"""
    doctor_id: Optional[int] = None
    agent_type: Optional[str] = Field(None, description="智能体类型: general, dermatology, cardiology, ...")


class SessionResponse(BaseModel):
    session_id: str
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    agent_type: str = "general"
    last_message: Optional[str] = None
    status: str = "active"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def ensure_timezone(cls, value):
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]


class AgentCapabilitiesResponse(BaseModel):
    """智能体能力响应"""
    actions: List[str]
    accepts_media: List[str]
    ui_components: List[str]
    description: str
