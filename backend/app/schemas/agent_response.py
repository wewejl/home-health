"""
统一智能体响应格式

所有智能体返回此统一格式，专科数据通过 specialty_data 扩展字段承载
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List


class AgentResponse(BaseModel):
    """统一智能体响应格式"""
    
    # ========== 基础字段（必填） ==========
    message: str = Field(..., description="AI 回复内容")
    stage: str = Field(..., description="当前阶段")
    progress: int = Field(..., ge=0, le=100, description="进度百分比")
    
    # ========== 可选字段 ==========
    quick_options: List[str] = Field(default=[], description="快捷回复选项")
    risk_level: Optional[str] = Field(None, description="风险等级")
    
    # 病历事件相关
    event_id: Optional[str] = Field(None, description="病历事件ID")
    is_new_event: bool = Field(False, description="是否创建新事件")
    should_show_dossier_prompt: bool = Field(False, description="是否提示生成病历")
    
    # ========== 专科扩展数据 ==========
    specialty_data: Optional[Dict[str, Any]] = Field(
        None,
        description="专科特有数据"
    )
    
    # ========== 状态持久化 ==========
    next_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="下次调用需要的状态"
    )
    
    @field_validator('stage')
    @classmethod
    def validate_stage(cls, v):
        valid_stages = ['greeting', 'collecting', 'analyzing', 'diagnosing', 'completed']
        if v not in valid_stages:
            raise ValueError(f'stage must be one of {valid_stages}')
        return v
    
    @field_validator('risk_level')
    @classmethod
    def validate_risk_level(cls, v):
        if v is not None:
            valid_levels = ['low', 'medium', 'high', 'emergency']
            if v not in valid_levels:
                raise ValueError(f'risk_level must be one of {valid_levels}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "根据您的描述，可能是湿疹",
                "stage": "diagnosing",
                "progress": 80,
                "quick_options": ["继续描述", "上传照片"],
                "risk_level": "low",
                "specialty_data": {
                    "diagnosis_card": {
                        "summary": "手臂湿疹",
                        "conditions": [{"name": "湿疹", "confidence": 0.85}]
                    }
                }
            }
        }
