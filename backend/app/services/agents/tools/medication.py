"""
药物查询工具

查询疾病的推荐用药和注意事项
"""
from typing import Dict, Any, List

# 工具 Schema
MEDICATION_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_medication",
        "description": "查询疾病的推荐用药、用法用量和注意事项。当需要为患者提供用药建议时使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "condition": {
                    "type": "string",
                    "description": "疾病或症状名称，例如：'湿疹'、'荨麻疹'"
                },
                "contraindications": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "禁忌症列表，如过敏药物、慢性病等"
                },
                "severity": {
                    "type": "string",
                    "enum": ["mild", "moderate", "severe"],
                    "description": "病情严重程度"
                }
            },
            "required": ["condition"]
        }
    }
}

# 药物数据库（简化版）
MEDICATION_DATABASE = {
    "湿疹": {
        "mild": {
            "topical": [
                {
                    "name": "炉甘石洗剂",
                    "usage": "外用，每日2-3次涂抹患处",
                    "effect": "止痒、收敛",
                    "warnings": ["避免用于破损皮肤"]
                },
                {
                    "name": "保湿霜（如凡士林）",
                    "usage": "每日多次涂抹，保持皮肤湿润",
                    "effect": "修复皮肤屏障",
                    "warnings": []
                }
            ],
            "oral": [
                {
                    "name": "氯雷他定",
                    "usage": "每日一次，每次10mg",
                    "effect": "抗过敏、止痒",
                    "warnings": ["驾驶时慎用"]
                }
            ]
        },
        "moderate": {
            "topical": [
                {
                    "name": "丁酸氢化可的松乳膏",
                    "usage": "每日1-2次涂抹患处，疗程不超过2周",
                    "effect": "中效激素，抗炎止痒",
                    "warnings": ["不宜长期使用", "面部慎用"]
                },
                {
                    "name": "他克莫司软膏",
                    "usage": "每日2次涂抹患处",
                    "effect": "非激素抗炎",
                    "warnings": ["可能有烧灼感", "避免日晒"]
                }
            ],
            "oral": [
                {
                    "name": "西替利嗪",
                    "usage": "每日一次，每次10mg",
                    "effect": "抗过敏",
                    "warnings": ["可能嗜睡"]
                }
            ]
        },
        "severe": {
            "topical": [
                {
                    "name": "糠酸莫米松乳膏",
                    "usage": "每日一次涂抹患处，疗程遵医嘱",
                    "effect": "强效激素",
                    "warnings": ["必须在医生指导下使用", "严格控制疗程"]
                }
            ],
            "oral": [
                {
                    "name": "泼尼松（需处方）",
                    "usage": "遵医嘱",
                    "effect": "系统性抗炎",
                    "warnings": ["必须在医生指导下使用", "不能自行停药"]
                }
            ],
            "note": "严重湿疹建议线下就医，在医生指导下用药"
        }
    },
    "荨麻疹": {
        "mild": {
            "oral": [
                {
                    "name": "氯雷他定",
                    "usage": "每日一次，每次10mg",
                    "effect": "抗组胺",
                    "warnings": []
                }
            ]
        },
        "moderate": {
            "oral": [
                {
                    "name": "氯雷他定 + 西替利嗪",
                    "usage": "氯雷他定早上，西替利嗪晚上",
                    "effect": "联合抗组胺",
                    "warnings": ["西替利嗪可能嗜睡"]
                }
            ]
        },
        "severe": {
            "oral": [
                {
                    "name": "地塞米松（需处方）",
                    "usage": "遵医嘱",
                    "effect": "快速抗过敏",
                    "warnings": ["仅用于急性发作", "需医生指导"]
                }
            ],
            "note": "如出现呼吸困难、喉头水肿，立即就医！"
        }
    },
    "痤疮": {
        "mild": {
            "topical": [
                {
                    "name": "过氧化苯甲酰凝胶",
                    "usage": "每晚一次涂抹患处",
                    "effect": "杀菌、去角质",
                    "warnings": ["可能刺激皮肤", "避免接触衣物"]
                },
                {
                    "name": "阿达帕林凝胶",
                    "usage": "每晚一次涂抹",
                    "effect": "维A酸类，疏通毛孔",
                    "warnings": ["孕妇禁用", "需避光", "起初可能加重"]
                }
            ]
        },
        "moderate": {
            "topical": [
                {
                    "name": "克林霉素凝胶",
                    "usage": "每日2次涂抹",
                    "effect": "抗菌消炎",
                    "warnings": ["不宜长期使用"]
                }
            ],
            "oral": [
                {
                    "name": "多西环素（需处方）",
                    "usage": "遵医嘱",
                    "effect": "口服抗生素",
                    "warnings": ["需处方", "避免日晒"]
                }
            ]
        },
        "severe": {
            "note": "严重痤疮（囊肿性）需皮肤科就诊，可能需要异维A酸治疗"
        }
    }
}


async def search_medication(
    condition: str,
    contraindications: List[str] = None,
    severity: str = "mild"
) -> Dict[str, Any]:
    """
    查询推荐用药
    
    Args:
        condition: 疾病名称
        contraindications: 禁忌症列表
        severity: 严重程度
        
    Returns:
        {
            "found": True/False,
            "condition": "疾病",
            "severity": "严重程度",
            "medications": {...},
            "warnings": [...],
            "disclaimer": "免责声明"
        }
    """
    contraindications = contraindications or []
    
    # 查找疾病
    disease_meds = None
    matched_condition = None
    
    for disease_name, meds in MEDICATION_DATABASE.items():
        if disease_name in condition or condition in disease_name:
            disease_meds = meds
            matched_condition = disease_name
            break
    
    if not disease_meds:
        return {
            "found": False,
            "condition": condition,
            "message": f"未找到 '{condition}' 的用药信息，建议咨询医生",
            "disclaimer": "用药请遵医嘱"
        }
    
    # 获取对应严重程度的用药
    severity_meds = disease_meds.get(severity, disease_meds.get("mild", {}))
    
    # 过滤禁忌药物
    filtered_meds = {
        "topical": [],
        "oral": []
    }
    warnings = []
    
    for med_type in ["topical", "oral"]:
        for med in severity_meds.get(med_type, []):
            # 检查是否在禁忌列表中
            is_contraindicated = False
            for contra in contraindications:
                if contra.lower() in med["name"].lower():
                    is_contraindicated = True
                    warnings.append(f"因禁忌症排除：{med['name']}")
                    break
            
            if not is_contraindicated:
                filtered_meds[med_type].append(med)
    
    # 特别提示
    if severity_meds.get("note"):
        warnings.append(severity_meds["note"])
    
    return {
        "found": True,
        "condition": matched_condition,
        "severity": severity,
        "medications": filtered_meds,
        "general_advice": [
            "用药前请仔细阅读说明书",
            "如有不适立即停药并就医",
            "处方药需在医生指导下使用"
        ],
        "warnings": warnings,
        "disclaimer": "以上用药建议仅供参考，具体用药请遵医嘱。AI不能替代专业医生的诊断和处方。"
    }
