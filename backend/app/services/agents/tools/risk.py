"""
风险评估工具

根据症状和患者信息评估疾病风险等级
"""
from typing import Dict, Any, List

# 工具 Schema
RISK_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "assess_risk",
        "description": "根据患者症状和基本信息评估疾病风险等级。用于判断病情严重程度和是否需要紧急就医。",
        "parameters": {
            "type": "object",
            "properties": {
                "symptoms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "症状列表，例如：['胸痛', '呼吸困难', '出汗']"
                },
                "patient_info": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer", "description": "年龄"},
                        "gender": {"type": "string", "description": "性别"},
                        "chronic_conditions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "慢性病史"
                        },
                        "allergies": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "过敏史"
                        }
                    },
                    "description": "患者基本信息"
                },
                "specialty": {
                    "type": "string",
                    "enum": ["dermatology", "cardiology", "orthopedics", "general"],
                    "description": "科室类型"
                }
            },
            "required": ["symptoms"]
        }
    }
}

# 危险信号（按科室分类）
EMERGENCY_SIGNS = {
    "dermatology": [
        "全身红斑", "大面积水疱", "发热伴皮疹", "口腔黏膜损害", 
        "眼部受累", "呼吸困难", "喉头水肿"
    ],
    "cardiology": [
        "持续胸痛", "剧烈胸痛", "呼吸困难", "大汗淋漓", 
        "意识模糊", "晕厥", "心悸伴晕厥"
    ],
    "orthopedics": [
        "肢体畸形", "无法活动", "剧烈疼痛", "肢体麻木",
        "皮肤苍白发凉", "开放性骨折"
    ],
    "general": [
        "高热", "意识障碍", "剧烈疼痛", "大出血", "呼吸困难"
    ]
}

# 高风险信号
HIGH_RISK_SIGNS = {
    "dermatology": [
        "皮疹快速扩散", "水疱", "糜烂", "继发感染", "影响日常生活的瘙痒"
    ],
    "cardiology": [
        "活动后胸闷", "夜间憋醒", "下肢水肿", "心悸频繁", "血压波动大"
    ],
    "orthopedics": [
        "关节肿胀", "活动受限", "夜间疼痛", "晨僵"
    ],
    "general": [
        "症状持续加重", "影响睡眠", "影响进食", "体重下降"
    ]
}


async def assess_risk(
    symptoms: List[str],
    patient_info: Dict[str, Any] = None,
    specialty: str = "general"
) -> Dict[str, Any]:
    """
    评估疾病风险等级
    
    Args:
        symptoms: 症状列表
        patient_info: 患者信息
        specialty: 科室类型
        
    Returns:
        {
            "risk_level": "low" | "medium" | "high" | "emergency",
            "score": 0-100,
            "urgent_signs": [...],
            "recommendations": [...],
            "reasoning": "评估理由"
        }
    """
    if not symptoms:
        return {
            "risk_level": "low",
            "score": 10,
            "urgent_signs": [],
            "recommendations": ["请描述您的具体症状"],
            "reasoning": "症状信息不足，无法评估"
        }
    
    patient_info = patient_info or {}
    
    # 获取对应科室的危险信号
    emergency_signs = EMERGENCY_SIGNS.get(specialty, EMERGENCY_SIGNS["general"])
    high_risk_signs = HIGH_RISK_SIGNS.get(specialty, HIGH_RISK_SIGNS["general"])
    
    # 匹配危险信号
    matched_emergency = []
    matched_high_risk = []
    
    symptoms_text = " ".join(symptoms).lower()
    
    for sign in emergency_signs:
        if sign in symptoms_text:
            matched_emergency.append(sign)
    
    for sign in high_risk_signs:
        if sign in symptoms_text:
            matched_high_risk.append(sign)
    
    # 计算风险分数
    base_score = 20
    score = base_score
    
    # 紧急信号加分
    score += len(matched_emergency) * 30
    
    # 高风险信号加分
    score += len(matched_high_risk) * 15
    
    # 症状数量加分
    score += min(len(symptoms) * 5, 20)
    
    # 年龄因素
    age = patient_info.get("age", 0)
    if age > 65 or age < 5:
        score += 10
    
    # 慢性病因素
    chronic_conditions = patient_info.get("chronic_conditions", [])
    if chronic_conditions:
        score += len(chronic_conditions) * 5
    
    # 限制分数范围
    score = min(score, 100)
    
    # 确定风险等级
    if matched_emergency or score >= 80:
        risk_level = "emergency"
        recommendations = [
            "建议立即就医或拨打急救电话",
            "不要自行用药",
            "保持冷静，记录症状变化"
        ]
    elif matched_high_risk or score >= 60:
        risk_level = "high"
        recommendations = [
            "建议尽快到医院就诊",
            "避免延误治疗",
            "密切关注症状变化"
        ]
    elif score >= 40:
        risk_level = "medium"
        recommendations = [
            "建议择期就医检查",
            "注意休息，避免诱因",
            "如症状加重请及时就医"
        ]
    else:
        risk_level = "low"
        recommendations = [
            "可先观察，注意休息",
            "保持健康生活方式",
            "如有不适可在线咨询"
        ]
    
    # 生成评估理由
    reasoning_parts = []
    if matched_emergency:
        reasoning_parts.append(f"存在紧急危险信号：{', '.join(matched_emergency)}")
    if matched_high_risk:
        reasoning_parts.append(f"存在高风险信号：{', '.join(matched_high_risk)}")
    if age > 65:
        reasoning_parts.append("老年患者需特别关注")
    if chronic_conditions:
        reasoning_parts.append(f"有慢性病史：{', '.join(chronic_conditions)}")
    if not reasoning_parts:
        reasoning_parts.append("症状相对轻微，暂无明显危险信号")
    
    return {
        "risk_level": risk_level,
        "score": score,
        "urgent_signs": matched_emergency + matched_high_risk,
        "recommendations": recommendations,
        "reasoning": "；".join(reasoning_parts)
    }
