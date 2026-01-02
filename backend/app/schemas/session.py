from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SessionCreate(BaseModel):
    doctor_id: Optional[int] = None


class SessionResponse(BaseModel):
    session_id: str
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    last_message: Optional[str] = None
    status: str = "active"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
