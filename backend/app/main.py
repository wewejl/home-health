from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .routes import (
    auth_router, departments_router, sessions_router, feedbacks_router, diseases_router, drugs_router,
    diagnosis_router, derma_router,
    admin_auth_router, admin_doctors_router, admin_departments_router,
    admin_knowledge_router, admin_documents_router, admin_feedbacks_router, admin_stats_router,
    admin_diseases_router, admin_drugs_router, admin_drug_categories_router
)
from .services.admin_auth_service import AdminAuthService
from .seed import seed_data
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="鑫琳医生 API",
    description="AI医生分身系统后端API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 用户端路由
app.include_router(auth_router)
app.include_router(departments_router)
app.include_router(sessions_router)
app.include_router(feedbacks_router)
app.include_router(diseases_router)
app.include_router(drugs_router)
app.include_router(diagnosis_router)
app.include_router(derma_router)

# 管理后台路由
app.include_router(admin_auth_router)
app.include_router(admin_doctors_router)
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
    return {"status": "healthy"}
