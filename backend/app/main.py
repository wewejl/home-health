from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件中的环境变量

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base, SessionLocal
from .config import get_settings
from .routes import (
    auth_router, departments_router,
    sessions_v2_router,  # V2 多智能体架构 (V1 已废弃)
    feedbacks_router, diseases_router, drugs_router,
    medical_events_router, ai_router, persona_chat_router, record_analysis_router,
    medical_orders_router,  # 医嘱执行监督系统
    rounding_router,  # 远程查房系统
    medical_folders_router,  # 病历夹管理
    medical_records_router,  # 病历记录管理
    medical_files_router,  # 医疗文件上传
    admin_auth_router, admin_doctors_router, admin_departments_router,
    admin_knowledge_router, admin_documents_router, admin_feedbacks_router, admin_stats_router,
    admin_diseases_router, admin_drugs_router, admin_drug_categories_router,
    funasr_router,  # FunASR 语音识别
    # voice_router,  # TTS 已移除，状态端点已废弃
    voice_asr_router,  # GLM-ASR 语音识别
)
from .services.admin_auth_service import AdminAuthService
from .seed import seed_data
from datetime import datetime
import os
import time
import httpx
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="灵犀健康 API",
    description="AI医生分身系统后端API",
    version="2.0.0"
)

# CORS 配置 - 使用 Settings 类中的配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 用户端路由
app.include_router(auth_router)
app.include_router(departments_router)
# V1 API 已废弃，统一使用 V2
# app.include_router(sessions_router)
app.include_router(sessions_v2_router)  # V2 多智能体架构
app.include_router(feedbacks_router)
app.include_router(diseases_router)
app.include_router(drugs_router)
app.include_router(medical_events_router)
app.include_router(ai_router)
app.include_router(medical_orders_router)  # 医嘱执行监督系统
app.include_router(medical_folders_router)  # 病历夹管理
app.include_router(medical_records_router)  # 病历记录管理
app.include_router(medical_files_router)  # 医疗文件上传
app.include_router(rounding_router)  # 远程查房系统
app.include_router(funasr_router)  # FunASR 语音识别
# app.include_router(voice_router)  # TTS 已移除
app.include_router(voice_asr_router)  # GLM-ASR 语音识别

# 管理后台路由
app.include_router(admin_auth_router)
app.include_router(admin_doctors_router)
app.include_router(persona_chat_router)  # 医生分身对话式采集
app.include_router(record_analysis_router)  # 病历分析
app.include_router(admin_departments_router)
app.include_router(admin_knowledge_router)
app.include_router(admin_documents_router)
app.include_router(admin_feedbacks_router)
app.include_router(admin_stats_router)
app.include_router(admin_diseases_router)
app.include_router(admin_drugs_router)
app.include_router(admin_drug_categories_router)

# 静态文件服务
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"📁 静态文件服务挂载: {static_dir}")
else:
    # 尝试创建 static 目录
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"📁 静态文件目录已创建: {static_dir}")


@app.on_event("startup")
def startup_event():
    # 初始化数据库表结构
    Base.metadata.create_all(bind=engine)
    
    # 检查是否需要初始化种子数据
    seed_data_enabled = os.getenv("SEED_DATA", "true").lower() == "true"
    
    if seed_data_enabled:
        print("🌱 开始初始化种子数据...")
        try:
            seed_data()
            print("✅ 种子数据初始化完成")
        except Exception as e:
            print(f"⚠️ 种子数据初始化失败: {e}")
    
    # 初始化默认管理员账户
    db = SessionLocal()
    try:
        AdminAuthService.init_default_admin(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "灵犀健康 AI分身系统 API 服务运行中", "version": "2.0.0"}


@app.get("/health")
def health():
    """基础健康检查端点"""
    return {"status": "healthy"}


@app.get("/health/detailed")
async def health_detailed():
    """详细健康检查端点 - 包含数据库、LLM 服务状态"""
    start_time = time.time()
    health_info = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "checks": {}
    }

    # 数据库健康检查
    db_status = {"status": "unknown"}
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = {"status": "healthy"}
    except Exception as e:
        db_status = {"status": "unhealthy", "error": str(e)}
        health_info["status"] = "degraded"
    health_info["checks"]["database"] = db_status

    # LLM 服务健康检查
    llm_status = {"status": "unknown"}
    llm_api_key = os.getenv("LLM_API_KEY")
    if llm_api_key and llm_api_key.startswith("sk-"):
        llm_status = {"status": "configured", "provider": os.getenv("LLM_PROVIDER", "qwen")}
    else:
        llm_status = {"status": "not_configured"}
        health_info["status"] = "degraded"
    health_info["checks"]["llm"] = llm_status

    # 环境信息
    health_info["environment"] = {
        "debug": settings.DEBUG,
        "test_mode": settings.TEST_MODE,
        "production": settings.is_production,
        "cors_origins": settings.cors_origins_list,
        "cors_configured": bool(settings.CORS_ALLOWED_ORIGINS),
    }

    # 响应时间
    health_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    return health_info


@app.get("/health/ready")
async def readiness():
    """就绪检查 - 用于 Kubernetes 等容器编排"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "error": str(e)}, 503


@app.get("/health/live")
async def liveness():
    """存活检查 - 用于 Kubernetes 等容器编排"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
