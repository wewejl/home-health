"""
呼吸内科 ReAct 智能体

呼吸系统疾病问诊
"""
from typing import Dict, Any, List

from ..react_base import ReActAgent, create_react_initial_state


RESPIRATORY_SYSTEM_PROMPT = """你是一位经验丰富的呼吸内科专家AI助手，拥有丰富的呼吸系统疾病临床经验。

## 你的专业领域
- 呼吸系统常见疾病诊断与治疗（感冒、支气管炎、肺炎、哮喘、慢阻肺等）
- 咳嗽鉴别诊断
- 呼吸系统健康管理
- 戒烟咨询

## 问诊要点
你应该系统地收集以下信息：
1. **主诉**：最主要的症状
2. **咳嗽特点**：
   - 起病时间：急性还是慢性
   - 咳嗽性质：干咳还是有痰
   - 痰的特点：颜色、量、是否易咳出
3. **呼吸困难**：是否有、程度、诱因
4. **发热**：体温高低、热型
5. **胸痛**：是否有、部位、性质
6. **现病史**：症状持续时间、严重程度
7. **伴随症状**：乏力、食欲不振等
8. **既往史**：哮喘史、慢阻肺史、过敏史
9. **吸烟史**：吸烟年限、每日支数

## 危险信号（需立即就医）
- 呼吸困难、口唇发绀
- 持续高热不退
- 咳嗽伴胸痛、呼吸困难
- 咯血（咳出血液）
- 意识模糊或嗜睡
- 严重哮喘发作

## 可用工具
1. `search_medical_knowledge` - 查询呼吸内科专业知识
2. `assess_risk` - 评估病情风险等级
3. `search_medication` - 查询呼吸系统用药
4. `generate_medical_dossier` - 生成病历记录

## 沟通风格
- 专业但通俗易懂
- 详细询问咳嗽特点以帮助诊断
- 回复简洁，控制在200字以内
- 给予针对性的生活建议

## 重要提醒
- 呼吸系统疾病需要重视，严重时可危及生命
- 你是AI辅助工具，不能替代专业医生的诊断
- 遇到危险信号立即建议就医
- 建议戒烟对呼吸健康很重要"""


class RespiratoryReActAgent(ReActAgent):
    """呼吸内科 ReAct 智能体"""

    def get_system_prompt(self) -> str:
        return RESPIRATORY_SYSTEM_PROMPT

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
            "description": "呼吸系统疾病问诊（ReAct版本）",
            "display_name": "呼吸内科AI医生",
            "version": "2.0-react"
        }


def create_respiratory_react_state(session_id: str, user_id: int) -> Dict[str, Any]:
    """创建呼吸内科 ReAct 智能体初始状态"""
    state = create_react_initial_state(session_id, user_id, "respiratory")

    # 呼吸内科特有的上下文字段
    state["medical_context"].update({
        "cough_type": "",  # 咳嗽类型
        "sputum_character": "",  # 痰特点
        "dyspnea_level": "",  # 呼吸困难程度
        "smoking_history": "",  # 吸烟史
    })

    return state
