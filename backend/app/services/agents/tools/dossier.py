"""
病历生成工具

生成结构化的医疗病历文档
"""
from typing import Dict, Any
from datetime import datetime
import uuid

# 工具 Schema
DOSSIER_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "generate_medical_dossier",
        "description": "生成结构化的医疗病历文档。当问诊完成，需要为患者生成病历记录时使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_data": {
                    "type": "object",
                    "properties": {
                        "chief_complaint": {
                            "type": "string",
                            "description": "主诉"
                        },
                        "present_illness": {
                            "type": "string", 
                            "description": "现病史"
                        },
                        "symptoms": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "症状列表"
                        },
                        "duration": {
                            "type": "string",
                            "description": "病程"
                        },
                        "physical_exam": {
                            "type": "string",
                            "description": "体格检查（如有图像分析结果）"
                        },
                        "preliminary_diagnosis": {
                            "type": "string",
                            "description": "初步诊断"
                        },
                        "differential_diagnosis": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "鉴别诊断"
                        },
                        "treatment_plan": {
                            "type": "string",
                            "description": "治疗方案"
                        },
                        "advice": {
                            "type": "string",
                            "description": "医嘱建议"
                        }
                    },
                    "description": "患者病历数据"
                }
            },
            "required": ["patient_data"]
        }
    }
}


async def generate_medical_dossier(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成医疗病历
    
    Args:
        patient_data: 患者病历数据
        
    Returns:
        {
            "dossier_id": "xxx",
            "created_at": "...",
            "content": {...},
            "formatted_text": "格式化的病历文本"
        }
    """
    dossier_id = str(uuid.uuid4())[:8]
    created_at = datetime.now().isoformat()
    
    # 构建病历内容
    content = {
        "id": dossier_id,
        "type": "outpatient_record",
        "created_at": created_at,
        "chief_complaint": patient_data.get("chief_complaint", "未记录"),
        "present_illness": patient_data.get("present_illness", "未记录"),
        "symptoms": patient_data.get("symptoms", []),
        "duration": patient_data.get("duration", "未知"),
        "physical_exam": patient_data.get("physical_exam", "AI问诊，未进行体格检查"),
        "preliminary_diagnosis": patient_data.get("preliminary_diagnosis", "待定"),
        "differential_diagnosis": patient_data.get("differential_diagnosis", []),
        "treatment_plan": patient_data.get("treatment_plan", ""),
        "advice": patient_data.get("advice", ""),
        "disclaimer": "本病历由AI辅助生成，仅供参考，不能替代专业医生诊断"
    }
    
    # 生成格式化文本
    formatted_text = _format_dossier(content)
    
    return {
        "dossier_id": dossier_id,
        "created_at": created_at,
        "content": content,
        "formatted_text": formatted_text
    }


def _format_dossier(content: Dict[str, Any]) -> str:
    """格式化病历为可读文本"""
    lines = [
        "=" * 50,
        "门诊病历（AI辅助）",
        "=" * 50,
        f"病历号：{content['id']}",
        f"记录时间：{content['created_at']}",
        "",
        "【主诉】",
        content["chief_complaint"],
        "",
        "【现病史】",
        content["present_illness"],
        "",
        "【主要症状】",
        "、".join(content["symptoms"]) if content["symptoms"] else "未记录",
        "",
        "【病程】",
        content["duration"],
        "",
        "【体格检查】",
        content["physical_exam"],
        "",
        "【初步诊断】",
        content["preliminary_diagnosis"],
    ]
    
    if content["differential_diagnosis"]:
        lines.extend([
            "",
            "【鉴别诊断】",
            "、".join(content["differential_diagnosis"])
        ])
    
    if content["treatment_plan"]:
        lines.extend([
            "",
            "【治疗方案】",
            content["treatment_plan"]
        ])
    
    if content["advice"]:
        lines.extend([
            "",
            "【医嘱】",
            content["advice"]
        ])
    
    lines.extend([
        "",
        "-" * 50,
        "⚠️ " + content["disclaimer"],
        "=" * 50
    ])
    
    return "\n".join(lines)
