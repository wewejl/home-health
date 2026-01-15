"""
动态快捷选项生成器

根据 AI 回复生成相关的快捷回复选项
"""
from typing import List
from pydantic import BaseModel, Field

from ..llm_provider import LLMProvider


class QuickOptionsOutput(BaseModel):
    """快捷选项输出"""
    options: List[str] = Field(
        description="3-4个快捷回复选项，每个2-6个字",
        default_factory=list
    )


QUICK_OPTIONS_PROMPT = """根据医生的回复，生成 3-4 个快捷回复选项供患者选择。

医生回复：
{response}

要求：
- 每个选项 2-6 个字
- 与当前问题相关
- 覆盖常见回答
- 符合口语表达

示例：
- 医生问"症状持续多久了" → ["刚开始", "几天了", "一周以上", "很久了"]
- 医生问"有其他症状吗" → ["有瘙痒", "有疼痛", "有脱皮", "没有了"]

直接输出选项列表，不要解释。"""


def generate_quick_options(response: str) -> List[dict]:
    """
    根据 AI 回复生成快捷选项
    
    Args:
        response: AI 的回复文本
    
    Returns:
        快捷选项列表 [{"text": "选项", "value": "选项", "category": "reply"}]
    """
    if not response or len(response) < 10:
        return []
    
    try:
        llm = LLMProvider.get_llm()
        
        # 使用结构化输出
        structured_llm = llm.with_structured_output(QuickOptionsOutput)
        
        prompt = QUICK_OPTIONS_PROMPT.format(response=response)
        result = structured_llm.invoke(prompt)
        
        return [
            {"text": opt, "value": opt, "category": "reply"}
            for opt in result.options[:4]  # 最多4个
        ]
    except Exception:
        # 降级：返回默认选项
        return [
            {"text": "好的", "value": "好的", "category": "reply"},
            {"text": "还有问题", "value": "我还有问题", "category": "reply"},
        ]
