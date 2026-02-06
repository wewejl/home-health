"""
医疗文件 schemas - API 请求和响应数据结构
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MedicalFileResponse(BaseModel):
    """文件响应"""
    id: str
    record_id: str
    user_id: int
    filename: str
    file_type: str  # image, pdf, video, audio, document
    mime_type: str
    file_size: int
    url: str
    thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MedicalFileUpdate(BaseModel):
    """更新文件请求（重命名）"""
    filename: str = Field(..., min_length=1, max_length=500)


class MedicalFileListResponse(BaseModel):
    """文件列表响应"""
    files: list[MedicalFileResponse]
    total: int


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    file: MedicalFileResponse
    message: str = "文件上传成功"
