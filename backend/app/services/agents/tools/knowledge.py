"""
医学知识查询工具

查询医学知识库，返回相关的疾病、症状、治疗方法等信息
"""
from typing import Dict, Any

# 工具 Schema（用于 Function Calling）
KNOWLEDGE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_medical_knowledge",
        "description": "查询医学知识库，获取疾病、症状、治疗方法等专业医学信息。当需要了解某种疾病的典型症状、诊断标准、治疗方案时使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "查询内容，例如：'湿疹的典型症状和治疗方法'、'银屑病与湿疹的区别'"
                },
                "specialty": {
                    "type": "string",
                    "enum": ["dermatology", "cardiology", "orthopedics", "general"],
                    "description": "科室类型，用于限定查询范围",
                    "default": "general"
                }
            },
            "required": ["query"]
        }
    }
}

# 内置的医学知识库（简化版，实际应接入专业知识库或RAG系统）
DERMATOLOGY_KNOWLEDGE = {
    "湿疹": {
        "definition": "湿疹是一种常见的过敏性皮肤病，以皮疹多形性、对称分布、剧烈瘙痒、反复发作为特征。",
        "symptoms": ["红斑", "丘疹", "水疱", "渗出", "结痂", "剧烈瘙痒", "皮肤干燥"],
        "causes": ["遗传因素", "免疫异常", "环境刺激", "过敏原接触", "精神压力"],
        "diagnosis": "根据皮疹形态、分布特点、病史及瘙痒程度综合判断。必要时可做斑贴试验或过敏原检测。",
        "treatment": ["外用糖皮质激素", "保湿剂", "抗组胺药", "避免诱因", "严重时短期口服激素"],
        "warning_signs": ["大面积皮损", "继发感染", "影响日常生活"]
    },
    "银屑病": {
        "definition": "银屑病（牛皮癣）是一种慢性炎症性皮肤病，典型表现为红色斑块上覆盖银白色鳞屑。",
        "symptoms": ["红色斑块", "银白色鳞屑", "点状出血", "瘙痒", "指甲改变"],
        "causes": ["遗传因素", "免疫异常", "感染", "精神压力", "药物诱发"],
        "diagnosis": "典型皮损特征：蜡滴现象、薄膜现象、点状出血。必要时可做皮肤活检。",
        "treatment": ["外用维A酸类", "糖皮质激素", "维生素D3衍生物", "光疗", "生物制剂"],
        "warning_signs": ["关节疼痛", "指甲严重受损", "大面积皮损"]
    },
    "接触性皮炎": {
        "definition": "接触性皮炎是皮肤接触某些物质后发生的急性或慢性炎症反应。",
        "symptoms": ["红斑", "水肿", "水疱", "瘙痒", "灼热感", "边界清楚"],
        "causes": ["化学物质", "金属（镍）", "化妆品", "植物", "药物"],
        "diagnosis": "明确的接触史，皮损局限于接触部位，斑贴试验可帮助确定过敏原。",
        "treatment": ["去除接触物", "外用激素", "湿敷", "抗组胺药", "严重时口服激素"],
        "warning_signs": ["全身症状", "大面积水疱", "继发感染"]
    },
    "荨麻疹": {
        "definition": "荨麻疹是由于皮肤黏膜小血管扩张及渗透性增加而出现的一种局限性水肿反应。",
        "symptoms": ["风团", "瘙痒", "皮疹此起彼伏", "消退后不留痕迹"],
        "causes": ["食物过敏", "药物过敏", "感染", "物理因素", "自身免疫"],
        "diagnosis": "典型风团表现，详细询问病史寻找诱因，必要时做过敏原检测。",
        "treatment": ["抗组胺药", "避免诱因", "急性发作时可用激素", "慢性者需长期治疗"],
        "warning_signs": ["喉头水肿", "呼吸困难", "腹痛", "低血压"]
    },
    "痤疮": {
        "definition": "痤疮是毛囊皮脂腺的慢性炎症性疾病，好发于青春期。",
        "symptoms": ["粉刺", "丘疹", "脓疱", "结节", "囊肿", "瘢痕"],
        "causes": ["雄激素水平升高", "皮脂分泌过多", "毛囊角化异常", "痤疮丙酸杆菌"],
        "diagnosis": "根据皮损类型和分布特点诊断，注意与毛囊炎、酒糟鼻鉴别。",
        "treatment": ["外用维A酸", "过氧化苯甲酰", "抗生素", "口服异维A酸（重症）"],
        "warning_signs": ["囊肿性痤疮", "严重瘢痕", "心理影响"]
    }
}

CARDIOLOGY_KNOWLEDGE = {
    "高血压": {
        "definition": "高血压是以体循环动脉压升高为主要特征的临床综合征。",
        "symptoms": ["头痛", "头晕", "心悸", "疲劳", "视物模糊"],
        "risk_factors": ["年龄", "肥胖", "高盐饮食", "缺乏运动", "遗传"],
        "diagnosis": "非同日三次测量血压≥140/90mmHg",
        "treatment": ["生活方式干预", "降压药物", "定期监测"],
        "warning_signs": ["剧烈头痛", "视力急剧下降", "胸痛", "呼吸困难"]
    },
    "冠心病": {
        "definition": "冠状动脉粥样硬化导致心肌缺血缺氧的心脏病。",
        "symptoms": ["胸痛", "胸闷", "气短", "心悸", "出汗"],
        "risk_factors": ["高血压", "糖尿病", "高血脂", "吸烟", "肥胖"],
        "diagnosis": "心电图、心脏超声、冠脉造影",
        "treatment": ["药物治疗", "介入治疗", "搭桥手术", "生活方式改善"],
        "warning_signs": ["持续胸痛>15分钟", "大汗淋漓", "濒死感"]
    }
}


async def search_medical_knowledge(query: str, specialty: str = "general") -> Dict[str, Any]:
    """
    查询医学知识库
    
    Args:
        query: 查询内容
        specialty: 科室类型
        
    Returns:
        {
            "found": True/False,
            "results": [...],
            "source": "internal_kb"
        }
    """
    results = []
    query_lower = query.lower()
    
    # 选择知识库
    if specialty == "dermatology":
        knowledge_base = DERMATOLOGY_KNOWLEDGE
    elif specialty == "cardiology":
        knowledge_base = CARDIOLOGY_KNOWLEDGE
    else:
        # 合并所有知识库
        knowledge_base = {**DERMATOLOGY_KNOWLEDGE, **CARDIOLOGY_KNOWLEDGE}
    
    # 简单的关键词匹配搜索
    for disease_name, disease_info in knowledge_base.items():
        # 检查疾病名称是否匹配
        if disease_name in query:
            results.append({
                "disease": disease_name,
                "info": disease_info,
                "relevance": "high"
            })
            continue
        
        # 检查症状是否匹配
        symptoms = disease_info.get("symptoms", [])
        matched_symptoms = [s for s in symptoms if s in query]
        if matched_symptoms:
            results.append({
                "disease": disease_name,
                "info": disease_info,
                "matched_symptoms": matched_symptoms,
                "relevance": "medium"
            })
    
    # 格式化结果为易读文本
    if results:
        formatted_results = []
        for r in results[:3]:  # 最多返回3个结果
            disease = r["disease"]
            info = r["info"]
            text = f"【{disease}】\n"
            text += f"定义：{info.get('definition', '无')}\n"
            text += f"典型症状：{', '.join(info.get('symptoms', []))}\n"
            text += f"诊断要点：{info.get('diagnosis', '无')}\n"
            text += f"治疗方法：{', '.join(info.get('treatment', []))}\n"
            text += f"危险信号：{', '.join(info.get('warning_signs', []))}"
            formatted_results.append(text)
        
        return {
            "found": True,
            "results": formatted_results,
            "count": len(results),
            "source": "internal_knowledge_base"
        }
    
    return {
        "found": False,
        "results": [],
        "message": f"未找到与 '{query}' 相关的医学知识",
        "source": "internal_knowledge_base"
    }
