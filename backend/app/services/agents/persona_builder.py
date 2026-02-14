"""
Persona 提示词构建器

根据虚拟医生的性格配置，构建个性化的 System Prompt
"""
from typing import Dict, Any, Optional
from ...models.virtual_doctor import (
    VirtualDoctorExtension,
    get_specialty_config
)


def build_system_prompt(
    base_prompt: str,
    doctor: Any,
    personality_type: Optional[str] = None
) -> str:
    """
    构建完整的 System Prompt = 科室基础 Prompt + 个性化 Prompt

    Args:
        base_prompt: 科室的基础系统提示词
        doctor: 医生实例（需要有 agent_type, name, title 等属性）
        personality_type: 性格类型，如果不指定则从 doctor.ai_persona_prompt 解析

    Returns:
        完整的系统提示词
    """
    # 获取性格类型
    if not personality_type:
        personality_type = _extract_personality_type(doctor)

    # 获取科室和医生信息
    specialty = doctor.agent_type if hasattr(doctor, 'agent_type') else "general"
    doctor_name = getattr(doctor, 'name', 'AI医生')
    doctor_title = getattr(doctor, 'title', '')

    # 获取科室配置
    specialty_config = get_specialty_config(specialty)
    specialty_name = specialty_config.get("name", "全科")

    # 获取性格配置
    personality_config = VirtualDoctorExtension.get_personality_config(personality_type)
    style_prompt = VirtualDoctorExtension.build_style_prompt(personality_type)

    # 构建个性化问候
    greeting = VirtualDoctorExtension.build_greeting(doctor_name, personality_type)

    # 组装完整 Prompt
    full_prompt = f"""{base_prompt}

---

## 你的身份

你是 {doctor_name}，{doctor_title}，{specialty_name}AI医生。

{greeting}

{style_prompt}

---

## 专业能力

你的专业能力基于 {specialty_name} 医学知识库，你可以：
- 进行专业的问诊和信息收集
- 提供初步诊断建议和健康指导
- 解答相关医学问题
- 必要时建议患者线下就医

## 重要提醒

- 你是AI辅助工具，不能替代专业医生的诊断
- 不提供确定性诊断，只提供参考建议
- 对于严重或不确定的情况，建议患者线下就医
"""

    return full_prompt


def build_personality_prompt_fragment(
    personality_type: str,
    doctor_name: str = "AI医生"
) -> str:
    """
    构建纯个性化的 Prompt 片段（用于增量更新）

    Args:
        personality_type: 性格类型
        doctor_name: 医生姓名

    Returns:
        个性化 Prompt 片段
    """
    greeting = VirtualDoctorExtension.build_greeting(doctor_name, personality_type)
    style_prompt = VirtualDoctorExtension.build_style_prompt(personality_type)

    return f"""{greeting}

{style_prompt}"""


def get_recommended_temperature(personality_type: str) -> float:
    """根据性格类型获取推荐的 temperature 值"""
    return VirtualDoctorExtension.get_recommended_temperature(personality_type)


def get_recommended_max_tokens(personality_type: str) -> int:
    """根据性格类型获取推荐的 max_tokens 值"""
    # 温和亲切型可以多说点，干练直接型少说点
    if personality_type == "friendly":
        return 600
    elif personality_type == "detailed":
        return 700
    elif personality_type == "concise":
        return 400
    else:  # formal
        return 500


def _extract_personality_type(doctor: Any) -> str:
    """
    从医生实例提取性格类型

    优先级：
    1. agent_config.personality_type
    2. ai_persona_prompt (从现有字段解析）
    3. 默认 formal
    """
    # 尝试从 agent_config 获取
    if hasattr(doctor, 'agent_config') and doctor.agent_config:
        if isinstance(doctor.agent_config, dict):
            return doctor.agent_config.get('personality_type', 'formal')

    # 尝试从 ai_persona_prompt 解析
    if hasattr(doctor, 'ai_persona_prompt') and doctor.ai_persona_prompt:
        prompt = doctor.ai_persona_prompt
        if '温和' in prompt or '亲切' in prompt or 'friendly' in prompt.lower():
            return 'friendly'
        elif '详细' in prompt or '耐心' in prompt or 'detailed' in prompt.lower():
            return 'detailed'
        elif '干练' in prompt or '直接' in prompt or '简洁' in prompt or 'concise' in prompt.lower():
            return 'concise'

    # 默认专业型
    return 'formal'


def get_personality_summary(personality_type: str) -> Dict[str, Any]:
    """
    获取性格类型摘要（用于 API 响应）
    """
    config = VirtualDoctorExtension.get_personality_config(personality_type)
    return {
        "code": personality_type,
        "name": config.get("name"),
        "description": config.get("description"),
        "style_tags": config.get("style_tags", []),
        "temperature": config.get("temperature", 0.7),
        "greeting_template": config.get("greeting_template", ""),
    }


def list_available_personalities() -> list:
    """列出所有可用的性格类型"""
    return VirtualDoctorExtension.list_available_personalities()
