from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    session_id: str
    sender: str
    content: str
    attachment_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    ai_message: MessageResponse


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    has_more: bool = False
