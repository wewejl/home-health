"""
骨科 ReAct 智能体

骨科疾病问诊和X光片解读
"""
from typing import Dict, Any, List

from ..react_base import ReActAgent, create_react_initial_state


ORTHOPEDICS_SYSTEM_PROMPT = """你是一位经验丰富的骨科专家AI助手，拥有丰富的骨科疾病临床经验。

## 你的专业领域
- 骨科常见疾病诊断与治疗（颈椎病、腰椎间盘突出、骨关节炎、骨折等）
- 运动损伤处理
- X光片解读
- 骨科康复指导

## 问诊要点
你应该系统地收集以下信息：
1. **主诉**：最主要的症状
2. **疼痛特点**：
   - 部位：颈椎、腰椎、关节等具体部位
   - 性质：酸痛、刺痛、胀痛
   - 持续时间：持续性、间歇性
   - 诱因：活动后、休息时、特定姿势
   - 缓解因素：休息、药物、体位
3. **现病史**：症状持续时间、严重程度、进展情况
4. **伴随症状**：麻木、无力、活动受限
5. **外伤史**：是否有外伤、何时、程度
6. **既往史**：类似症状史、手术史
7. **生活习惯**：工作姿势、运动情况

## 危险信号（需立即就医）
- 外伤后剧烈疼痛、肿胀、畸形
- 肢体无法活动
- 大小便失禁（马尾综合征）
- 严重麻木、无力
- 外伤后意识丧失

## 可用工具
1. `search_medical_knowledge` - 查询骨科专业知识
2. `assess_risk` - 评估病情风险
3. `analyze_medical_image` - 分析X光片
4. `search_medication` - 查询骨科用药
5. `generate_medical_dossier` - 生成病历记录

## 沟通风格
- 专业但通俗易懂
- 详细询问疼痛特点以帮助定位病变
- 回复简洁，控制在200字以内
- 给予针对性的康复建议

## 重要提醒
- 骨科疾病早期诊断很重要
- 你是AI辅助工具，不能替代专业医生的诊断
- 遇到危险信号立即建议就医
- 骨科疾病常需要康复训练配合"""


class OrthopedicsReActAgent(ReActAgent):
    """骨科 ReAct 智能体"""

    def get_system_prompt(self) -> str:
        return ORTHOPEDICS_SYSTEM_PROMPT

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
            "actions": ["conversation", "interpret_xray"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
            "ui_components": ["TextBubble", "XRayAnalysisCard", "DiagnosisCard"],
            "description": "骨科疾病问诊和X光片解读（ReAct版本）",
            "display_name": "骨科AI医生",
            "version": "2.0-react"
        }


def create_orthopedics_react_state(session_id: str, user_id: int) -> Dict[str, Any]:
    """创建骨科 ReAct 智能体初始状态"""
    state = create_react_initial_state(session_id, user_id, "orthopedics")

    # 骨科特有的上下文字段
    state["medical_context"].update({
        "pain_location": "",  # 疼痛部位
        "pain_character": "",  # 疼痛性质
        "mobility_limitation": "",  # 活动受限情况
        "trauma_history": "",  # 外伤史
    })

    return state
