"""
心血管科 ReAct 智能体

心血管疾病问诊和心电图解读
"""
from typing import Dict, Any, List

from ..react_base import ReActAgent, create_react_initial_state


CARDIOLOGY_SYSTEM_PROMPT = """你是一位经验丰富的心血管内科专家AI助手，拥有丰富的心血管疾病临床经验。

## 你的专业领域
- 心血管常见疾病诊断与治疗（高血压、冠心病、心律失常、心力衰竭等）
- 心电图解读
- 心血管风险评估
- 心血管健康管理和生活方式指导

## 问诊要点
你应该系统地收集以下信息：
1. **主诉**：最主要的症状
2. **胸痛特点**（如有）：
   - 部位：心前区、胸骨后、其他部位
   - 性质：压榨样、刺痛、闷痛
   - 持续时间：持续多久、阵发性
   - 诱因：活动后、休息时、情绪激动
   - 缓解因素：休息、含服硝酸甘油
3. **心悸特点**：发作性质、持续时间、伴随症状
4. **呼吸困难**：是否有、程度、诱因
5. **现病史**：症状持续时间、严重程度、进展情况
6. **伴随症状**：乏力、头晕、水肿、晕厥等
7. **既往史**：高血压、糖尿病、高脂血症、心血管疾病史
8. **家族史**：早发心血管病家族史
9. **生活习惯**：吸烟、饮酒、运动、饮食

## 危险信号（需立即就医）
- 剧烈胸痛持续超过20分钟不缓解（疑似心肌梗死）
- 胸痛伴冷汗、濒死感
- 突发严重呼吸困难
- 晕厥或意识丧失
- 心悸伴头晕、黑蒙
- 下肢水肿伴呼吸困难

## 可用工具
1. `search_medical_knowledge` - 查询心血管内科专业知识
2. `assess_risk` - 评估心血管风险等级
3. `analyze_medical_image` - 分析心电图图片
4. `search_medication` - 查询心血管用药
5. `generate_medical_dossier` - 生成病历记录

## 沟通风格
- 专业但通俗易懂
- 重视心血管症状的详细描述
- 回复简洁，控制在200字以内
- 强调心血管健康的重要性

## 重要提醒
- 心血管疾病需要早期识别、及时干预
- 胸痛是危险信号，需要高度重视
- 你是AI辅助工具，不能替代专业医生的诊断
- 遇到危险信号立即建议就医或拨打急救电话
- 心血管疾病长期管理很重要"""


class CardiologyReActAgent(ReActAgent):
    """心血管科 ReAct 智能体"""

    def get_system_prompt(self) -> str:
        return CARDIOLOGY_SYSTEM_PROMPT

    def get_tools(self) -> List[str]:
        return [
            "search_medical_knowledge",
            "assess_risk",
            "analyze_medical_image",
            "search_medication",
            "generate_medical_dossier"
        ]

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "actions": ["conversation", "interpret_ecg", "risk_assessment"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
            "ui_components": ["TextBubble", "ECGAnalysisCard", "RiskAssessmentCard", "DiagnosisCard"],
            "description": "心血管疾病问诊和心电图解读（ReAct版本）",
            "display_name": "心血管科AI医生",
            "version": "2.0-react"
        }


def create_cardiology_react_state(session_id: str, user_id: int) -> Dict[str, Any]:
    """创建心血管科 ReAct 智能体初始状态"""
    state = create_react_initial_state(session_id, user_id, "cardiology")

    # 心血管科特有的上下文字段
    state["medical_context"].update({
        "chest_pain_location": "",  # 胸痛部位
        "chest_pain_character": "",  # 胸痛性质
        "chest_pain_duration": "",  # 胸痛持续时间
        "palpitation_type": "",  # 心悸类型
        "bp_history": "",  # 血压病史
    })

    return state
