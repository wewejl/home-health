"""
基础模块 - 提供 BaseAgent 接口和共享 LLM 工具
"""
from .base_agent import BaseAgent
from .llm_factory import create_llm, get_qwen_client

__all__ = ["BaseAgent", "create_llm", "get_qwen_client"]
