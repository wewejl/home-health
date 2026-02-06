"""
病历夹 schemas - API 请求和响应数据结构
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MedicalFolderBase(BaseModel):
    """病历夹基础模型"""
    name: str = Field(..., min_length=1, max_length=255, description="文件夹名称")
    description: Optional[str] = Field(None, description="描述")
    color: str = Field("#7B5FEA", description="颜色，如 #7B5FEA")
    icon: str = Field("folder", description="图标名称")
    sort_order: int = Field(0, description="排序序号")


class MedicalFolderCreate(MedicalFolderBase):
    """创建病历夹请求"""
    pass


class MedicalFolderUpdate(BaseModel):
    """更新病历夹请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None


class MedicalFolderResponse(MedicalFolderBase):
    """病历夹响应"""
    id: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    record_count: int = 0

    class Config:
        from_attributes = True


class MedicalFolderListResponse(BaseModel):
    """病历夹列表响应"""
    folders: list[MedicalFolderResponse]
    total: int
