"""
皮肤科智能体输出模型 - Pydantic 结构化输出

使用 with_structured_output() 保证 LLM 输出格式
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class ConversationOutput(BaseModel):
    """对话节点输出模型"""
    message: str = Field(description="回复消息")
    next_action: Literal["continue", "complete"] = Field(
        default="continue",
        description="下一步动作：continue 继续问诊，complete 给出诊断"
    )
    extracted_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="从用户输入中提取的医学信息"
    )
    quick_options: List[Dict[str, str]] = Field(
        default_factory=list,
        description="快捷回复选项"
    )


class ImageAnalysisOutput(BaseModel):
    """图片分析输出模型"""
    message: str = Field(description="分析描述")
    skin_features: Dict[str, str] = Field(
        default_factory=dict,
        description="皮损特征：形态、颜色、分布等"
    )
    extracted_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="提取的信息：部位、症状等"
    )
    confidence: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="分析置信度"
    )


class ConditionInfo(BaseModel):
    """诊断条目"""
    name: str = Field(description="疾病名称")
    probability: Literal["likely", "possible", "unlikely"] = Field(description="可能性")
    basis: str = Field(description="诊断依据")


class DiagnosisOutput(BaseModel):
    """诊断节点输出模型"""
    diagnosis_message: str = Field(description="诊断说明")
    conditions: List[ConditionInfo] = Field(
        default_factory=list,
        description="鉴别诊断列表"
    )
    risk_level: Literal["low", "medium", "high", "emergency"] = Field(
        default="low",
        description="风险等级"
    )
    care_advice: str = Field(description="护理建议")
    treatment_suggestions: List[str] = Field(
        default_factory=list,
        description="治疗建议"
    )
    need_offline_visit: bool = Field(
        default=False,
        description="是否需要线下就医"
    )
    follow_up_days: Optional[int] = Field(
        default=None,
        description="建议复诊天数"
    )
