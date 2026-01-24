from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


# ==================== MedLive 数据模型 ====================

class DiseaseSectionItem(BaseModel):
    """疾病内容子项"""
    id: str
    title: Optional[str] = None
    content: str
    level: int


class DiseaseSection(BaseModel):
    """疾病内容区块"""
    id: str
    title: str
    icon: str
    content: Optional[str] = None
    items: Optional[List[DiseaseSectionItem]] = None


class MedLiveDiseaseResponse(BaseModel):
    """MedLive 格式疾病详情响应"""
    id: int
    name: str
    department: Optional[str] = None
    source: str
    url: Optional[str] = None
    sections: List[DiseaseSection]


# ==================== DXY 数据模型（兼容保留）====================

class DiseaseBase(BaseModel):
    name: str
    pinyin: Optional[str] = None
    pinyin_abbr: Optional[str] = None
    department_id: Optional[int] = None
    recommended_department: Optional[str] = None
    overview: Optional[str] = None
    symptoms: Optional[str] = None
    causes: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    prevention: Optional[str] = None
    care: Optional[str] = None
    author_name: Optional[str] = None
    author_title: Optional[str] = None
    author_avatar: Optional[str] = None
    reviewer_info: Optional[str] = None
    is_hot: bool = False
    sort_order: int = 0
    is_active: bool = True


class DiseaseCreate(DiseaseBase):
    pass


class DiseaseUpdate(BaseModel):
    name: Optional[str] = None
    pinyin: Optional[str] = None
    pinyin_abbr: Optional[str] = None
    department_id: Optional[int] = None
    recommended_department: Optional[str] = None
    overview: Optional[str] = None
    symptoms: Optional[str] = None
    causes: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    prevention: Optional[str] = None
    care: Optional[str] = None
    author_name: Optional[str] = None
    author_title: Optional[str] = None
    author_avatar: Optional[str] = None
    reviewer_info: Optional[str] = None
    is_hot: Optional[bool] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class DiseaseListResponse(BaseModel):
    """疾病列表响应（简要信息）"""
    id: int
    name: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    recommended_department: Optional[str] = None
    is_hot: bool
    view_count: int

    class Config:
        from_attributes = True


class DiseaseDetailResponse(BaseModel):
    """疾病详情响应（完整信息，兼容 DXY 格式）"""
    id: int
    name: str
    pinyin: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    recommended_department: Optional[str] = None
    overview: Optional[str] = None
    symptoms: Optional[str] = None
    causes: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    prevention: Optional[str] = None
    care: Optional[str] = None
    author_name: Optional[str] = None
    author_title: Optional[str] = None
    author_avatar: Optional[str] = None
    reviewer_info: Optional[str] = None
    is_hot: bool
    view_count: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DiseaseAdminResponse(BaseModel):
    """管理后台疾病响应"""
    id: int
    name: str
    pinyin: Optional[str] = None
    pinyin_abbr: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    recommended_department: Optional[str] = None
    overview: Optional[str] = None
    symptoms: Optional[str] = None
    causes: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    prevention: Optional[str] = None
    care: Optional[str] = None
    author_name: Optional[str] = None
    author_title: Optional[str] = None
    author_avatar: Optional[str] = None
    reviewer_info: Optional[str] = None
    is_hot: bool
    sort_order: int
    is_active: bool
    view_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DiseaseSearchResponse(BaseModel):
    """搜索结果响应"""
    total: int
    items: list[DiseaseListResponse]
