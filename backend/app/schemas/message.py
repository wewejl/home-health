from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MessageCreate(BaseModel):
    """发送消息请求（兼容旧版）"""
    content: str


class AttachmentSchema(BaseModel):
    """附件 Schema"""
    type: str = Field(..., description="附件类型: image, pdf, ...")
    url: Optional[str] = Field(None, description="附件 URL")
    base64: Optional[str] = Field(None, description="Base64 编码")
    metadata: Optional[Dict[str, Any]] = Field(None, description="附件元数据")


class EnhancedMessageCreate(BaseModel):
    """发送消息请求（增强版）"""
    content: str
    attachments: Optional[List[AttachmentSchema]] = Field(None, description="附件列表")
    action: Optional[str] = Field("conversation", description="动作类型: conversation, analyze_skin, interpret_report, ...")


class MessageResponse(BaseModel):
    id: int
    session_id: str
    sender: str
    content: str
    attachment_url: Optional[str] = None
    message_type: str = "text"
    attachments: Optional[List[Dict[str, Any]]] = None
    structured_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    ai_message: MessageResponse


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    has_more: bool = False


class StreamCompleteResponse(BaseModel):
    """流式响应完成事件数据"""
    message: str
    structured_data: Optional[Dict[str, Any]] = None
    quick_options: Optional[List[Dict[str, str]]] = None
