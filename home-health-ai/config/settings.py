"""
HIS 门诊智能助手系统 - 配置文件
"""

import os
from pathlib import Path

# ============================================
# 项目路径
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ============================================
# DeepSeek API 配置
# ============================================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-134730411ff645efba6522a419f51be3")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ============================================
# PostgreSQL 配置
# ============================================

# Docker 数据库配置
POSTGRESQL_HOST = os.getenv("POSTGRESQL_HOST", "localhost")
POSTGRESQL_PORT = os.getenv("POSTGRESQL_PORT", "5433")
POSTGRESQL_DB = os.getenv("POSTGRESQL_DB", "home_health")
POSTGRESQL_USER = os.getenv("POSTGRESQL_USER", "postgres")
POSTGRESQL_PASSWORD = os.getenv("POSTGRESQL_PASSWORD", "postgres")

# 构建数据库连接字符串
if POSTGRESQL_PASSWORD:
    POSTGRESQL_URL = f"postgresql://{POSTGRESQL_USER}:{POSTGRESQL_PASSWORD}@{POSTGRESQL_HOST}:{POSTGRESQL_PORT}/{POSTGRESQL_DB}"
else:
    # 使用 Unix socket 或 peer 认证
    POSTGRESQL_URL = f"postgresql://@{POSTGRESQL_HOST}:{POSTGRESQL_PORT}/{POSTGRESQL_DB}"

# 别名（简化导入）
DATABASE_URL = POSTGRESQL_URL

# ============================================
# 应用配置
# ============================================

# 应用配置
APP_NAME = "HIS 门诊智能助手"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# API 配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# 会话配置
SESSION_DEFAULT_TITLE = "新对话"
SESSION_MAX_HISTORY = 100  # 保留最近 N 条消息
SESSION_AUTO_SAVE_INTERVAL = 60  # 自动保存间隔（秒）

# ============================================
# AutoGen 配置
# ============================================

# Model Client 配置（官方格式）- 保留用于兼容性
AUTOGEN_MODEL_CONFIG = {
    "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
    "config": {
        "model": DEEPSEEK_MODEL,
        "api_key": DEEPSEEK_API_KEY,
        "base_url": DEEPSEEK_BASE_URL,
        "model_info": {
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "unknown",
            "structured_output": False,
            "multiple_system_messages": True,
        },
    },
}

# Model Client 工厂函数（符合 AutoGen 最佳实践）
def create_model_client(parallel_tool_calls: bool = True):
    """创建 OpenAI Chat Completion Client

    Args:
        parallel_tool_calls: 是否允许并行工具调用
            - 主 Agent 使用 AgentTool 时必须设为 False
            - 子 Agent 可以设为 True（默认）

    Returns:
        OpenAIChatCompletionClient: 模型客户端实例

    参考:
        AutoGen 官方文档：使用 AgentTool 时主 Agent 必须禁用并行工具调用
    """
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    from autogen_core.models import ModelFamily

    return OpenAIChatCompletionClient(
        model=DEEPSEEK_MODEL,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": ModelFamily.UNKNOWN,
            "structured_output": False,
            "multiple_system_messages": True,
        },
        parallel_tool_calls=parallel_tool_calls,
    )

# Agent 配置
AGENT_CONFIG = {
    "diagnosis": {
        "name": "diagnosis_expert",
        "system_message": """你是HIS医院的诊断专家。

你的职责：
- 根据患者症状提供初步诊断建议
- 推荐必要的检查项目
- 解读检查结果

⚠️ 重要声明：
- 所有建议仅供参考，不能替代专业医师的临床判断
- 遇到急症应立即建议患者就医
""",
        "description": "诊断专家",
    },
    "medication": {
        "name": "medication_expert",
        "system_message": """你是HIS医院的用药专家。

你的职责：
- 提供用药建议
- 检查药物相互作用
- 提醒用药注意事项

⚠️ 重要声明：
- 所有用药建议仅供参考
- 必须遵循医师处方
- 注意过敏史和禁忌症
""",
        "description": "用药专家",
    },
    "guideline": {
        "name": "guideline_expert",
        "system_message": """你是HIS医院的临床指南专家。

你的职责：
- 查询临床诊疗指南
- 提供循证医学建议
- 解读ICD编码

⚠️ 重要声明：
- 提供的信息基于权威指南
- 临床决策需结合患者具体情况
""",
        "description": "指南查询专家",
    },
}

# ============================================
# 日志配置
# ============================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / "app.log"

# ============================================
# 安全配置
# ============================================

# 敏感信息脱敏
SENSITIVE_FIELDS = ["password", "api_key", "token", "secret"]

# 数据导出限制
MAX_EXPORT_ROWS = 10000

# ============================================
# 工具函数配置
# ============================================

# ICD-10 编码数据库（示例）
ICD10_DATABASE = {
    "高血压": "I10 - 特发性（原发性）高血压",
    "冠心病": "I25 - 慢性缺血性心脏病",
    "糖尿病": "E11 - 2型糖尿病",
    "肺炎": "J18 - 肺炎，未特指",
    "胃炎": "K29 - 胃炎和十二指肠炎",
}

# 常见药物相互作用
DRUG_INTERACTIONS = {
    ("阿司匹林", "华法林"): "🔴 严重相互作用：阿司匹林 + 华法林可增加出血风险",
    ("ACE抑制剂", "保钾利尿剂"): "⚠️ 中度相互作用：可能导致高钾血症",
}

# ============================================
# 性能配置
# ============================================

# 并发配置
MAX_CONCURRENT_SESSIONS = 100
SESSION_TIMEOUT = 3600  # 会话超时（秒）

# 缓存配置
CACHE_ENABLED = True
CACHE_TTL = 3600  # 缓存过期时间（秒）

# ============================================
# 环境变量验证
# ============================================

def validate_config():
    """验证配置是否完整"""
    errors = []

    if not DEEPSEEK_API_KEY:
        errors.append("DEEPSEEK_API_KEY 未设置")

    # 测试数据库连接
    try:
        import psycopg
        conn = psycopg.connect(POSTGRESQL_URL)
        conn.close()
    except Exception as e:
        errors.append(f"数据库连接失败: {e}")

    return errors


if __name__ == "__main__":
    # 验证配置
    errors = validate_config()
    if errors:
        print("❌ 配置错误:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ 配置验证通过")
        print(f"📊 数据库: {POSTGRESQL_DB}")
        print(f"🤖 模型: {DEEPSEEK_MODEL}")
