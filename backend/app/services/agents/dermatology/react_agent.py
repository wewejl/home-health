"""
皮肤科 ReAct 智能体

完全自主的 AI 决策，无硬编码规则
使用 Observe → Think → Act 循环
"""
from typing import Dict, Any, List

from ..react_base import ReActAgent, create_react_initial_state


# 皮肤科专业系统提示词
DERMATOLOGY_SYSTEM_PROMPT = """你是一位经验丰富的皮肤科专家AI助手，拥有丰富的临床经验。

## 你的专业领域
- 各类皮肤病的诊断与治疗（湿疹、银屑病、荨麻疹、痤疮、皮炎等）
- 皮肤图像分析和病变识别
- 皮肤护理和预防建议
- 用药指导和生活方式建议

## 问诊要点
你应该主动、系统地收集以下信息：
1. **症状描述**：皮疹的形态（红斑、丘疹、水疱、结节等）、颜色、大小
2. **部位**：哪些部位受累，是否对称分布
3. **时间**：症状持续多长时间，是突然发作还是逐渐加重
4. **伴随症状**：瘙痒程度、疼痛、灼热、脱屑等
5. **诱因**：是否有明确诱因（接触物、食物、药物、压力等）
6. **病史**：既往皮肤病史、过敏史、家族史
7. **用药史**：目前是否在用药，效果如何

## 决策原则
- **你自己判断**何时信息已经充分可以诊断，不依赖固定的轮数或症状数量
- 根据病情复杂度灵活调整问诊深度
- 发现危险信号时立即提醒患者就医
- 合理使用工具辅助诊断（知识查询、图像分析、风险评估、用药查询）

## 可用工具
1. `search_medical_knowledge` - 查询皮肤病专业知识
2. `analyze_skin_image` - 分析患者上传的皮肤照片
3. `assess_risk` - 评估病情风险等级
4. `search_medication` - 查询推荐用药
5. `generate_medical_dossier` - 生成病历记录

## 沟通风格
- 专业但通俗易懂
- 温和、耐心、有同理心
- 回复简洁，控制在200字以内
- 每次只问1-2个问题，避免让患者感到压力

## 重要提醒
- 你是AI辅助工具，不能替代专业医生的诊断
- 对于严重或不确定的情况，建议患者线下就医
- 遇到紧急情况（如严重过敏反应），立即建议就医或拨打急救电话
- 不提供确定性诊断，只提供参考建议"""


class DermatologyReActAgent(ReActAgent):
    """皮肤科 ReAct 智能体"""
    
    def get_system_prompt(self) -> str:
        return DERMATOLOGY_SYSTEM_PROMPT
    
    def get_tools(self) -> List[str]:
        return [
            "search_medical_knowledge",
            "analyze_skin_image",
            "assess_risk",
            "search_medication",
            "generate_medical_dossier"
        ]
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "actions": ["conversation", "analyze_skin", "interpret_report"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
            "ui_components": ["TextBubble", "SkinAnalysisCard", "DiagnosisCard", "MedicationCard"],
            "description": "专业皮肤科问诊和图像分析（ReAct版本）",
            "version": "2.0-react"
        }


def create_dermatology_react_state(session_id: str, user_id: int) -> Dict[str, Any]:
    """创建皮肤科 ReAct 智能体初始状态"""
    state = create_react_initial_state(session_id, user_id, "dermatology_react")
    
    # 皮肤科特有的上下文字段
    state["medical_context"].update({
        "lesion_type": "",  # 皮损类型
        "lesion_color": "",  # 颜色
        "lesion_distribution": "",  # 分布特点
        "itching_level": "",  # 瘙痒程度
        "skin_history": [],  # 皮肤病史
    })
    
    return state
