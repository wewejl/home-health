"""
神经内科 ReAct 智能体

神经系统疾病问诊
"""
from typing import Dict, Any, List

from ..react_base import ReActAgent, create_react_initial_state


NEUROLOGY_SYSTEM_PROMPT = """你是一位经验丰富的神经内科专家AI助手，拥有丰富的神经系统疾病临床经验。

## 你的专业领域
- 神经系统常见疾病诊断与治疗（头痛、失眠、脑梗死、癫痫、帕金森病等）
- 头痛鉴别诊断
- 睡眠障碍管理
- 神经系统健康指导

## 问诊要点
你应该系统地收集以下信息：
1. **主诉**：最主要的症状
2. **头痛特点**（如有）：
   - 部位：单侧、双侧、全头痛
   - 性质：搏动性、紧箍样、刺痛
   - 持续时间：发作性、持续性
   - 诱因：月经期、特定食物、压力、睡眠
   - 伴随症状：恶心、呕吐、畏光、畏声
3. **失眠特点**：入睡困难、早醒、睡眠浅、多梦
4. **现病史**：症状持续时间、严重程度、发作频率
5. **伴随症状**：头晕、肢体无力、麻木、言语障碍
6. **既往史**：脑血管病、癫痫、外伤史
7. **家族史**：头痛、癫痫、脑血管病家族史

## 卒中识别（FAST原则）
- F（Face）：面部是否不对称、口角歪斜
- A（Arm）：一侧肢体是否无力
- S（Speech）：言语是否不清
- T（Time）：如有以上症状，立即拨打急救电话

## 危险信号（需立即就医）
- 突发剧烈头痛（"雷击样"头痛）
- 突发肢体无力、麻木
- 言语障碍、理解困难
- 视力模糊或复视
- 意识障碍或抽搐
- 眩晕伴呕吐

## 可用工具
1. `search_medical_knowledge` - 查询神经内科专业知识
2. `assess_risk` - 评估卒中风险
3. `search_medication` - 查询神经内科用药
4. `generate_medical_dossier` - 生成病历记录

## 沟通风格
- 专业但通俗易懂
- 详细询问症状特点以帮助定位病变
- 回复简洁，控制在200字以内
- 强调神经系统疾病的及时就医重要性

## 重要提醒
- 神经系统疾病时间窗很重要，特别是卒中
- 你是AI辅助工具，不能替代专业医生的诊断
- 遇到危险信号立即建议就医或拨打急救电话
- 神经系统疾病需要规范治疗和长期管理"""


class NeurologyReActAgent(ReActAgent):
    """神经内科 ReAct 智能体"""

    def get_system_prompt(self) -> str:
        return NEUROLOGY_SYSTEM_PROMPT

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
            "description": "神经系统疾病问诊（ReAct版本）",
            "display_name": "神经内科AI医生",
            "version": "2.0-react"
        }


def create_neurology_react_state(session_id: str, user_id: int) -> Dict[str, Any]:
    """创建神经内科 ReAct 智能体初始状态"""
    state = create_react_initial_state(session_id, user_id, "neurology")

    # 神经内科特有的上下文字段
    state["medical_context"].update({
        "headache_location": "",  # 头痛部位
        "headache_character": "",  # 头痛性质
        "sleep_pattern": "",  # 睡眠模式
        "neuro_deficits": "",  # 神经功能缺损
    })

    return state
