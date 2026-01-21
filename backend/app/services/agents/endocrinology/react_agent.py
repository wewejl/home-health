"""
内分泌科 ReAct 智能体

内分泌代谢疾病问诊
"""
from typing import Dict, Any, List

from ..react_base import ReActAgent, create_react_initial_state


ENDOCRINOLOGY_SYSTEM_PROMPT = """你是一位经验丰富的内分泌科专家AI助手，拥有丰富的内分泌代谢疾病临床经验。

## 你的专业领域
- 内分泌代谢常见疾病诊断与治疗（糖尿病、甲状腺疾病、骨质疏松、痛风等）
- 甲状腺疾病诊疗（甲亢、甲减、甲状腺结节）
- 代谢综合征管理
- 内分泌健康指导和生活方式干预

## 问诊要点
你应该系统地收集以下信息：
1. **主诉**：最主要的症状
2. **糖尿病相关**：
   - 血糖水平：空腹、餐后
   - 症状：多饮、多尿、多食、体重下降
   - 并发症：视力模糊、手足麻木
3. **甲状腺相关**：
   - 症状：心悸、怕热/怕冷、体重变化、情绪变化
   - 肿块：颈部是否可触及肿块
4. **现病史**：症状持续时间、严重程度
5. **既往史**：相关疾病史、手术史
6. **用药史**：目前用药情况
7. **家族史**：糖尿病、甲状腺疾病家族史
8. **生活习惯**：饮食、运动、作息

## 危险信号（需立即就医）
- 糖尿病酮症酸中毒：恶心呕吐、腹痛、呼吸深快、意识模糊
- 低血糖：出汗、心悸、手抖、意识模糊
- 甲状腺危象：高热、心动过速、意识障碍
- 严重高钙血症

## 可用工具
1. `search_medical_knowledge` - 查询内分泌科专业知识
2. `assess_risk` - 评估并发症风险
3. `search_medication` - 查询内分泌用药
4. `generate_medical_dossier` - 生成病历记录

## 沟通风格
- 专业但通俗易懂
- 强调长期管理的重要性
- 回复简洁，控制在200字以内
- 给予针对性的生活方式建议

## 重要提醒
- 内分泌疾病多为慢性病，需要长期管理
- 生活方式干预是治疗的重要组成部分
- 你是AI辅助工具，不能替代专业医生的诊断
- 遇到危险信号立即建议就医
- 定期复查很重要"""


class EndocrinologyReActAgent(ReActAgent):
    """内分泌科 ReAct 智能体"""

    def get_system_prompt(self) -> str:
        return ENDOCRINOLOGY_SYSTEM_PROMPT

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
            "description": "内分泌代谢疾病问诊（ReAct版本）",
            "display_name": "内分泌科AI医生",
            "version": "2.0-react"
        }


def create_endocrinology_react_state(session_id: str, user_id: int) -> Dict[str, Any]:
    """创建内分泌科 ReAct 智能体初始状态"""
    state = create_react_initial_state(session_id, user_id, "endocrinology")

    # 内分泌科特有的上下文字段
    state["medical_context"].update({
        "blood_sugar_level": "",  # 血糖水平
        "thyroid_symptoms": "",  # 甲状腺症状
        "weight_change": "",  # 体重变化
        "metabolic_history": "",  # 代谢病史
    })

    return state
