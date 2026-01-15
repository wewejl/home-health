"""
皮肤科智能体模块

提供多种实现：
- DermaAgentWrapper: CrewAI 实现（旧）
- DermaLangGraphWrapper: LangGraph 状态机实现（过渡）
- DermaReActWrapper: LangGraph ReAct 实现（新）
"""
from ...config import get_settings

settings = get_settings()

# 导入 ReAct 实现
from .react_wrapper import DermaReActWrapper
from .react_state import create_react_initial_state

# 根据配置选择默认实现
if settings.USE_LANGGRAPH:
    from .derma_langgraph_wrapper import DermaLangGraphWrapper
    # 默认使用 ReAct 实现
    DermaAgentWrapper = DermaReActWrapper
    __all__ = [
        "DermaAgentWrapper",
        "DermaReActWrapper",
        "DermaLangGraphWrapper",
        "create_react_initial_state"
    ]
else:
    from .derma_wrapper import DermaAgentWrapper as CrewAIDermaWrapper
    from .derma_agent import DermaAgent, DermaTaskType, create_derma_initial_state
    # CrewAI 模式保持兼容
    DermaAgentWrapper = CrewAIDermaWrapper
    __all__ = [
        "DermaAgentWrapper",
        "DermaReActWrapper",
        "DermaAgent",
        "DermaTaskType",
        "create_derma_initial_state",
        "create_react_initial_state"
    ]
