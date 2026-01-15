from .auth_service import AuthService
from .qwen_service import QwenService
from .admin_auth_service import AdminAuthService
from .knowledge_service import KnowledgeService
from .qwen_vl_service import QwenVLService, qwen_vl_service
from .agent_router import AgentRouter, initialize_agents

# 模块化智能体导出（仅导出 Wrapper，避免启动时加载 CrewAI）
from .dermatology import DermaAgentWrapper
from .cardiology import CardioAgentWrapper
from .orthopedics import OrthoAgentWrapper
from .general import GeneralAgent

__all__ = [
    # 基础服务
    "AuthService", "QwenService", "AdminAuthService", "KnowledgeService",
    "QwenVLService", "qwen_vl_service",
    # 智能体路由
    "AgentRouter", "initialize_agents",
    # 科室智能体（仅 Wrapper）
    "DermaAgentWrapper",
    "CardioAgentWrapper",
    "OrthoAgentWrapper",
    "GeneralAgent",
]
