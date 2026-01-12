"""
LLM 工厂 - 提供共享的 LLM 创建函数
"""
import os
from openai import OpenAI
from functools import lru_cache


@lru_cache(maxsize=1)
def get_qwen_client() -> OpenAI:
    """获取 Qwen 客户端（单例模式）"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable is not set")
    
    return OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )


def create_llm(
    model: str = "qwen-plus",
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> dict:
    """
    创建 LLM 配置
    
    Args:
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大输出 token 数
        
    Returns:
        LLM 配置字典
    """
    return {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "client": get_qwen_client()
    }
