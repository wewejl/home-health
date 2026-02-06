"""
病历记录 schemas - API 请求和响应数据结构
"""
from pydantic import BaseModel, Field, field_serializer, field_validator
from datetime import datetime, date
from typing import Optional, List, Union
from .medical_file import MedicalFileResponse


class MedicalRecordBase(BaseModel):
    """病历记录基础模型"""
    folder_id: str = Field(..., description="所属文件夹ID")
    title: str = Field(..., min_length=1, max_length=255, description="标题")
    record_date: date = Field(..., description="记录日期")
    description: Optional[str] = Field(None, description="描述")

    # 验证器：支持 ISO8601 格式的日期字符串输入
    @field_validator('record_date', mode='before')
    @classmethod
    def parse_record_date(cls, v: Union[str, date]) -> date:
        """解析日期，支持 ISO8601 格式字符串或 date 对象"""
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                # 尝试解析 ISO8601 格式
                return datetime.fromisoformat(v.replace('Z', '+00:00')).date()
            except ValueError:
                # 尝试解析简单的 YYYY-MM-DD 格式
                try:
                    return datetime.strptime(v, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError(f"Invalid date format: {v}")
        raise ValueError(f"Invalid date type: {type(v)}")

    # 将日期序列化为 ISO8601 格式 (兼容 iOS Swift Date 解码)
    @field_serializer('record_date')
    def serialize_record_date(self, dt: date, _info) -> str:
        """将 date 序列化为 ISO8601 格式字符串（带 UTC 时区后缀）"""
        # 转换为 datetime 并格式化为 ISO8601，带 Z 后缀
        if isinstance(dt, date):
            # 将日期转换为当天中午 12:00:00 的 datetime
            dt_datetime = datetime.combine(dt, datetime.min.time()).replace(hour=12, minute=0, second=0, microsecond=0)
            return dt_datetime.isoformat() + 'Z'
        return (dt.isoformat() + 'Z') if dt else ""


class MedicalRecordCreate(MedicalRecordBase):
    """创建病历记录请求"""
    pass


class MedicalRecordUpdate(BaseModel):
    """更新病历记录请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    record_date: Optional[Union[str, date]] = None
    description: Optional[str] = None
    folder_id: Optional[str] = None

    # 验证器：支持 ISO8601 格式的日期字符串输入
    @field_validator('record_date', mode='before')
    @classmethod
    def parse_record_date_optional(cls, v: Optional[Union[str, date]]) -> Optional[date]:
        """解析可选日期，支持 ISO8601 格式字符串或 date 对象"""
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00')).date()
            except ValueError:
                try:
                    return datetime.strptime(v, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError(f"Invalid date format: {v}")
        raise ValueError(f"Invalid date type: {type(v)}")


class MedicalRecordResponse(MedicalRecordBase):
    """病历记录响应"""
    id: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    file_count: int = 0

    class Config:
        from_attributes = True


class MedicalRecordDetailResponse(MedicalRecordResponse):
    """病历记录详情响应（包含文件）"""
    files: List[MedicalFileResponse] = []


class MedicalRecordListResponse(BaseModel):
    """病历记录列表响应"""
    records: List[MedicalRecordResponse]
    total: int
