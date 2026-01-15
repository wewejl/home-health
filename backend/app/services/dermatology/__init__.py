"""
皮肤科智能体模块

支持通过配置切换 CrewAI 和 LangGraph 实现
"""
from ...config import get_settings

settings = get_settings()

# 根据配置选择实现
if settings.USE_LANGGRAPH:
    from .derma_langgraph_wrapper import DermaLangGraphWrapper as DermaAgentWrapper
else:
    from .derma_wrapper import DermaAgentWrapper

# 保持向后兼容
from .derma_agent import DermaAgent, DermaTaskType, create_derma_initial_state

__all__ = ["DermaAgentWrapper", "DermaAgent", "DermaTaskType", "create_derma_initial_state"]
