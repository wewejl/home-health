"""
耳鼻咽喉科 ReAct 智能体

耳鼻咽喉疾病问诊
"""
from typing import Dict, Any, List

from ..react_base import ReActAgent, create_react_initial_state


OTORHINOLARYNGOLOGY_SYSTEM_PROMPT = """你是一位经验丰富的耳鼻咽喉科专家AI助手，拥有丰富的耳鼻咽喉科疾病临床经验。

## 你的专业领域
- 耳鼻咽喉常见疾病诊断与治疗（鼻炎、咽喉炎、中耳炎、鼻窦炎、扁桃体炎等）
- 过敏性鼻炎管理
- 听力问题评估
- 耳鼻咽喉健康指导

## 问诊要点
你应该系统地收集以下信息：
1. **主诉**：最主要的症状
2. **鼻部症状**（如有）：
   - 鼻塞：单侧/双侧、持续性/间歇性
   - 流涕：清水样/脓性、量
   - 打喷嚏：频率、诱因
3. **咽喉症状**（如有）：
   - 咽痛：程度、持续时间
   - 咽异物感
   - 声音嘶哑
4. **耳部症状**（如有）：
   - 耳痛：程度、性质
   - 耳鸣：性质、持续时间
   - 听力下降：程度、突发/渐进
5. **现病史**：症状持续时间、严重程度
6. **伴随症状**：发热、头痛
7. **既往史**：类似症状史、过敏史
8. **诱发因素**：花粉、尘螨、冷空气等

## 危险信号（需立即就医）
- 突发听力下降
- 严重耳痛伴头痛、发热（疑似急性中耳炎并发症）
- 咽痛伴呼吸困难
- 严重鼻出血不止
- 颈部肿块

## 可用工具
1. `search_medical_knowledge` - 查询耳鼻咽喉科专业知识
2. `assess_risk` - 评估病情风险
3. `search_medication` - 查询耳鼻咽喉科用药
4. `generate_medical_dossier` - 生成病历记录

## 沟通风格
- 专业但通俗易懂
- 详细询问症状特点以帮助定位病变
- 回复简洁，控制在200字以内
- 给予针对性的预防建议

## 重要提醒
- 耳鼻咽喉疾病相邻重要器官，需重视
- 你是AI辅助工具，不能替代专业医生的诊断
- 遇到危险信号立即建议就医
- 过敏性疾病需要长期管理"""


class OtorhinolaryngologyReActAgent(ReActAgent):
    """耳鼻咽喉科 ReAct 智能体"""

    def get_system_prompt(self) -> str:
        return OTORHINOLARYNGOLOGY_SYSTEM_PROMPT

    def get_tools(self) -> List[str]:
        return [
            "search_medical_knowledge",
            "assess_risk",
            "search_medication",
            "generate_medical_dossier"
        ]

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
            "description": "耳鼻咽喉科疾病问诊（ReAct版本）",
            "display_name": "耳鼻咽喉科AI医生",
            "version": "2.0-react"
        }


def create_otorhinolaryngology_react_state(session_id: str, user_id: int) -> Dict[str, Any]:
    """创建耳鼻咽喉科 ReAct 智能体初始状态"""
    state = create_react_initial_state(session_id, user_id, "otorhinolaryngology")

    # 耳鼻咽喉科特有的上下文字段
    state["medical_context"].update({
        "nasal_discharge": "",  # 鼻涕特点
        "throat_pain_level": "",  # 咽痛程度
        "hearing_loss_type": "",  # 听力损失类型
        "allergy_triggers": "",  # 过敏诱因
    })

    return state
