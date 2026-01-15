"""
LLM Provider 单例模块 - 提供 LangChain ChatOpenAI 实例复用
"""
from typing import Optional
from langchain_openai import ChatOpenAI
from ..config import get_settings


class LLMProvider:
    """LLM 提供者（单例模式）- 复用 LLM 实例以提高性能"""
    
    _llm: Optional[ChatOpenAI] = None
    _multimodal_llm: Optional[ChatOpenAI] = None
    
    @classmethod
    def get_llm(cls) -> ChatOpenAI:
        """
        获取普通文本 LLM 实例
        
        使用 DashScope 兼容的 OpenAI 接口
        """
        if cls._llm is None:
            settings = get_settings()
            cls._llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                timeout=settings.LLM_TIMEOUT,
                max_retries=settings.LLM_MAX_RETRIES,
            )
        return cls._llm
    
    @classmethod
    def get_multimodal_llm(cls) -> ChatOpenAI:
        """
        获取多模态 LLM 实例（支持图片分析）
        
        使用 Qwen-VL 模型
        """
        if cls._multimodal_llm is None:
            settings = get_settings()
            cls._multimodal_llm = ChatOpenAI(
                model=settings.QWEN_VL_MODEL,
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_VL_MAX_TOKENS,
                timeout=60,  # 图片分析需要更长时间
                max_retries=settings.LLM_MAX_RETRIES,
            )
        return cls._multimodal_llm
    
    @classmethod
    def reset(cls):
        """重置 LLM 实例（用于测试或配置变更）"""
        cls._llm = None
        cls._multimodal_llm = None
