from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件中的环境变量

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .routes import (
    auth_router, departments_router, sessions_router, sessions_v2_router, feedbacks_router, diseases_router, drugs_router,
    medical_events_router, ai_router, persona_chat_router, record_analysis_router,  # diagnosis_router, derma_router 已废弃
    medical_orders_router,  # 医嘱执行监督系统
    rounding_router,  # 远程查房系统
    admin_auth_router, admin_doctors_router, admin_departments_router,
    admin_knowledge_router, admin_documents_router, admin_feedbacks_router, admin_stats_router,
    admin_diseases_router, admin_drugs_router, admin_drug_categories_router,
    funasr_router,  # FunASR 语音识别
    voice_router,  # 语音服务转发 (ASR + TTS)
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

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="鑫琳医生 API",
    description="AI医生分身系统后端API",
    version="2.0.0"
)

# CORS 配置 - 根据环境变量动态设置
def get_cors_origins():
    """根据环境获取允许的 CORS 源"""
    allowed_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if allowed_origins_str:
        return [origin.strip() for origin in allowed_origins_str.split(",")]
    # 开发环境默认允许所有来源
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    if debug_mode:
        return ["*"]
    # 生产环境默认只允许同源
    return []

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 用户端路由
app.include_router(auth_router)
app.include_router(departments_router)
app.include_router(sessions_router)
app.include_router(sessions_v2_router)  # V2 多智能体架构
app.include_router(feedbacks_router)
app.include_router(diseases_router)
app.include_router(drugs_router)
# diagnosis_router, derma_router 已废弃，使用 sessions_router 统一接口
app.include_router(medical_events_router)
app.include_router(ai_router)
app.include_router(medical_orders_router)  # 医嘱执行监督系统
app.include_router(rounding_router)  # 远程查房系统
app.include_router(funasr_router)  # FunASR 语音识别
app.include_router(voice_router)  # 语音服务转发 (ASR + TTS)

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
    return {"message": "鑫琳医生 AI分身系统 API 服务运行中", "version": "2.0.0"}


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
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "test_mode": os.getenv("TEST_MODE", "false").lower() == "true",
        "cors_origins_configured": bool(os.getenv("CORS_ALLOWED_ORIGINS"))
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
