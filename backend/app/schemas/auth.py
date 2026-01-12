from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date
import re


class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(..., description="手机号")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        pattern = r'^1[3-9]\d{9}$'
        if not re.match(pattern, v):
            raise ValueError('请输入正确的11位手机号')
        return v


class SendCodeResponse(BaseModel):
    """发送验证码响应"""
    message: str
    expires_in: int = Field(default=300, description="验证码有效期(秒)")


class LoginRequest(BaseModel):
    """登录请求"""
    phone: str
    code: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        pattern = r'^1[3-9]\d{9}$'
        if not re.match(pattern, v):
            raise ValueError('请输入正确的11位手机号')
        return v
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if v in (None, ""):
            return None
        if len(v) < 4:
            raise ValueError('请输入验证码')
        return v


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    phone: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    is_profile_completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    refresh_token: Optional[str] = None
    user: UserResponse
    is_new_user: bool = False


class ProfileUpdateRequest(BaseModel):
    """更新用户资料请求"""
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    gender: Optional[str] = Field(None, description="性别: male/female/other")
    birthday: Optional[date] = Field(None, description="生日")
    emergency_contact_name: Optional[str] = Field(None, max_length=50, description="紧急联系人姓名")
    emergency_contact_phone: Optional[str] = Field(None, max_length=20, description="紧急联系人电话")
    emergency_contact_relation: Optional[str] = Field(None, max_length=20, description="与紧急联系人关系")
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        if v and v not in ['male', 'female', 'other']:
            raise ValueError('性别只能是 male/female/other')
        return v
    
    @field_validator('emergency_contact_phone')
    @classmethod
    def validate_emergency_phone(cls, v):
        if v:
            pattern = r'^1[3-9]\d{9}$'
            if not re.match(pattern, v):
                raise ValueError('请输入正确的紧急联系人手机号')
        return v


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """刷新Token响应"""
    token: str
    refresh_token: str


# ===== 密码认证相关 Schema =====

class PasswordRegisterRequest(BaseModel):
    """密码注册请求"""
    phone: str = Field(..., description="手机号")
    code: Optional[str] = Field(None, description="验证码")
    password: str = Field(..., min_length=6, max_length=32, description="密码")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        pattern = r'^1[3-9]\d{9}$'
        if not re.match(pattern, v):
            raise ValueError('请输入正确的11位手机号')
        return v
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if v is None or v == "":
            return None
        if len(v) < 4:
            raise ValueError('验证码长度至少4位')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('密码长度至少6位')
        if len(v) > 32:
            raise ValueError('密码长度不能超过32位')
        if ' ' in v:
            raise ValueError('密码不能包含空格')
        return v


class PasswordLoginRequest(BaseModel):
    """密码登录请求"""
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        pattern = r'^1[3-9]\d{9}$'
        if not re.match(pattern, v):
            raise ValueError('请输入正确的11位手机号')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v:
            raise ValueError('请输入密码')
        return v


class SetPasswordRequest(BaseModel):
    """设置/更新密码请求（已登录用户）"""
    code: str = Field(..., description="验证码")
    new_password: str = Field(..., min_length=6, max_length=32, description="新密码")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if not v or len(v) < 4:
            raise ValueError('请输入验证码')
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('密码长度至少6位')
        if len(v) > 32:
            raise ValueError('密码长度不能超过32位')
        if ' ' in v:
            raise ValueError('密码不能包含空格')
        return v


class PasswordResetRequest(BaseModel):
    """密码重置请求"""
    phone: str = Field(..., description="手机号")
    code: str = Field(..., description="验证码")
    new_password: str = Field(..., min_length=6, max_length=32, description="新密码")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        pattern = r'^1[3-9]\d{9}$'
        if not re.match(pattern, v):
            raise ValueError('请输入正确的11位手机号')
        return v
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if not v or len(v) < 4:
            raise ValueError('请输入验证码')
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('密码长度至少6位')
        if len(v) > 32:
            raise ValueError('密码长度不能超过32位')
        if ' ' in v:
            raise ValueError('密码不能包含空格')
        return v


class CheckPhoneResponse(BaseModel):
    """检查手机号响应"""
    exists: bool = Field(..., description="用户是否存在")
    has_password: bool = Field(..., description="是否设置了密码")
