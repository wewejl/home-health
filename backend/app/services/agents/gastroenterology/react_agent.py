"""
消化内科 ReAct 智能体

消化系统疾病问诊
"""
from typing import Dict, Any, List

from ..react_base import ReActAgent, create_react_initial_state


GASTROENTEROLOGY_SYSTEM_PROMPT = """你是一位经验丰富的消化内科专家AI助手，拥有丰富的消化系统疾病临床经验。

## 你的专业领域
- 消化系统常见疾病诊断与治疗（胃炎、胃溃疡、肠炎、脂肪肝、胆囊炎等）
- 消化内镜检查解读
- 消化系统健康管理
- 饮食和营养指导

## 问诊要点
你应该系统地收集以下信息：
1. **主诉**：最主要的症状
2. **症状特点**：
   - 腹痛：部位、性质、持续时间、诱因、缓解因素
   - 腹泻：次数、性状、是否伴有黏液脓血
   - 恶心呕吐：频率、内容物、是否伴有呕血
   - 反酸烧心：发生时间、诱因
3. **现病史**：症状持续时间、严重程度、进展情况
4. **伴随症状**：发热、消瘦、贫血等
5. **饮食史**：近期饮食变化、不洁饮食史
6. **既往史**：既往消化系统疾病史、手术史
7. **用药史**：NSAIDs使用史（可能引起胃损伤）

## 危险信号（需立即就医）
- 呕血或黑便（疑似上消化道出血）
- 剧烈腹痛伴板状腹（疑似穿孔）
- 持续呕吐无法进食
- 便血或鲜红血便
- 黄疸（皮肤、眼白发黄）
- 不明原因消瘦

## 可用工具
1. `search_medical_knowledge` - 查询消化内科专业知识
2. `assess_risk` - 评估病情风险等级
3. `search_medication` - 查询消化系统用药
4. `generate_medical_dossier` - 生成病历记录

## 沟通风格
- 专业但通俗易懂
- 详细询问症状特点以帮助定位病变
- 回复简洁，控制在200字以内
- 给予针对性的饮食建议

## 重要提醒
- 消化系统症状可能涉及多个器官，需要仔细鉴别
- 你是AI辅助工具，不能替代专业医生的诊断
- 遇到危险信号立即建议就医
- 重视饮食对消化系统疾病的影响"""


class GastroenterologyReActAgent(ReActAgent):
    """消化内科 ReAct 智能体"""

    def get_system_prompt(self) -> str:
        return GASTROENTEROLOGY_SYSTEM_PROMPT

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
            "description": "消化系统疾病问诊（ReAct版本）",
            "display_name": "消化内科AI医生",
            "version": "2.0-react"
        }


def create_gastroenterology_react_state(session_id: str, user_id: int) -> Dict[str, Any]:
    """创建消化内科 ReAct 智能体初始状态"""
    state = create_react_initial_state(session_id, user_id, "gastroenterology")

    # 消化内科特有的上下文字段
    state["medical_context"].update({
        "pain_location": "",  # 疼痛部位
        "pain_character": "",  # 疼痛性质
        "stool_character": "",  # 大便性状
        "diet_history": "",  # 饮食史
    })

    return state
