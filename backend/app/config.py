from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "鑫琳医生 API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SEED_DATA: bool = True
    
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
    
    # LLM 配置
    LLM_PROVIDER: str = "qwen"
    LLM_MODEL: str = "qwen-plus"
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.7
    
    # Qwen-VL 多模态配置（皮肤科智能体使用）
    QWEN_VL_MODEL: str = "qwen-vl-plus"  # 可选: qwen-vl-plus, qwen-vl-max, qwen2-vl-7b-instruct
    
    # Admin JWT 配置
    ADMIN_JWT_SECRET: str = "admin-secret-key-change-in-production"
    ADMIN_JWT_EXPIRE_HOURS: int = 24

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
