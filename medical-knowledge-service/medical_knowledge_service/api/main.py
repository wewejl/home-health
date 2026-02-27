"""
医学知识库服务 API
"""
import os
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..knowledge_service import KnowledgeService
from ..core import KnowledgeConfig, EmbeddingConfig, VectorStoreConfig


# 全局服务实例
_knowledge_service: Optional[KnowledgeService] = None


def get_service() -> KnowledgeService:
    """获取知识库服务实例"""
    if _knowledge_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    return _knowledge_service


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """验证 API Key"""
    expected_key = os.getenv("API_KEY", "dev-key-123456")

    if expected_key and expected_key != "dev-key-123456":
        if not x_api_key or x_api_key != expected_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _knowledge_service

    # 启动时初始化
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/medical_knowledge"
    )

    config = KnowledgeConfig(
        embedding=EmbeddingConfig(
            provider=os.getenv("EMBEDDING_PROVIDER", "mock"),
            dimension=int(os.getenv("DIMENSION", "1024")),
            api_key=os.getenv("EMBEDDING_API_KEY"),
            base_url=os.getenv("EMBEDDING_BASE_URL"),
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
        ),
        vector_store=VectorStoreConfig(
            provider="pgvector",
            connection_string=database_url,
            table_name=os.getenv("VECTOR_TABLE", "knowledge_vectors")
        )
    )

    _knowledge_service = KnowledgeService(config)
    await _knowledge_service.initialize()

    # 加载初始数据
    await _knowledge_service.load_data(force_reload=False)

    yield

    # 关闭时清理
    if _knowledge_service:
        await _knowledge_service.close()


# 创建 FastAPI 应用
app = FastAPI(
    title="Medical Knowledge Service",
    description="医学知识库向量检索服务",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Request Models ============

class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., description="搜索查询文本", min_length=1)
    specialty: Optional[str] = Field(None, description="科室过滤")
    top_k: int = Field(5, description="返回结果数量", ge=1, le=50)
    score_threshold: float = Field(0.0, description="相似度阈值", ge=0.0, le=1.0)


class LoadDataRequest(BaseModel):
    """加载数据请求"""
    force_reload: bool = Field(False, description="是否强制重新加载")


# ============ API Endpoints ============

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Medical Knowledge Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    service = get_service()
    health = await service.health_check()
    return health


@app.post("/api/v1/search")
async def search_knowledge(
    request: SearchRequest,
    _: None = Depends(verify_api_key)
):
    """
    搜索医学知识

    根据查询文本检索相关的医学知识条目。
    """
    service = get_service()

    result = await service.search(
        query=request.query,
        specialty=request.specialty,
        top_k=request.top_k,
        score_threshold=request.score_threshold
    )

    return {
        "success": True,
        "data": result
    }


@app.post("/api/v1/data/load", dependencies=[Depends(verify_api_key)])
async def load_data(request: LoadDataRequest):
    """
    加载知识库数据

    将 ICD-10 医学知识数据加载到向量数据库中。
    """
    service = get_service()

    loaded_counts = await service.load_data(force_reload=request.force_reload)

    return {
        "success": True,
        "data": {
            "loaded": loaded_counts,
            "total": sum(loaded_counts.values())
        },
        "message": f"已加载 {sum(loaded_counts.values())} 条知识数据"
    }


@app.get("/api/v1/stats", dependencies=[Depends(verify_api_key)])
async def get_stats():
    """
    获取知识库统计信息

    返回知识库中的文档数量、各科室分布等信息。
    """
    service = get_service()

    stats = await service.get_stats()

    return {
        "success": True,
        "data": stats
    }


@app.get("/api/v1/specialties")
async def list_specialties():
    """
    获取支持的科室列表

    返回所有支持医学专科的列表。
    """
    specialties = [
        {"code": "dermatology", "name": "皮肤科", "diseases": ["湿疹", "银屑病", "特应性皮炎", "甲癣"]},
        {"code": "cardiology", "name": "心内科", "diseases": ["高血压", "心肌梗死", "心力衰竭"]},
        {"code": "respiratory", "name": "呼吸科", "diseases": ["支气管哮喘", "慢阻肺"]},
        {"code": "gastroenterology", "name": "消化科", "diseases": ["胃食管反流病", "胃溃疡"]},
        {"code": "neurology", "name": "神经内科", "diseases": ["偏头痛", "多发性硬化"]},
        {"code": "endocrinology", "name": "内分泌科", "diseases": ["2型糖尿病"]},
        {"code": "orthopedics", "name": "骨科", "diseases": ["下腰痛"]},
        {"code": "ophthalmology", "name": "眼科", "diseases": ["近视"]},
        {"code": "otorhinolaryngology", "name": "耳鼻喉科", "diseases": ["过敏性鼻炎"]},
        {"code": "obstetrics_gynecology", "name": "妇产科", "diseases": ["痛经"]},
        {"code": "pediatrics", "name": "儿科", "diseases": ["急性上呼吸道感染"]},
        {"code": "general", "name": "全科", "diseases": []},
    ]

    return {
        "success": True,
        "data": specialties
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)
