from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import secrets
import warnings


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "灵犀健康 API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SEED_DATA: bool = True

    # 服务端口 (固定使用 8100)
    PORT: int = 8100

    # 文件上传配置
    UPLOAD_DIR: Path = Path("static/uploads/medical_files")
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: dict = {
        "image": {".jpg", ".jpeg", ".png", ".gif", ".heic", ".webp"},
        "pdf": {".pdf"},
        "video": {".mp4", ".mov", ".avi", ".mkv"},
        "audio": {".mp3", ".m4a", ".wav", ".aac"},
        "document": {".doc", ".docx", ".txt", ".xls", ".xlsx"}
    }
    
    # 数据库
    # 添加 UTC 时区配置以修复日期格式问题 (PostgreSQL 输出格式与 Pydantic 兼容)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/home_health?options=-c%20timezone%3DUTC"
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
    
    # 语音转写配置 - 统一使用阿里云 Qwen-ASR
    ASR_SAMPLE_RATE: int = 16000

    # 阿里云 DashScope 配置（语音识别）
    DASHSCOPE_API_KEY: str = ""
    
    # Admin JWT 配置
    ADMIN_JWT_SECRET: str = "admin-secret-key-change-in-production"
    ADMIN_JWT_EXPIRE_HOURS: int = 24

    # CORS 配置
    CORS_ALLOWED_ORIGINS: str = ""  # 逗号分隔的允许来源列表
    CORS_ALLOW_CREDENTIALS: bool = True

    class Config:
        # 支持多环境文件：.env.local 会覆盖 .env
        env_file = (".env.local", ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_security_settings()

    def _validate_security_settings(self):
        """验证安全配置，在非开发环境发出警告"""
        if not self.DEBUG:
            # 生产环境安全检查
            if self.JWT_SECRET_KEY in [
                "dev-secret-key-change-in-production",
                "admin-secret-key-change-in-production",
                "xinlin-doctor-secret-key-2024",
            ]:
                warnings.warn(
                    "⚠️  SECURITY WARNING: Using default JWT secret key in production! "
                    "Set a strong JWT_SECRET_KEY and ADMIN_JWT_SECRET in environment.",
                    RuntimeWarning,
                    stacklevel=2
                )

            if not self.CORS_ALLOWED_ORIGINS:
                warnings.warn(
                    "⚠️  SECURITY WARNING: CORS_ALLOWED_ORIGINS not set in production. "
                    "This may allow unauthorized cross-origin requests.",
                    RuntimeWarning,
                    stacklevel=2
                )

    @property
    def cors_origins_list(self) -> list[str]:
        """获取 CORS 允许的来源列表"""
        if self.CORS_ALLOWED_ORIGINS:
            return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",")]
        # 开发环境默认允许本地来源
        if self.DEBUG:
            return [
                "http://localhost:8150",  # 前端固定端口
                "http://127.0.0.1:8150",
                "http://localhost:5173",  # 兼容其他项目
                "http://localhost:5174",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:5174",
                "http://127.0.0.1:3000",
            ]
        # 生产环境默认不允许跨域
        return []

    @property
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return not self.DEBUG

    @property
    def should_use_secure_cookies(self) -> bool:
        """生产环境使用安全 cookies"""
        return self.is_production


@lru_cache()
def get_settings() -> Settings:
    return Settings()
