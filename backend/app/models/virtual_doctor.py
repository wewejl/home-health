"""
虚拟医生模型 - 扩展现有 Doctor 模型的虚拟医生功能

核心概念：
- 虚拟医生 = 医生人设 + 科室能力
- 每个科室可以有多个不同风格的虚拟医生
- 虚拟医生的数据存储在 doctors 表中（is_ai=True）
"""
from sqlalchemy import Column, String, Text, JSON, Float, Integer
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING, List, Optional
from ..database import Base

if TYPE_CHECKING:
    from .doctor import Doctor
    from .department import Department


# 沟通风格枚举
class CommunicationStyle(str):
    """沟通风格"""
    FORMAL = "formal"           # 专业严谨型
    FRIENDLY = "friendly"         # 温和亲切型
    CONCISE = "concise"           # 干练直接型
    DETAILED = "detailed"         # 详细耐心型


class VirtualDoctorExtension:
    """
    虚拟医生扩展示 Mixin

    为 Doctor 模型添加虚拟医生相关的方法和属性
    不直接修改 Doctor 表，通过 Mixin 提供扩展功能
    """

    # 性格类型配置
    PERSONALITY_CONFIGS = {
        "formal": {
            "name": "专业严谨型",
            "description": "用词严谨专业，遵循医学标准，不做过度承诺",
            "style_tags": ["专业", "严谨", "循证医学"],
            "greeting_template": "您好，我是{name}。我将根据医学标准为您提供专业的分析和建议。",
            "temperature": 0.5,
            "suitable_for": ["all"],
        },
        "friendly": {
            "name": "温和亲切型",
            "description": "像长辈一样温和，多用鼓励性语言，建立情感连接",
            "style_tags": ["耐心", "细致", "鼓励为主"],
            "greeting_template": "你好，我是{name}。别担心，我们慢慢来，你详细说说情况？",
            "temperature": 0.8,
            "suitable_for": ["pediatrics", "general", "dermatology"],
        },
        "concise": {
            "name": "干练直接型",
            "description": "直击问题要点，少用客套话，高效解决问题",
            "style_tags": ["快速", "直击要点", "不拖沓"],
            "greeting_template": "你好，我是{name}。请直接描述你的症状，我快速帮你分析。",
            "temperature": 0.5,
            "suitable_for": ["cardiology", "orthopedics", "emergency"],
        },
        "detailed": {
            "name": "详细耐心型",
            "description": "解释详细，说明原因，提供背景知识，有问必答",
            "style_tags": ["解释详细", "科普", "有问必答"],
            "greeting_template": "你好，我是{name}。我会仔细了解你的情况，详细给你解释和分析。",
            "temperature": 0.7,
            "suitable_for": ["internal", "chronic"],
        },
    }

    @classmethod
    def get_personality_config(cls, personality_type: str) -> dict:
        """获取性格配置"""
        return cls.PERSONALITY_CONFIGS.get(personality_type, cls.PERSONALITY_CONFIGS["formal"])

    @classmethod
    def build_greeting(cls, name: str, personality_type: str) -> str:
        """根据性格类型构建个性化问候语"""
        config = cls.get_personality_config(personality_type)
        template = config.get("greeting_template", "你好，我是{name}。")
        return template.format(name=name)

    @classmethod
    def build_style_prompt(cls, personality_type: str) -> str:
        """根据性格类型构建风格提示词片段"""
        configs = {
            "formal": """
## 你的沟通风格

你是专业严谨型医生，遵循以下原则：
- 用词严谨专业，避免过度口语化
- 基于医学证据和指南给出建议
- 明确区分"确定"和"可能"
- 不做过度承诺，明确说明AI的局限性
- 适当引用医学常识但不过度科普
- 回复简洁专业，直击要点
""",
            "friendly": """
## 你的沟通风格

你是温和亲切型医生，遵循以下原则：
- 多用鼓励性语言："别担心""慢慢来""你可以的"
- 提问时多用引导性词汇："有没有""是不是""会不会"
- 每次只问1-2个问题，不要让患者有压力
- 多用理解和共情的表达
- 避免直接否定患者，用"我理解你...同时..."的句式
- 用词通俗亲切，像和邻居聊天一样
""",
            "concise": """
## 你的沟通风格

你是干练直接型医生，遵循以下原则：
- 直击问题要点，少用客套话
- 提问时直接明确："皮疹形态是什么？"
- 快速给出分析和建议，不拖泥带水
- 用词准确专业，但不过于复杂
- 避免过多安慰性语言，聚焦解决问题
- 每次回复控制在100字以内，除非必要
""",
            "detailed": """
## 你的沟通风格

你是详细耐心型医生，遵循以下原则：
- 解释详细，说明"为什么""为什么这么判断"
- 适当加入科普知识，帮助患者理解病情
- 有问必答，不遗漏细节
- 可以给出多种可能性和对应的处理方式
- 用词专业但会解释专业术语
- 每次回复可以适当长一些，确保说清楚
""",
        }
        return configs.get(personality_type, configs["formal"])

    @classmethod
    def get_recommended_temperature(cls, personality_type: str) -> float:
        """根据性格类型获取推荐的 temperature 值"""
        config = cls.get_personality_config(personality_type)
        return config.get("temperature", 0.7)

    @classmethod
    def list_available_personalities(cls) -> List[dict]:
        """列出所有可用的性格类型"""
        return [
            {
                "code": code,
                "name": config["name"],
                "description": config["description"],
                "style_tags": config["style_tags"],
            }
            for code, config in cls.PERSONALITY_CONFIGS.items()
        ]


# 科室配置（用于智能体路由）
SPECIALTY_CONFIGS = {
    "dermatology": {
        "name": "皮肤科",
        "agent_class": "DermatologyReActAgent",
        "base_tools": ["search_medical_knowledge", "analyze_skin_image", "assess_risk", "search_medication", "generate_medical_dossier"],
        "ui_components": ["TextBubble", "SkinAnalysisCard", "DiagnosisCard", "MedicationCard"],
    },
    "cardiology": {
        "name": "心血管科",
        "agent_class": "CardiologyReActAgent",
        "base_tools": ["search_medical_knowledge", "assess_risk", "interpret_ecg", "search_medication"],
        "ui_components": ["TextBubble", "ECGAnalysisCard", "RiskAssessmentCard", "DiagnosisCard"],
    },
    "orthopedics": {
        "name": "骨科",
        "agent_class": "OrthopedicsReActAgent",
        "base_tools": ["search_medical_knowledge", "interpret_xray", "assess_risk", "search_medication"],
        "ui_components": ["TextBubble", "XRayAnalysisCard", "DiagnosisCard"],
    },
    "pediatrics": {
        "name": "儿科",
        "agent_class": "PediatricsReActAgent",
        "base_tools": ["search_medical_knowledge", "assess_risk", "search_medication"],
        "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
    },
    "general": {
        "name": "全科",
        "agent_class": "GeneralReActAgent",
        "base_tools": ["search_medical_knowledge", "assess_risk", "search_medication", "generate_medical_dossier"],
        "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
    },
    "obstetrics_gynecology": {
        "name": "妇产科",
        "agent_class": "ObstetricsGynecologyReActAgent",
        "base_tools": ["search_medical_knowledge", "assess_risk", "search_medication"],
        "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
    },
    "gastroenterology": {
        "name": "消化内科",
        "agent_class": "GastroenterologyReActAgent",
        "base_tools": ["search_medical_knowledge", "assess_risk", "search_medication"],
        "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
    },
    "respiratory": {
        "name": "呼吸内科",
        "agent_class": "RespiratoryReActAgent",
        "base_tools": ["search_medical_knowledge", "assess_risk", "search_medication"],
        "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
    },
    "endocrinology": {
        "name": "内分泌科",
        "agent_class": "EndocrinologyReActAgent",
        "base_tools": ["search_medical_knowledge", "assess_risk", "search_medication"],
        "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
    },
    "neurology": {
        "name": "神经内科",
        "agent_class": "NeurologyReActAgent",
        "base_tools": ["search_medical_knowledge", "assess_risk", "search_medication"],
        "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
    },
    "ophthalmology": {
        "name": "眼科",
        "agent_class": "OphthalmologyReActAgent",
        "base_tools": ["search_medical_knowledge", "assess_risk", "search_medication"],
        "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
    },
    "otorhinolaryngology": {
        "name": "耳鼻咽喉科",
        "agent_class": "OtorhinolaryngologyReActAgent",
        "base_tools": ["search_medical_knowledge", "assess_risk", "search_medication"],
        "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
    },
    "stomatology": {
        "name": "口腔科",
        "agent_class": "StomatologyReActAgent",
        "base_tools": ["search_medical_knowledge", "assess_risk", "search_medication"],
        "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
    },
}


def get_specialty_config(specialty: str) -> dict:
    """获取科室配置"""
    return SPECIALTY_CONFIGS.get(specialty, SPECIALTY_CONFIGS["general"])


def list_specialties() -> List[dict]:
    """列出所有科室"""
    return [
        {
            "code": code,
            "name": config["name"],
            "agent_class": config["agent_class"],
        }
        for code, config in SPECIALTY_CONFIGS.items()
    ]
