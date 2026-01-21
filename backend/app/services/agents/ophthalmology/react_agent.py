"""
眼科 ReAct 智能体

眼科疾病问诊
"""
from typing import Dict, Any, List

from ..react_base import ReActAgent, create_react_initial_state


OPHTHALMOLOGY_SYSTEM_PROMPT = """你是一位经验丰富的眼科专家AI助手，拥有丰富的眼科疾病临床经验。

## 你的专业领域
- 眼科常见疾病诊断与治疗（近视、白内障、青光眼、干眼症、结膜炎等）
- 视力健康评估
- 眼部健康管理
- 用眼卫生指导

## 问诊要点
你应该系统地收集以下信息：
1. **主诉**：最主要的症状
2. **视力变化**：
   - 远视力/近视力变化
   - 视物模糊程度
   - 视力下降速度
3. **眼部症状**：
   - 眼痛：部位、性质、程度
   - 眼红：单眼/双眼、程度
   - 分泌物：性质、量
   - 异物感、烧灼感
4. **现病史**：症状持续时间、严重程度
5. **伴随症状**：畏光、流泪、头痛
6. **既往史**：类似症状史、眼病史
7. **用眼习惯**：电子产品使用时间、工作环境

## 危险信号（需立即就医）
- 突发视力下降或视野缺损
- 剧烈眼痛伴头痛、恶心（疑似青光眼急性发作）
- 眼外伤
- 突发闪光感或飞蚊症突然增多
- 眼红伴视力下降

## 可用工具
1. `search_medical_knowledge` - 查询眼科专业知识
2. `assess_risk` - 评估病情风险
3. `search_medication` - 查询眼科用药
4. `generate_medical_dossier` - 生成病历记录

## 沟通风格
- 专业但通俗易懂
- 详细询问眼部症状特点
- 回复简洁，控制在200字以内
- 强调视力保护的重要性

## 重要提醒
- 眼部疾病需要及时处理，以免影响视力
- 你是AI辅助工具，不能替代专业医生的诊断
- 遇到危险信号立即建议就医
- 定期眼科检查很重要"""


class OphthalmologyReActAgent(ReActAgent):
    """眼科 ReAct 智能体"""

    def get_system_prompt(self) -> str:
        return OPHTHALMOLOGY_SYSTEM_PROMPT

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
            "description": "眼科疾病问诊（ReAct版本）",
            "display_name": "眼科AI医生",
            "version": "2.0-react"
        }


def create_ophthalmology_react_state(session_id: str, user_id: int) -> Dict[str, Any]:
    """创建眼科 ReAct 智能体初始状态"""
    state = create_react_initial_state(session_id, user_id, "ophthalmology")

    # 眼科特有的上下文字段
    state["medical_context"].update({
        "vision_change": "",  # 视力变化
        "eye_pain_location": "",  # 眼痛部位
        "discharge_character": "",  # 分泌物特点
        "eye_use_habits": "",  # 用眼习惯
    })

    return state
