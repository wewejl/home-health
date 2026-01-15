"""
心血管内科智能体模块
"""
from .cardio_wrapper import CardioAgentWrapper

# 延迟导入 CrewAI 组件，避免启动时初始化
# from .cardio_agent import CardioAgent, CardioTaskType, create_cardio_initial_state

__all__ = ["CardioAgentWrapper"]
