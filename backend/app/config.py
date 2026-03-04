from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import secrets
import warnings
import os


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
    # 默认使用 Docker 内部网络配置，本地开发可通过环境变量覆盖
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@postgres:5432/home_health?options=-c%20timezone%3DUTC"
    KNOWLEDGE_DB_URL: str = "sqlite:///./knowledge.db"  # 知识库独立存储

    # JWT 配置
    # 生成强随机密钥作为默认值（仅用于开发环境）
    # 生产环境必须通过环境变量设置
    _default_jwt_secret = secrets.token_urlsafe(32)
    JWT_SECRET_KEY: str = _default_jwt_secret
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 测试模式（默认关闭，生产环境安全）
    TEST_MODE: bool = False
    # - true 时: 验证码 000000 为万能验证码，其他验证码正常验证（但不发真实短信）
    # - false 时: 所有验证码必须真实验证，发送真实短信（需配置阿里云）

    # 管理员认证测试模式（独立控制，默认关闭，生产环境安全）
    ADMIN_TEST_MODE: bool = False
    # - true 时: 管理员/医生 API 跳过认证检查，自动使用测试账号
    # - false 时: 必须提供有效的 JWT token

    # 测试账号手机号（仅这些号码可以使用 000000 验证码）
    TEST_PHONES: str = "18107300888"  # 多个号码用逗号分隔，如 "13800138000,13900139000"

    # 短信服务配置（已废弃，由 SMS_PROVIDER 和 TEST_MODE 控制）
    ENABLE_SMS_VERIFICATION: bool = False  # 保留此配置仅为兼容，不再使用

    # 短信服务提供商
    SMS_PROVIDER: str = "aliyun"  # mock=模拟发送(仅日志), aliyun=阿里云短信
    SMS_ACCESS_KEY_ID: str = "LTAI5tMPbmvNP5rNzd6uiALx"
    SMS_ACCESS_KEY_SECRET: str = "zb5cA+aWzARI/OosFzD1Dv/8tqVj49iawGCKI2rs9/5qMKnCgi3SbomCeVY/EUCAmtqUGF3fb3JU6p1AWYtBLzo343Y78hcnOE6DYIgIT538gBmJfjRM4rH9lvRYlMg6CdJYXUw2NaAt8539dqtwkson83zCv+UdN5ylnJLm6nwfnA40fWXazBJeCKWq3ftJ/WIRYk+og0Qg65gINE6tz7yM3D1vFuUkjlmMS0mHoz08yUy/jKKVUiW9kjRRCJLRMfqOeOsQokM="
    SMS_SIGN_NAME: str = "鑫琳医生"
    SMS_TEMPLATE_CODE: str = ""

    # 阿里云号码认证服务（一键登录）
    DYPNS_APP_KEY: str = "FC220000012370277"  # 方案Code，iOS/Android SDK 需要
    
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
    USE_AGENTIC_ENGINE: bool = False  # 是否启用主智能体+检索子智能体引擎
    AGENTIC_ENABLED_SPECIALTIES: str = "general,cardiology,respiratory"  # agentic 灰度专科白名单
    AGENTIC_MAX_CONTEXT_TURNS: int = 200  # 会话上下文最大轮次（默认覆盖完整问诊）
    # Agentic 引擎内部配置
    AGENTIC_MODEL_CONTEXT_MESSAGES: int = 14  # LLM 上下文保留的最近消息轮次
    AGENTIC_MAX_QUERY_LENGTH: int = 200  # 检索查询最大字符数
    AGENTIC_MAX_USER_INPUT_LENGTH: int = 5000  # 用户输入最大字符数（防止提示注入）
    AGENTIC_STREAM_CHUNK_SIZE: int = 12  # SSE 流式响应分块大小
    USE_TRIAGE_ENGINE: bool = True  # 是否启用新导诊引擎灰度开关
    TRIAGE_ENABLED_SPECIALTIES: str = "general,cardiology,respiratory"  # 灰度专科白名单
    AI_ENGINE_MODE: str = "remote_ai"  # legacy | remote_ai | hybrid_shadow
    AI_SERVICE_URL: str = "http://192.168.65.254:8300"  # 独立 AI 后端地址 (host.docker.internal IP)
    AI_SERVICE_TOKEN: str = ""  # backend -> ai 服务鉴权 token
    AI_SERVICE_TIMEOUT: int = 20  # 请求总超时（秒）
    AI_SERVICE_CONNECT_TIMEOUT: int = 3  # 建连超时（秒）
    AI_SERVICE_MAX_RETRIES: int = 1  # 可重试次数（仅 timeout/5xx/429）
    AI_SERVICE_RETRY_BACKOFF_MS: int = 200  # 首次重试退避（毫秒）
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

    # 知识库服务配置（独立服务）
    KNOWLEDGE_SERVICE_URL: str = "http://localhost:8200"  # 独立知识库服务地址
    KNOWLEDGE_SERVICE_API_KEY: str = "change-me-knowledge-key"  # 默认启用鉴权，生产环境必须替换
    KNOWLEDGE_SERVICE_TIMEOUT: int = 10  # 请求超时（秒）

    # Admin JWT 配置
    # 生成强随机密钥作为默认值（仅用于开发环境）
    # 生产环境必须通过环境变量设置
    _default_admin_jwt_secret = secrets.token_urlsafe(32)
    ADMIN_JWT_SECRET: str = _default_admin_jwt_secret
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
        """验证安全配置，生产环境强制检查"""
        valid_ai_modes = {"legacy", "remote_ai", "hybrid_shadow"}
        if self.ai_engine_mode not in valid_ai_modes:
            raise ValueError(
                f"CONFIG ERROR: AI_ENGINE_MODE must be one of {sorted(valid_ai_modes)}, "
                f"got: {self.AI_ENGINE_MODE!r}"
            )

        if self.ai_engine_mode in {"remote_ai", "hybrid_shadow"}:
            if not self.AI_SERVICE_URL:
                raise ValueError(
                    "CONFIG ERROR: AI_SERVICE_URL is required when AI_ENGINE_MODE is remote_ai/hybrid_shadow"
                )

        if not self.DEBUG:
            # 生产环境安全检查
            # 检查是否使用了默认生成的密钥或已知的弱密钥
            default_secrets = {
                "dev-secret-key-change-in-production",
                "admin-secret-key-change-in-production",
                "your-secret-key-change-in-production",
                "xinlin-doctor-secret-key-2024",
                self._default_jwt_secret,
                self._default_admin_jwt_secret,
                # 检查示例配置中的弱密钥
                "CHANGE_THIS_IN_PRODUCTION_USE_STRONG_RANDOM_KEY",
                "change-me-knowledge-key",
                "dev-key-123456",
                "",
            }

            # 强制检查 JWT 密钥（生产环境必须设置强密钥）
            if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY in default_secrets:
                raise ValueError(
                    "SECURITY ERROR: Production environment requires a strong JWT_SECRET_KEY. "
                    "Set it via environment variable. Generate with: "
                    'python -c "import secrets; print(secrets.token_urlsafe(32))"'
                )

            if not self.ADMIN_JWT_SECRET or self.ADMIN_JWT_SECRET in default_secrets:
                raise ValueError(
                    "SECURITY ERROR: Production environment requires a strong ADMIN_JWT_SECRET. "
                    "Set it via environment variable. Generate with: "
                    'python -c "import secrets; print(secrets.token_urlsafe(32))"'
                )

            # 检查测试模式（生产环境必须关闭）
            if self.TEST_MODE:
                raise ValueError(
                    "SECURITY ERROR: TEST_MODE is enabled in production environment. "
                    "Set TEST_MODE=false in environment variables."
                )

            if self.ADMIN_TEST_MODE:
                raise ValueError(
                    "SECURITY ERROR: ADMIN_TEST_MODE is enabled in production environment. "
                    "Set ADMIN_TEST_MODE=false in environment variables."
                )

            # 检查知识库服务 API Key（生产环境必须设置强密钥）
            if not self.KNOWLEDGE_SERVICE_API_KEY or self.KNOWLEDGE_SERVICE_API_KEY in default_secrets:
                raise ValueError(
                    "SECURITY ERROR: Production environment requires a strong KNOWLEDGE_SERVICE_API_KEY. "
                    "Set it via environment variable."
                )

            # 检查 AI 服务 token（remote_ai / hybrid_shadow 需要）
            if self.ai_engine_mode in {"remote_ai", "hybrid_shadow"}:
                if not self.AI_SERVICE_TOKEN or self.AI_SERVICE_TOKEN in default_secrets:
                    raise ValueError(
                        "SECURITY ERROR: Production environment with remote AI requires a strong AI_SERVICE_TOKEN. "
                        "Set it via environment variable."
                    )

            # CORS 配置警告（可选，不阻止启动）
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

    @property
    def triage_enabled_specialties_list(self) -> list[str]:
        """导诊引擎灰度专科白名单"""
        raw = self.TRIAGE_ENABLED_SPECIALTIES or ""
        items = [s.strip().lower() for s in raw.split(",") if s.strip()]
        return items or ["general", "cardiology", "respiratory"]

    @property
    def agentic_enabled_specialties_list(self) -> list[str]:
        """agentic 引擎灰度专科白名单"""
        raw = self.AGENTIC_ENABLED_SPECIALTIES or ""
        items = [s.strip().lower() for s in raw.split(",") if s.strip()]
        return items or ["general", "cardiology", "respiratory"]

    @property
    def ai_engine_mode(self) -> str:
        """AI 引擎模式（统一小写）"""
        return (self.AI_ENGINE_MODE or "legacy").strip().lower()


# 全局设置实例（单例模式）
_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """获取设置实例（单例模式，支持运行时配置更新）"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reset_settings() -> None:
    """重置设置实例（用于测试或配置更新）"""
    global _settings_instance
    _settings_instance = None
