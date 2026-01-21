"""
统一智能体模块

基于 LangGraph 构建的多科室智能体系统
使用 ReAct 架构实现 AI 自主决策
"""
from .react_base import (
    ReActAgent,
    ReActAgentState,
    create_react_initial_state,
    create_initial_state,  # 别名
    LangGraphAgent,  # 别名
    AgentState,  # 别名
)
from .router import AgentRouter

__all__ = [
    # ReAct Agent（主架构）
    "ReActAgent",
    "ReActAgentState",
    "create_react_initial_state",
    # 兼容性别名
    "LangGraphAgent",
    "AgentState",
    "create_initial_state",
    # 路由器
    "AgentRouter",
]
