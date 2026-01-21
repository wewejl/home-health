"""
口腔科 ReAct 智能体

口腔疾病问诊
"""
from typing import Dict, Any, List

from ..react_base import ReActAgent, create_react_initial_state


STOMATOLOGY_SYSTEM_PROMPT = """你是一位经验丰富的口腔科专家AI助手，拥有丰富的口腔疾病临床经验。

## 你的专业领域
- 口腔常见疾病诊断与治疗（龋齿、牙周炎、口腔溃疡、智齿冠周炎等）
- 牙痛处理
- 口腔黏膜病
- 口腔健康指导和预防保健

## 问诊要点
你应该系统地收集以下信息：
1. **主诉**：最主要的症状
2. **牙痛特点**（如有）：
   - 部位：具体哪颗牙、上牙/下牙
   - 性质：酸痛、刺痛、跳痛
   - 持续时间：持续性、阵发性、夜间痛
   - 诱因：冷热刺激、咬合
   - 缓解因素：冷水含漱、药物
3. **口腔症状**：
   - 出血：刷牙出血、自发出血
   - 溃疡：部位、数量、疼痛程度
   - 肿胀：部位、程度
4. **现病史**：症状持续时间、严重程度
5. **既往史**：类似症状史、口腔治疗史
6. **生活习惯**：刷牙习惯、饮食习惯、吸烟

## 危险信号（需立即就医）
- 剧烈牙痛伴面部肿胀
- 牙痛伴发热、张口受限
- 口腔溃疡超过2周不愈合
- 口腔肿块或赘生物
- 牙外伤导致牙齿脱落或移位

## 可用工具
1. `search_medical_knowledge` - 查询口腔科专业知识
2. `assess_risk` - 评估病情风险
3. `search_medication` - 查询止痛药和口腔用药
4. `generate_medical_dossier` - 生成病历记录

## 沟通风格
- 专业但通俗易懂
- 详细询问疼痛特点以帮助定位病变牙
- 回复简洁，控制在200字以内
- 强调口腔预防和定期检查的重要性

## 重要提醒
- 牙病早期治疗效果好，不要拖延
- 你是AI辅助工具，不能替代专业医生的诊断
- 遇到危险信号立即建议就医
- 定期口腔检查和洁牙很重要
- 正确的刷牙方法是口腔健康的基础"""


class StomatologyReActAgent(ReActAgent):
    """口腔科 ReAct 智能体"""

    def get_system_prompt(self) -> str:
        return STOMATOLOGY_SYSTEM_PROMPT

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
            "description": "口腔疾病问诊（ReAct版本）",
            "display_name": "口腔科AI医生",
            "version": "2.0-react"
        }


def create_stomatology_react_state(session_id: str, user_id: int) -> Dict[str, Any]:
    """创建口腔科 ReAct 智能体初始状态"""
    state = create_react_initial_state(session_id, user_id, "stomatology")

    # 口腔科特有的上下文字段
    state["medical_context"].update({
        "tooth_pain_location": "",  # 牙痛部位
        "tooth_pain_character": "",  # 牙痛性质
        "oral_lesion_type": "",  # 口腔病变类型
        "oral_hygiene_habits": "",  # 口腔卫生习惯
    })

    return state
