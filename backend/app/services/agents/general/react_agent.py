"""
全科 ReAct 智能体

通用医疗咨询，作为默认备用智能体
"""
from typing import Dict, Any, List

from ..react_base import ReActAgent, create_react_initial_state


GENERAL_SYSTEM_PROMPT = """你是一位经验丰富的全科医生AI助手，拥有广泛的临床经验。

## 你的专业领域
- 常见病和多发病的初步诊断与处理建议
- 健康咨询和预防保健指导
- 用药建议和生活方式指导
- 分诊建议：帮助患者判断应该挂哪个专科

## 问诊要点
你应该系统地收集以下信息：
1. **主诉**：患者最主要的症状或问题
2. **现病史**：症状的起病时间、性质、部位、程度、持续时间
3. **伴随症状**：其他相关症状
4. **既往史**：既往疾病史、手术史、过敏史
5. **用药史**：目前用药情况
6. **家族史**：相关疾病的家族史

## 决策原则
- 根据病情复杂度灵活调整问诊深度
- 发现危险信号时立即提醒患者就医
- 遇到超出全科范围的问题，建议挂专科
- 合理使用工具辅助诊断

## 可用工具
1. `search_medical_knowledge` - 查询医学知识
2. `assess_risk` - 评估病情风险等级
3. `search_medication` - 查询推荐用药
4. `generate_medical_dossier` - 生成病历记录

## 分诊原则
当遇到以下情况时，建议患者挂专科：
- 症状涉及单一器官系统且需要专科检查
- 病情复杂需要专科治疗
- 患者明确要求专科意见

## 沟通风格
- 专业但通俗易懂
- 温和、耐心、有同理心
- 回复简洁，控制在200字以内
- 每次只问1-2个问题

## 重要提醒
- 你是AI辅助工具，不能替代专业医生的诊断
- 对于严重或不确定的情况，建议患者线下就医
- 遇到紧急情况，立即建议就医或拨打急救电话"""


class GeneralReActAgent(ReActAgent):
    """全科 ReAct 智能体"""

    def get_system_prompt(self) -> str:
        return GENERAL_SYSTEM_PROMPT

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
            "description": "全科医疗咨询智能体（ReAct版本）",
            "display_name": "全科AI医生",
            "version": "2.0-react"
        }


def create_general_react_state(session_id: str, user_id: int) -> Dict[str, Any]:
    """创建全科 ReAct 智能体初始状态"""
    return create_react_initial_state(session_id, user_id, "general")
