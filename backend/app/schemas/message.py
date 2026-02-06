from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union
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
    created_at: Union[datetime, str]

    @field_validator('attachments', mode='before')
    @classmethod
    def parse_attachments(cls, v):
        """处理 PostgreSQL JSON 类型返回的字符串 'null'"""
        if v == 'null' or v == '' or v is None:
            return None
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return None
        return v

    @field_validator('structured_data', mode='before')
    @classmethod
    def parse_structured_data(cls, v):
        """处理 PostgreSQL JSON 类型返回的字符串 'null'"""
        if v == 'null' or v == '' or v is None:
            return None
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return None
        return v

    @field_validator('created_at', mode='before')
    @classmethod
    def parse_created_at(cls, v):
        """处理 PostgreSQL 返回的 datetime 字符串"""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # PostgreSQL 返回的 datetime 格式: "2026-01-30 15:18:35.52283+00"
            # 需要转换为 ISO 8601 格式
            try:
                # 尝试解析各种可能的格式
                if '+' in v:
                    # 格式: "2026-01-30 15:18:35.52283+00"
                    # 替换空格为 T，添加冒号到时区
                    parts = v.rsplit('+', 1)
                    if len(parts) == 2:
                        base = parts[0].replace(' ', 'T')
                        tz = parts[1]
                        # 补全时区格式 (00 -> +00:00)
                        if len(tz) == 2:
                            tz = f"+{tz}:00"
                        elif len(tz) == 4 and ':' not in tz:
                            tz = f"{tz[:3]}:{tz[3:]}"
                        v = f"{base}+{tz}"
                return datetime.fromisoformat(v)
            except Exception as e:
                # 如果解析失败，返回当前时间
                return datetime.utcnow()
        return v

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
