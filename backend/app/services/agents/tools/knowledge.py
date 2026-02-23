"""
医学知识查询工具

查询向量知识库，返回相关的疾病、症状、治疗方法等信息
使用 PostgreSQL + pgvector 进行语义检索
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

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
                    "enum": ["dermatology", "cardiology", "orthopedics", "neurology",
                             "respiratory", "gastroenterology", "endocrinology",
                             "ophthalmology", "otorhinolaryngology", "stomatology",
                             "obstetrics_gynecology", "pediatrics", "general"],
                    "description": "科室类型，用于限定查询范围。可选值：dermatology(皮肤科), cardiology(心内科), orthopedics(骨科), neurology(神经科), respiratory(呼吸科), gastroenterology(消化科), endocrinology(内分泌科), ophthalmology(眼科), otorhinolaryngology(耳鼻喉科), stomatology(口腔科), obstetrics_gynecology(妇产科), pediatrics(儿科), general(全科)",
                    "default": "general"
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回结果数量，默认5条",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
}

# 科室中英文映射
SPECIALTY_MAP = {
    "dermatology": "皮肤科",
    "cardiology": "心内科",
    "orthopedics": "骨科",
    "neurology": "神经科",
    "respiratory": "呼吸科",
    "gastroenterology": "消化科",
    "endocrinology": "内分泌科",
    "ophthalmology": "眼科",
    "otorhinolaryngology": "耳鼻喉科",
    "stomatology": "口腔科",
    "obstetrics_gynecology": "妇产科",
    "pediatrics": "儿科",
    "general": "全科"
}

# 知识库服务实例（延迟初始化）
_knowledge_service = None


def get_knowledge_service():
    """获取知识库服务实例（单例）"""
    global _knowledge_service
    if _knowledge_service is None:
        try:
            from app.services.knowledge import KnowledgeService
            _knowledge_service = KnowledgeService.get_instance()
            logger.info("[KnowledgeTool] 知识库服务初始化成功")
        except ImportError as e:
            logger.warning(f"[KnowledgeTool] 无法导入知识库服务: {e}")
            _knowledge_service = False
        except Exception as e:
            logger.error(f"[KnowledgeTool] 初始化知识库服务失败: {e}")
            _knowledge_service = False
    return _knowledge_service if _knowledge_service is not False else None


def format_knowledge_result(result: Dict[str, Any]) -> str:
    """
    将知识库检索结果格式化为易读文本

    Args:
        result: 知识库检索结果

    Returns:
        格式化的文本
    """
    import json

    content = result.get("content", "")
    metadata = result.get("metadata", {})
    score = result.get("score", 0)

    # metadata 可能是 JSON 字符串，需要解析
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}

    # 提取元数据
    code = metadata.get("code", "")
    name = metadata.get("name", "")
    keywords = metadata.get("keywords", [])
    category = metadata.get("category", "")

    # 构建格式化输出
    lines = []

    # 标题行
    if name and code:
        lines.append(f"【{name}（{code}）】")
    elif name:
        lines.append(f"【{name}】")
    elif content:
        lines.append(f"【相关医学知识】")

    # 内容
    lines.append(content)

    # 关键词
    if keywords:
        lines.append(f"关键词：{', '.join(keywords)}")

    # 相似度分数（调试用）
    if score > 0:
        lines.append(f"(相关度: {score:.2%})")

    return "\n".join(lines)


async def search_medical_knowledge(
    query: str,
    specialty: str = "general",
    top_k: int = 5
) -> Dict[str, Any]:
    """
    查询医学知识库（使用向量检索）

    Args:
        query: 查询内容
        specialty: 科室类型
        top_k: 返回结果数量

    Returns:
        {
            "found": True/False,
            "results": [...],
            "count": int,
            "query_used": str,
            "specialty": str,
            "source": "vector_knowledge_base"
        }
    """
    # 获取知识库服务
    kb_service = get_knowledge_service()

    if kb_service is None:
        # 知识库服务不可用，返回空结果
        return {
            "found": False,
            "results": [],
            "count": 0,
            "query_used": query,
            "specialty": specialty,
            "source": "vector_knowledge_base",
            "error": "知识库服务不可用"
        }

    try:
        # 确保知识库已初始化
        if not kb_service._initialized:
            await kb_service.initialize()

        # 执行向量检索
        search_result = await kb_service.search(
            query=query,
            specialty=specialty,
            top_k=top_k
        )

        found = search_result.get("found", False)
        raw_results = search_result.get("results", [])

        # 格式化结果
        formatted_results = []
        for result in raw_results:
            formatted_results.append(format_knowledge_result(result))

        return {
            "found": found,
            "results": formatted_results,
            "raw_results": raw_results,  # 保留原始结果供进一步处理
            "count": len(formatted_results),
            "query_used": search_result.get("query_used", query),
            "specialty": specialty,
            "specialty_name": SPECIALTY_MAP.get(specialty, specialty),
            "source": "vector_knowledge_base"
        }

    except Exception as e:
        logger.error(f"[KnowledgeTool] 检索失败: {e}")
        return {
            "found": False,
            "results": [],
            "count": 0,
            "query_used": query,
            "specialty": specialty,
            "source": "vector_knowledge_base",
            "error": str(e)
        }


# ========== 后备方案：内置知识库 ==========
# 当向量知识库不可用时使用

FALLBACK_DERMATOLOGY_KNOWLEDGE = {
    "湿疹": {
        "definition": "湿疹是一种常见的过敏性皮肤病，以皮疹多形性、对称分布、剧烈瘙痒、反复发作为特征。",
        "symptoms": ["红斑", "丘疹", "水疱", "渗出", "结痂", "剧烈瘙痒", "皮肤干燥"],
        "diagnosis": "根据皮疹形态、分布特点、病史及瘙痒程度综合判断。",
        "treatment": ["外用糖皮质激素", "保湿剂", "抗组胺药", "避免诱因"],
        "warning_signs": ["大面积皮损", "继发感染", "影响日常生活"]
    },
    "荨麻疹": {
        "definition": "荨麻疹是由于皮肤黏膜小血管扩张及渗透性增加而出现的局限性水肿反应。",
        "symptoms": ["风团", "瘙痒", "皮疹此起彼伏", "消退后不留痕迹"],
        "diagnosis": "典型风团表现，详细询问病史寻找诱因。",
        "treatment": ["抗组胺药", "避免诱因", "急性发作时可用激素"],
        "warning_signs": ["喉头水肿", "呼吸困难", "腹痛", "低血压"]
    }
}

FALLBACK_CARDIOLOGY_KNOWLEDGE = {
    "高血压": {
        "definition": "高血压是以体循环动脉压升高为主要特征的临床综合征。",
        "symptoms": ["头痛", "头晕", "心悸", "疲劳", "视物模糊"],
        "diagnosis": "非同日三次测量血压≥140/90mmHg",
        "treatment": ["生活方式干预", "降压药物", "定期监测"],
        "warning_signs": ["剧烈头痛", "视力急剧下降", "胸痛", "呼吸困难"]
    }
}


async def search_medical_knowledge_fallback(
    query: str,
    specialty: str = "general"
) -> Dict[str, Any]:
    """
    后备方案：使用内置知识库（当向量知识库不可用时）

    Args:
        query: 查询内容
        specialty: 科室类型

    Returns:
        查询结果
    """
    results = []
    query_lower = query.lower()

    # 选择知识库
    if specialty == "dermatology":
        knowledge_base = FALLBACK_DERMATOLOGY_KNOWLEDGE
    elif specialty == "cardiology":
        knowledge_base = FALLBACK_CARDIOLOGY_KNOWLEDGE
    else:
        knowledge_base = {**FALLBACK_DERMATOLOGY_KNOWLEDGE, **FALLBACK_CARDIOLOGY_KNOWLEDGE}

    # 关键词匹配
    for disease_name, disease_info in knowledge_base.items():
        if disease_name in query:
            text = f"【{disease_name}】\n"
            text += f"定义：{disease_info.get('definition', '无')}\n"
            text += f"典型症状：{', '.join(disease_info.get('symptoms', []))}\n"
            text += f"诊断要点：{disease_info.get('diagnosis', '无')}\n"
            text += f"治疗方法：{', '.join(disease_info.get('treatment', []))}\n"
            text += f"危险信号：{', '.join(disease_info.get('warning_signs', []))}"
            results.append(text)

    return {
        "found": len(results) > 0,
        "results": results,
        "count": len(results),
        "query_used": query,
        "specialty": specialty,
        "source": "fallback_knowledge_base",
        "note": "使用内置知识库（向量知识库不可用）"
    }
