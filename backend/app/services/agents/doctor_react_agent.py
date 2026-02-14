"""
统一医生 ReAct 智能体

基于 Doctor 配置动态构建 ReAct 智能体，支持：
1. 动态加载科室基础能力
2. 注入个性化性格特征
3. 根据医生配置调整模型参数
"""
from typing import Dict, Any, List, Optional
from .react_base import ReActAgent, create_react_initial_state
from .persona_builder import build_system_prompt, get_recommended_temperature, get_recommended_max_tokens
from ...models.virtual_doctor import get_specialty_config


class DoctorReActAgent(ReActAgent):
    """
    统一医生 ReAct 智能体

    根据医生配置动态构建：
    - System Prompt = 科室基础 + 个性化性格
    - Tools = 根据科室和医生配置
    - Model Params = 根据性格类型推荐
    """

    def __init__(self, doctor_config: Dict[str, Any]):
        """
        初始化医生智能体

        Args:
            doctor_config: 医生配置字典，需包含：
                - agent_type: 科室类型
                - name: 医生姓名
                - title: 职称
                - personality_type: 性格类型（可选）
                - ai_temperature: 温度值（可选，会根据性格类型推荐）
                - ai_max_tokens: 最大 tokens（可选）
        """
        self.doctor_config = doctor_config
        self.specialty = doctor_config.get('agent_type', 'general')

        # 获取性格类型
        self.personality_type = (
            doctor_config.get('agent_config', {}).get('personality_type') or
            _extract_personality_from_config(doctor_config)
        )

        # 获取科室配置
        self.specialty_config = get_specialty_config(self.specialty)

        # 初始化基类
        super().__init__(enable_parallel_tools=True)

    def get_system_prompt(self) -> str:
        """
        获取完整的 System Prompt

        = 科室基础 Prompt + 个性化 Prompt
        """
        # 获取科室基础 Prompt
        base_prompt = self._get_base_prompt()

        # 构建完整 Prompt
        return build_system_prompt(
            base_prompt=base_prompt,
            doctor=self.doctor_config,
            personality_type=self.personality_type
        )

    def get_tools(self) -> List[str]:
        """获取智能体可用的工具列表"""
        # 从科室配置获取基础工具
        base_tools = self.specialty_config.get("base_tools", [
            "search_medical_knowledge",
            "assess_risk",
            "search_medication"
        ])

        # 医生可以配置额外工具（从 agent_config）
        extra_tools = self.doctor_config.get('agent_config', {}).get('extra_tools', [])

        return base_tools + extra_tools

    def get_model_config(self) -> Dict[str, Any]:
        """
        获取模型配置

        根据性格类型推荐最优参数，但允许医生配置覆盖
        """
        # 推荐参数
        recommended_temp = get_recommended_temperature(self.personality_type)
        recommended_max_tokens = get_recommended_max_tokens(self.personality_type)

        return {
            "temperature": self.doctor_config.get('ai_temperature', recommended_temp),
            "max_tokens": self.doctor_config.get('ai_max_tokens', recommended_max_tokens),
            "model": self.doctor_config.get('ai_model', 'qwen-plus'),
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """获取智能体能力配置"""
        return {
            "agent_type": self.specialty,
            "doctor_id": self.doctor_config.get('id'),
            "doctor_name": self.doctor_config.get('name'),
            "personality_type": self.personality_type,
            "actions": ["conversation"] + self._get_special_actions(),
            "accepts_media": self._get_accepted_media_types(),
            "ui_components": self.specialty_config.get("ui_components", ["TextBubble"]),
            "version": "3.0-doctor"
        }

    def _get_base_prompt(self) -> str:
        """
        获取科室基础 System Prompt

        这里从现有的科室智能体获取基础 Prompt
        """
        # 动态导入对应科室的智能体，获取其基础 Prompt
        specialty = self.specialty
        prompt_map = {
            "dermatology": _get_dermatology_base_prompt,
            "cardiology": _get_cardiology_base_prompt,
            "orthopedics": _get_orthopedics_base_prompt,
            "pediatrics": _get_pediatrics_base_prompt,
            "general": _get_general_base_prompt,
        }

        prompt_func = prompt_map.get(specialty, _get_general_base_prompt)
        return prompt_func()

    def _get_special_actions(self) -> List[str]:
        """获取科室特殊能力"""
        specialty_actions = {
            "dermatology": ["analyze_skin", "interpret_report"],
            "cardiology": ["interpret_ecg", "risk_assessment"],
            "orthopedics": ["interpret_xray"],
        }
        return specialty_actions.get(self.specialty, [])

    def _get_accepted_media_types(self) -> List[str]:
        """获取接受的媒体类型"""
        media_map = {
            "dermatology": ["image/jpeg", "image/png", "application/pdf"],
            "cardiology": ["image/jpeg", "image/png", "application/pdf"],
            "orthopedics": ["image/jpeg", "image/png", "application/pdf"],
        }
        return media_map.get(self.specialty, [])


# ========== 科室基础 Prompt 获取函数 ==========

def _get_dermatology_base_prompt() -> str:
    """皮肤科基础 Prompt"""
    from ..dermatology.react_agent import DERMATOLOGY_SYSTEM_PROMPT
    return DERMATOLOGY_SYSTEM_PROMPT


def _get_cardiology_base_prompt() -> str:
    """心血管科基础 Prompt"""
    from ..cardiology.react_agent import CARDIOLOGY_SYSTEM_PROMPT
    return CARDIOLOGY_SYSTEM_PROMPT


def _get_orthopedics_base_prompt() -> str:
    """骨科基础 Prompt"""
    from ..orthopedics.react_agent import ORTHOPEDICS_SYSTEM_PROMPT
    return ORTHOPEDICS_SYSTEM_PROMPT


def _get_pediatrics_base_prompt() -> str:
    """儿科基础 Prompt"""
    from ..pediatrics.react_agent import PEDIATRICS_SYSTEM_PROMPT
    return PEDIATRICS_SYSTEM_PROMPT


def _get_general_base_prompt() -> str:
    """全科基础 Prompt"""
    from ..general.react_agent import GENERAL_SYSTEM_PROMPT
    return GENERAL_SYSTEM_PROMPT


def _extract_personality_from_config(doctor_config: Dict[str, Any]) -> str:
    """从医生配置提取性格类型"""
    # 从 agent_config.personality_type 获取
    agent_config = doctor_config.get('agent_config', {})
    if agent_config and 'personality_type' in agent_config:
        return agent_config['personality_type']

    # 从 ai_persona_prompt 解析
    ai_prompt = doctor_config.get('ai_persona_prompt', '')
    if ai_prompt:
        if '温和' in ai_prompt or '亲切' in ai_prompt or 'friendly' in ai_prompt.lower():
            return 'friendly'
        elif '详细' in ai_prompt or '耐心' in ai_prompt or 'detailed' in ai_prompt.lower():
            return 'detailed'
        elif '干练' in ai_prompt or '直接' in ai_prompt or '简洁' in ai_prompt or 'concise' in ai_prompt.lower():
            return 'concise'

    # 默认专业型
    return 'formal'
