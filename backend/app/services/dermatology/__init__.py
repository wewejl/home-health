"""
皮肤科智能体模块

支持通过配置切换 CrewAI 和 LangGraph 实现
"""
from ...config import get_settings

settings = get_settings()

# 根据配置选择实现
if settings.USE_LANGGRAPH:
    from .derma_langgraph_wrapper import DermaLangGraphWrapper as DermaAgentWrapper
    # LangGraph 模式下不导入 CrewAI 组件，避免启动时初始化
    __all__ = ["DermaAgentWrapper"]
else:
    from .derma_wrapper import DermaAgentWrapper
    # CrewAI 模式下才导入相关组件
    from .derma_agent import DermaAgent, DermaTaskType, create_derma_initial_state
    __all__ = ["DermaAgentWrapper", "DermaAgent", "DermaTaskType", "create_derma_initial_state"]
