from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FeedbackCreate(BaseModel):
    message_id: Optional[int] = None
    rating: Optional[int] = None
    feedback_type: Optional[str] = None
    feedback_text: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    session_id: str
    message_id: Optional[int] = None
    user_id: int
    rating: Optional[int] = None
    feedback_type: Optional[str] = None
    feedback_text: Optional[str] = None
    status: str = "pending"
    handled_by: Optional[int] = None
    handled_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FeedbackHandleRequest(BaseModel):
    status: str  # reviewed/resolved
    resolution_notes: Optional[str] = None
