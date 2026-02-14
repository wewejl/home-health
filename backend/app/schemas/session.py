from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal, Union
from datetime import datetime, timezone
import re


# 有效的智能体类型
VALID_AGENT_TYPES = Literal["general", "dermatology", "cardiology", "orthopedics"]


class SessionCreate(BaseModel):
    """创建会话请求（兼容旧版）"""
    doctor_id: Optional[int] = Field(None, ge=1, description="医生ID")


class EnhancedSessionCreate(BaseModel):
    """创建会话请求（增强版）"""
    doctor_id: Optional[int] = Field(None, ge=1, description="医生ID")
    agent_type: VALID_AGENT_TYPES = Field("general", description="智能体类型")

    @field_validator("doctor_id")
    @classmethod
    def validate_doctor_id(cls, v):
        if v is not None and v < 1:
            raise ValueError("doctor_id 必须是正整数")
        return v


class SessionResponse(BaseModel):
    session_id: str
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    agent_type: str = "general"
    last_message: Optional[str] = None
    status: str = "active"
    created_at: datetime
    updated_at: datetime
    # 虚拟医生分身扩展字段
    personality_type: Optional[str] = None
    greeting: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def ensure_timezone(cls, value):
        # Handle string input
        if isinstance(value, str):
            # Parse datetime string, handling microseconds
            # PostgreSQL format: 2026-01-29 15:28:49.992313+00
            try:
                # Try to parse with microseconds
                if '.' in value:
                    # Split the microseconds part
                    main_part, micros_part = value.split('.')
                    micros = micros_part.split('+')[0]  # Get microseconds before timezone
                    tz_part = micros_part.split('+')[1] if '+' in micros_part else None
                    value = f"{main_part}.{micros}"
                    if tz_part:
                        value += f"+{tz_part}"
                value = datetime.fromisoformat(value)
            except:
                # Fallback to standard parsing
                value = datetime.fromisoformat(value.replace('+00', '+00:00'))

        # Ensure timezone
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
