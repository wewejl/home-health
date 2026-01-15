"""
骨科智能体模块
支持：骨科症状问诊、X光片解读
"""
from .ortho_wrapper import OrthoAgentWrapper

# 延迟导入 CrewAI 组件，避免启动时初始化
# from .ortho_agent import OrthoAgent, OrthoTaskType, create_ortho_initial_state
# from .ortho_crew_service import OrthoCrewService, ortho_crew_service

__all__ = ["OrthoAgentWrapper"]
