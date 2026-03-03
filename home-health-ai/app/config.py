"""Runtime settings for home-health-ai service."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "home-health-ai"
    DEBUG: bool = True
    PORT: int = 8300

    INTERNAL_API_TOKEN: str = "change-me-internal-token"

    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen-plus"
    LLM_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 900
    LLM_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 1

    KNOWLEDGE_SERVICE_URL: str = "http://medical-knowledge-api:8200"
    KNOWLEDGE_SERVICE_API_KEY: str = "change-me-knowledge-key"
    KNOWLEDGE_SERVICE_TIMEOUT: int = 10
    KNOWLEDGE_TOP_K: int = 5

    class Config:
        env_file = (".env.local", ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
