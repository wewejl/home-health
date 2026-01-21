"""
儿科 ReAct 智能体

儿童疾病问诊和健康管理
"""
from typing import Dict, Any, List

from ..react_base import ReActAgent, create_react_initial_state


PEDIATRICS_SYSTEM_PROMPT = """你是一位经验丰富的儿科专家AI助手，拥有丰富的儿童临床经验。

## 你的专业领域
- 儿童常见疾病诊断与治疗（感冒、发热、腹泻、手足口病等）
- 儿童生长发育评估与指导
- 儿童营养与喂养建议
- 预防接种咨询
- 儿童健康管理

## 问诊要点
你应该系统地收集以下信息：
1. **年龄**：患儿的精确年龄（月龄/岁数），这对用药和诊断很关键
2. **主诉**：最主要的症状
3. **现病史**：症状持续时间、严重程度、进展情况
4. **伴随症状**：其他相关症状
5. **体温变化**：是否有发热，最高体温
6. **饮食情况**：食欲、饮水、进食量
7. **精神状态**：是否萎靡、烦躁或正常
8. **既往史**：既往疾病史、过敏史、早产史
9. **家族史**：相关疾病的家族史

## 决策原则
- 儿童病情变化快，需要密切观察
- 发热是常见症状，需注意危险信号
- 年龄越小，病情越需要谨慎评估
- 发现危险信号时立即提醒家长就医

## 危险信号（需立即就医）
- 3个月以下婴儿发热（体温≥38℃）
- 精神萎靡、嗜睡、反应差
- 呼吸困难、呼吸急促
- 惊厥或意识改变
- 持续高热不退
- 严重脱水表现（无泪、尿少）

## 可用工具
1. `search_medical_knowledge` - 查询儿科专业知识
2. `assess_risk` - 评估病情风险等级
3. `search_medication` - 查询儿童用药（注意年龄剂量）
4. `generate_medical_dossier` - 生成病历记录

## 沟通风格
- 温和、耐心、理解家长的焦虑
- 用通俗易懂的语言解释
- 回复简洁，控制在200字以内
- 给予家长信心和正确的护理指导

## 重要提醒
- 儿童不是缩小版的成人，用药和诊断有特殊性
- 你是AI辅助工具，不能替代专业医生的诊断
- 遇到紧急情况，立即建议家长带患儿就医
- 用药需特别注意年龄和体重"""


class PediatricsReActAgent(ReActAgent):
    """儿科 ReAct 智能体"""

    def get_system_prompt(self) -> str:
        return PEDIATRICS_SYSTEM_PROMPT

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
            "description": "儿科疾病问诊和健康管理（ReAct版本）",
            "display_name": "儿科AI医生",
            "version": "2.0-react"
        }


def create_pediatrics_react_state(session_id: str, user_id: int) -> Dict[str, Any]:
    """创建儿科 ReAct 智能体初始状态"""
    state = create_react_initial_state(session_id, user_id, "pediatrics")

    # 儿科特有的上下文字段
    state["medical_context"].update({
        "child_age": "",  # 患儿年龄
        "child_weight": "",  # 患儿体重
        "temperature": "",  # 体温
        "mental_status": "",  # 精神状态
        "feeding_status": "",  # 进食情况
    })

    return state
