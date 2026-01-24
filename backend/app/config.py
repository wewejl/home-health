from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "灵犀医生 API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SEED_DATA: bool = True

    # 服务端口 (固定使用 8100)
    PORT: int = 8100
    
    # 数据库
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/home_health"
    KNOWLEDGE_DB_URL: str = "sqlite:///./knowledge.db"  # 知识库独立存储
    
    # JWT 配置
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 测试模式
    TEST_MODE: bool = True
    # - true 时: 验证码 000000 为万能验证码，其他验证码正常验证（但不发真实短信）
    # - false 时: 所有验证码必须真实验证，发送真实短信（需配置阿里云）

    # 测试账号手机号（仅这些号码可以使用 000000 验证码）
    TEST_PHONES: str = "18107300888"  # 多个号码用逗号分隔，如 "13800138000,13900139000"

    # 短信服务配置（已废弃，由 SMS_PROVIDER 和 TEST_MODE 控制）
    ENABLE_SMS_VERIFICATION: bool = False  # 保留此配置仅为兼容，不再使用

    # 短信服务提供商
    SMS_PROVIDER: str = "mock"  # mock=模拟发送(仅日志), aliyun=阿里云短信
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
    ASR_PROVIDER: str = "mock"  # mock/aliyun/openai/glm
    ASR_SAMPLE_RATE: int = 16000
    OPENAI_API_KEY: str = ""  # 用于 Whisper API

    # GLM-ASR 配置（智谱语音识别）
    GLM_API_KEY: str = ""
    GLM_ASR_MODEL: str = "glm-asr-2512"
    GLM_ASR_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/audio/transcriptions"
    
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
