"""
Embedding 服务实现
"""
from .mock_embedding import MockEmbedding
from .openai_embedding import OpenAIEmbedding
from .qwen_embedding import QwenEmbedding

__all__ = ["MockEmbedding", "OpenAIEmbedding", "QwenEmbedding"]
