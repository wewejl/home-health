"""
ReAct Agent 工具集

提供给智能体调用的工具函数
"""
from .knowledge import search_medical_knowledge, KNOWLEDGE_TOOL_SCHEMA
from .risk import assess_risk, RISK_TOOL_SCHEMA
from .image import analyze_skin_image, IMAGE_TOOL_SCHEMA
from .dossier import generate_medical_dossier, DOSSIER_TOOL_SCHEMA
from .medication import search_medication, MEDICATION_TOOL_SCHEMA
from .crag import corrective_rag_search, CORRECTIVE_RAG_TOOL_SCHEMA

# 所有工具的 schema（用于 Function Calling）
ALL_TOOL_SCHEMAS = [
    KNOWLEDGE_TOOL_SCHEMA,
    RISK_TOOL_SCHEMA,
    IMAGE_TOOL_SCHEMA,
    DOSSIER_TOOL_SCHEMA,
    MEDICATION_TOOL_SCHEMA,
    CORRECTIVE_RAG_TOOL_SCHEMA,  # 新增 CRAG 工具
]

# 工具名称到函数的映射
TOOL_REGISTRY = {
    "search_medical_knowledge": search_medical_knowledge,
    "assess_risk": assess_risk,
    "analyze_skin_image": analyze_skin_image,
    "generate_medical_dossier": generate_medical_dossier,
    "search_medication": search_medication,
    "corrective_rag_search": corrective_rag_search,  # 新增 CRAG 工具
}

# 并行工具导入
from .parallel import execute_tools_parallel, parallel_medical_search, get_parallel_executor

__all__ = [
    # 基础工具
    "search_medical_knowledge",
    "assess_risk",
    "analyze_skin_image",
    "generate_medical_dossier",
    "search_medication",
    # CRAG 工具
    "corrective_rag_search",
    # 并行执行
    "execute_tools_parallel",
    "parallel_medical_search",
    "get_parallel_executor",
    # Schema 和注册表
    "ALL_TOOL_SCHEMAS",
    "TOOL_REGISTRY",
]
