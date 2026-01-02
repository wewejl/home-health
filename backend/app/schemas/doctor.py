from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class DoctorResponse(BaseModel):
    id: int
    name: str
    title: Optional[str] = None
    department_id: int
    hospital: Optional[str] = None
    specialty: Optional[str] = None
    intro: Optional[str] = None
    avatar_url: Optional[str] = None
    rating: float = 5.0
    monthly_answers: int = 0
    avg_response_time: str = "5分钟"
    can_prescribe: bool = False
    is_top_hospital: bool = False
    is_ai: bool = True
    is_active: bool = True

    class Config:
        from_attributes = True


class DoctorCreate(BaseModel):
    name: str
    title: Optional[str] = None
    department_id: int
    hospital: Optional[str] = None
    specialty: Optional[str] = None
    intro: Optional[str] = None
    avatar_url: Optional[str] = None
    rating: float = 5.0
    monthly_answers: int = 0
    avg_response_time: str = "5分钟"
    can_prescribe: bool = False
    is_top_hospital: bool = False
    is_ai: bool = True
    ai_persona_prompt: Optional[str] = None
    ai_model: str = "qwen-plus"
    ai_temperature: float = 0.7
    ai_max_tokens: int = 500
    knowledge_base_id: Optional[str] = None
    agent_type: str = "simple"
    agent_config: Optional[dict] = None
    is_active: bool = True


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    department_id: Optional[int] = None
    hospital: Optional[str] = None
    specialty: Optional[str] = None
    intro: Optional[str] = None
    avatar_url: Optional[str] = None
    rating: Optional[float] = None
    monthly_answers: Optional[int] = None
    avg_response_time: Optional[str] = None
    can_prescribe: Optional[bool] = None
    is_top_hospital: Optional[bool] = None
    is_ai: Optional[bool] = None
    ai_persona_prompt: Optional[str] = None
    ai_model: Optional[str] = None
    ai_temperature: Optional[float] = None
    ai_max_tokens: Optional[int] = None
    knowledge_base_id: Optional[str] = None
    agent_type: Optional[str] = None
    agent_config: Optional[dict] = None
    is_active: Optional[bool] = None


class DoctorDetailResponse(BaseModel):
    id: int
    name: str
    title: Optional[str] = None
    department_id: int
    hospital: Optional[str] = None
    specialty: Optional[str] = None
    intro: Optional[str] = None
    avatar_url: Optional[str] = None
    rating: float = 5.0
    monthly_answers: int = 0
    avg_response_time: str = "5分钟"
    can_prescribe: bool = False
    is_top_hospital: bool = False
    is_ai: bool = True
    ai_persona_prompt: Optional[str] = None
    ai_model: str = "qwen-plus"
    ai_temperature: float = 0.7
    ai_max_tokens: int = 500
    knowledge_base_id: Optional[str] = None
    agent_type: str = "simple"
    agent_config: Optional[Any] = None
    is_active: bool = True
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
