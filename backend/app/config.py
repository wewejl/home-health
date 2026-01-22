from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "鑫琳医生 API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SEED_DATA: bool = True

    # 服务端口 (固定使用 8100)
    PORT: int = 8100
    
    # 数据库
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # JWT 配置
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    TEST_MODE: bool = True
    
    # 验证码配置
    ENABLE_SMS_VERIFICATION: bool = False  # 临时禁用验证码功能，待接入真实短信服务后启用

    # 短信服务配置（阿里云）
    SMS_PROVIDER: str = "mock"  # mock/aliyun
    SMS_ACCESS_KEY_ID: str = ""
    SMS_ACCESS_KEY_SECRET: str = ""
    SMS_SIGN_NAME: str = ""
    SMS_TEMPLATE_CODE: str = ""
    
    # LLM 配置
    LLM_PROVIDER: str = "qwen"
    LLM_MODEL: str = "qwen-plus"
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.7
    
    # Qwen-VL 多模态配置（皮肤科智能体使用）
    QWEN_VL_MODEL: str = "qwen3-vl-plus"  # 可选: qwen3-vl-plus, qwen-vl-plus, qwen-vl-max
    
    # LangGraph 配置
    USE_LANGGRAPH: bool = True  # 是否使用 LangGraph 替代 CrewAI
    LLM_TIMEOUT: int = 30  # LLM 调用超时（秒）
    LLM_MAX_RETRIES: int = 1  # LLM 调用最大重试次数
    LLM_MAX_TOKENS: int = 1500  # 普通 LLM 最大 token
    LLM_VL_MAX_TOKENS: int = 2000  # 多模态 LLM 最大 token
    
    # AI 算法服务配置
    AI_SUMMARY_MODEL: str = ""  # 留空使用 LLM_MODEL
    AI_SUMMARY_MAX_TOKENS: int = 2000
    AI_SUMMARY_TEMPERATURE: float = 0.3
    AI_AGGREGATION_TIME_WINDOW_DAYS: int = 7
    AI_AGGREGATION_SIMILARITY_THRESHOLD: float = 0.7
    
    # 语音转写配置
    ASR_PROVIDER: str = "mock"  # mock/aliyun/openai
    ASR_SAMPLE_RATE: int = 16000
    OPENAI_API_KEY: str = ""  # 用于 Whisper API
    
    # Admin JWT 配置
    ADMIN_JWT_SECRET: str = "admin-secret-key-change-in-production"
    ADMIN_JWT_EXPIRE_HOURS: int = 24

    class Config:
        # 支持多环境文件：.env.local 会覆盖 .env
        env_file = (".env.local", ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
