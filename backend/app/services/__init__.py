from .auth_service import AuthService
from .qwen_service import QwenService
from .admin_auth_service import AdminAuthService
from .knowledge_service import KnowledgeService
from .qwen_vl_service import QwenVLService, qwen_vl_service
from .agent_router import AgentRouter, initialize_agents

# 模块化智能体导出
from .dermatology import DermaAgentWrapper, DermaAgent, DermaTaskType, create_derma_initial_state
from .cardiology import CardioAgentWrapper, CardioAgent, CardioTaskType, create_cardio_initial_state
from .orthopedics import OrthoAgentWrapper, OrthoAgent, OrthoTaskType, create_ortho_initial_state
from .general import GeneralAgent

__all__ = [
    # 基础服务
    "AuthService", "QwenService", "AdminAuthService", "KnowledgeService",
    "QwenVLService", "qwen_vl_service",
    # 智能体路由
    "AgentRouter", "initialize_agents",
    # 皮肤科
    "DermaAgentWrapper", "DermaAgent", "DermaTaskType", "create_derma_initial_state",
    # 心血管内科
    "CardioAgentWrapper", "CardioAgent", "CardioTaskType", "create_cardio_initial_state",
    # 骨科
    "OrthoAgentWrapper", "OrthoAgent", "OrthoTaskType", "create_ortho_initial_state",
    # 通用
    "GeneralAgent",
]
