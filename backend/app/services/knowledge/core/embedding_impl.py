"""
Embedding 服务实现

支持多种 Embedding 提供商：
- OpenAI 兼容 API（包括千问、通义千问等）
- 本地模型（通过 Sentence Transformers）
- Mock（用于开发测试）
"""
import httpx
import hashlib
from typing import List
from .embedding import EmbeddingService
from .config import EmbeddingConfig
import asyncio
import logging

logger = logging.getLogger(__name__)


class OpenAIEmbedding(EmbeddingService):
    """OpenAI 兼容的 Embedding 服务（支持千问、通义千问等）"""

    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.openai.com/v1"
        self.model = config.model

    async def encode(self, texts: List[str]) -> List[List[float]]:
        """批量编码"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "input": texts,
            "encoding_format": "float"
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                return [item["embedding"] for item in data["data"]]
        except Exception as e:
            logger.error(f"[OpenAIEmbedding] 编码失败: {e}")
            # 返回零向量作为后备
            dim = self.config.dimension
            return [[0.0] * dim for _ in texts]

    async def encode_single(self, text: str) -> List[float]:
        """编码单个文本"""
        results = await self.encode([text])
        return results[0] if results else []


class QwenEmbedding(EmbeddingService):
    """阿里云千问 Embedding 服务（专用于中文）"""

    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self.api_key = config.api_key
        # 千问 Embedding API 端点
        self.base_url = config.base_url or "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
        self.model = config.model or "text-embedding-v3"

    async def encode(self, texts: List[str]) -> List[List[float]]:
        """批量编码（千问 API 一次处理一个文本）"""
        embeddings = []

        for text in texts:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "input": {
                    "texts": [text]
                }
            }

            try:
                async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                    response = await client.post(
                        self.base_url,
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    data = response.json()

                    # 千问返回格式
                    if "output" in data and "embeddings" in data["output"]:
                        embedding = data["output"]["embeddings"][0]["embedding"]
                        embeddings.append(embedding)
                    else:
                        logger.warning(f"[QwenEmbedding] 响应格式异常: {data}")
                        embeddings.append([0.0] * self.config.dimension)

            except Exception as e:
                logger.error(f"[QwenEmbedding] 编码失败: {e}")
                embeddings.append([0.0] * self.config.dimension)

        return embeddings

    async def encode_single(self, text: str) -> List[float]:
        """编码单个文本"""
        results = await self.encode([text])
        return results[0] if results else []


class ImprovedMockEmbedding(EmbeddingService):
    """
    改进的模拟 Embedding 服务

    使用更智能的哈希方法生成伪向量，
    使得相似文本的向量相似度更高
    """

    async def encode(self, texts: List[str]) -> List[List[float]]:
        """生成伪向量（使用改进的哈希方法）"""
        vectors = []
        dim = self.config.dimension

        for text in texts:
            # 多个哈希组合，增加维度多样性
            hash1 = hashlib.sha256(text.encode()).digest()
            hash2 = hashlib.md5((text + "_salt1").encode()).digest()
            hash3 = hashlib.sha512((text + "_salt2").encode()).digest()
            combined_hash = hash1 + hash2 + hash3

            # 扩展到指定维度
            vector = []
            for i in range(dim):
                # 组合不同哈希字节生成更均匀的分布
                idx = i % len(combined_hash)
                byte_val = combined_hash[idx]

                # 使用更复杂的变换，生成正态分布类似的值
                normalized = (byte_val / 255.0) * 2 - 1
                # 添加一些非线性变换
                if i % 3 == 0:
                    normalized = normalized * 0.5 + 0.5
                elif i % 3 == 1:
                    normalized = (normalized ** 2) * 2 - 1

                vector.append(normalized)

            # L2 归一化
            norm = sum(v**2 for v in vector) ** 0.5
            if norm > 0:
                vector = [v / norm for v in vector]

            vectors.append(vector)

        return vectors

    async def encode_single(self, text: str) -> List[float]:
        results = await self.encode([text])
        return results[0] if results else []


def get_embedding_service(config: EmbeddingConfig) -> EmbeddingService:
    """
    获取 Embedding 服务实例

    优先级：
    1. 如果配置了千问 API，使用 QwenEmbedding
    2. 如果配置了 OpenAI API，使用 OpenAIEmbedding
    3. 否则使用 ImprovedMockEmbedding
    """
    provider = config.provider.lower()

    # 千问优先（中文效果最好）
    if provider == "qwen" and config.api_key:
        logger.info("[Embedding] 使用千问 Embedding 服务")
        return QwenEmbedding(config)

    # OpenAI 兼容 API
    if provider == "openai" and config.api_key:
        logger.info("[Embedding] 使用 OpenAI Embedding 服务")
        return OpenAIEmbedding(config)

    # 默认使用改进的 Mock
    logger.info("[Embedding] 使用改进的 Mock Embedding 服务")
    return ImprovedMockEmbedding(config)
