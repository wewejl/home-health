"""
皮肤科 ReAct Agent 工具定义

LLM 可调用的医疗工具集
"""
from typing import List, Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..llm_provider import LLMProvider


class SkinAnalysisResult(BaseModel):
    """图片分析结果"""
    description: str = Field(description="皮损描述")
    morphology: str = Field(description="形态特征")
    color: str = Field(description="颜色特征")
    distribution: str = Field(description="分布特征")
    suggested_conditions: List[str] = Field(default_factory=list)


class DiagnosisResult(BaseModel):
    """诊断结果"""
    conditions: List[dict] = Field(default_factory=list)
    risk_level: str = Field(default="low")
    care_advice: str = Field(default="")
    need_offline_visit: bool = Field(default=False)


@tool
def analyze_skin_image(image_base64: str, chief_complaint: str = "") -> dict:
    """
    分析皮肤图片，识别皮损特征。
    
    Args:
        image_base64: 图片的 base64 编码（带 data:image 前缀）
        chief_complaint: 患者主诉，帮助分析
    
    Returns:
        包含皮损描述、形态、颜色、分布特征的分析结果
    """
    llm = LLMProvider.get_multimodal_llm()
    
    prompt = """你是皮肤科影像专家。分析皮肤照片，描述皮损特征。

分析要点：
- 形态：斑、丘疹、水疱、结节等
- 颜色：红、褐、紫、白等
- 分布：局限性、泛发性、对称性
- 边界：清楚或模糊

用简洁专业的语言描述。"""
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=[
            {"type": "image_url", "image_url": {"url": image_base64}},
            {"type": "text", "text": f"请分析这张皮肤图片。患者主诉：{chief_complaint or '未说明'}"}
        ])
    ]
    
    response = llm.invoke(messages)
    
    return {
        "description": response.content,
        "type": "skin_analysis"
    }


@tool
def generate_diagnosis(
    symptoms: List[str],
    location: str,
    duration: str,
    additional_info: str = ""
) -> dict:
    """
    综合问诊信息生成初步诊断建议。
    
    Args:
        symptoms: 症状列表，如 ["瘙痒", "红斑", "脱皮"]
        location: 皮损部位，如 "面部" "手臂"
        duration: 持续时间，如 "三天" "一周"
        additional_info: 其他信息，如图片分析结果
    
    Returns:
        包含鉴别诊断、风险等级、护理建议的诊断结果
    """
    llm = LLMProvider.get_llm()
    
    prompt = f"""作为皮肤科专家，根据以下信息给出初步诊断建议：

症状：{', '.join(symptoms) if symptoms else '未明确'}
部位：{location or '未明确'}
持续时间：{duration or '未明确'}
{f'补充信息：{additional_info}' if additional_info else ''}

请给出：
1. 1-3个可能的诊断（按可能性排序）
2. 风险等级（low/medium/high/emergency）
3. 护理建议
4. 是否需要线下就诊

用自然语言回复，不要输出 JSON。"""
    
    response = llm.invoke(prompt)
    
    return {
        "diagnosis_text": response.content,
        "type": "diagnosis"
    }


def get_derma_tools():
    """获取皮肤科工具列表"""
    return [analyze_skin_image, generate_diagnosis]
