"""
FastAPI 应用 - HIS 门诊 AI 助手 REST API
"""

import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from src.services.chat_service import ChatService
from src.api.ios_adapter import get_ios_adapter
from src.api.models import (
    ChatRequest,
    SessionHistoryResponse,
    SessionListResponse,
    DeleteSessionResponse,
    HealthResponse,
    ErrorResponse,
    iOSMessageRequest,
)
from src.api.backend_compat import router as backend_compat_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局服务实例
chat_service: ChatService = None


# =====================================================
# 应用生命周期管理
# =====================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    global chat_service
    logger.info("🚀 启动 HIS 门诊 AI 助手 API...")

    try:
        chat_service = ChatService()
        logger.info("✅ ChatService 初始化成功")
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        raise

    yield

    # 关闭时清理
    logger.info("👋 关闭 HIS 门诊 AI 助手 API...")


# =====================================================
# FastAPI 应用
# =====================================================

app = FastAPI(
    title="HIS 门诊 AI 助手 API",
    description="为 HIS 医院系统提供智能医疗助手服务，支持多轮对话、用药建议、诊断辅助",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
import os
static_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'static')
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"✅ 静态文件挂载: {static_dir}")
else:
    logger.warning(f"⚠️  静态文件目录不存在: {static_dir}")

# 注册后端兼容路由
app.include_router(backend_compat_router)
logger.info("✅ 后端兼容路由已注册: /v1/chat/respond")


# =====================================================
# 核心接口：对话
# =====================================================

@app.post(
    "/chat/stream",
    summary="对话接口（流式响应）",
    description="处理用户对话消息，以流式方式返回 AI 思考过程、工具调用和最终回复",
    tags=["对话"]
)
async def chat_stream(request: ChatRequest):
    """对话接口（主接口）

    流式输出：
    - ThoughtEvent（AI 思考过程）
    - ToolCallRequestEvent（工具调用）
    - ToolCallExecutionEvent（工具执行结果）
    - Response（最终回复）

    特点：
    - ✅ 使用 AutoGen 框架
    - ✅ 保留双 Agent 架构（主 Agent + 用药专家）
    - ✅ 保留工具调用
    - ✅ 实时显示 AI 思考过程
    - ✅ 支持跨会话记忆

    Args:
        request: 对话请求

    Returns:
        StreamingResponse: 流式响应

    Example:
        ```javascript
        const response = await fetch('/chat/stream', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({...})
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            console.log(decoder.decode(value));
        }
        ```
    """
    async def generate_response() -> AsyncGenerator[str, None]:
        """生成 AutoGen 流式响应"""
        try:
            logger.info(f"[/chat/stream] session_id={request.session_id}, user={request.his_user_id}")

            # 调用 AutoGen 流式服务（已格式化为 SSE）
            async for event in chat_service.chat_stream_autogen(
                session_id=request.session_id,
                his_user_id=request.his_user_id,
                message=request.message,
                his_patient_id=request.his_patient_id
            ):
                # chat_stream_autogen 已返回 "data: {...}\n\n" 格式，直接 yield
                yield event

            # 发送完成标记
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

            logger.info(f"[/chat/stream] 流式响应完成: session_id={request.session_id}")

        except Exception as e:
            logger.error(f"[/chat/stream] 错误: {e}", exc_info=True)

            # 发送错误信息
            error_data = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


# =====================================================
# iOS 兼容接口
# =====================================================

@app.post(
    "/sessions/{session_id}/messages",
    summary="iOS 问诊接口（流式响应）",
    description="iOS 问诊模块专用接口，兼容 iOS SSE 格式",
    tags=["iOS"]
)
async def ios_send_message(
    session_id: str,
    request: iOSMessageRequest
):
    """iOS 问诊接口 - 兼容 iOS SSE 格式

    SSE 事件格式:
        event: meta
        data: {"session_id": "...", "agent_type": "general"}

        event: chunk
        data: {"text": "增量文本"}

        event: complete
        data: {"message": "完整回复", "stage": "...", "progress": 100}

        event: error
        data: {"error": "错误信息"}

    Args:
        session_id: 会话 ID
        request: iOS 消息请求

    Returns:
        StreamingResponse: SSE 流式响应
    """
    async def generate_ios_response() -> AsyncGenerator[str, None]:
        """生成 iOS 格式流式响应"""
        try:
            logger.info(f"[/sessions/{session_id}/messages] iOS 请求")

            adapter = get_ios_adapter()

            # 转换请求格式
            his_user_id = getattr(request, 'his_user_id', None) or f"user_{session_id}"

            async for event in adapter.stream_to_ios_format(
                session_id=session_id,
                his_user_id=his_user_id,
                message=request.content,
                his_patient_id=None
            ):
                yield event

            logger.info(f"[/sessions/{session_id}/messages] 完成")

        except Exception as e:
            logger.error(f"[/sessions/{session_id}/messages] 错误: {e}", exc_info=True)
            error_event = f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            yield error_event

    return StreamingResponse(
        generate_ios_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post(
    "/sessions",
    summary="iOS 创建会话",
    description="iOS 创建新会话接口",
    tags=["iOS"]
)
async def ios_create_session(
    doctor_id: int = None,
    agent_type: str = "general"
):
    """iOS 创建会话接口

    Args:
        doctor_id: 医生 ID（可选）
        agent_type: 智能体类型（默认 general）

    Returns:
        会话创建响应
    """
    import uuid
    session_id = f"session_{uuid.uuid4().hex[:12]}"

    return {
        "session_id": session_id,
        "agent_type": agent_type
    }


# =====================================================
# 查询接口
# =====================================================

@app.get(
    "/history/{session_id}",
    response_model=SessionHistoryResponse,
    summary="获取会话历史",
    description="获取指定会话的完整对话历史",
    responses={
        200: {"description": "查询成功"},
        404: {"model": ErrorResponse, "description": "会话不存在"},
    },
    tags=["查询"]
)
async def get_session_history(session_id: str) -> SessionHistoryResponse:
    """获取会话历史

    Args:
        session_id: 会话 ID

    Returns:
        SessionHistoryResponse: 会话历史记录

    Example:
        ```bash
        curl "http://localhost:8000/history/session_001"
        ```
    """
    try:
        logger.info(f"[/history/{session_id}] 查询会话历史")

        history = chat_service.get_session_history(session_id)

        return SessionHistoryResponse(
            session_id=session_id,
            messages=history,
            total_count=len(history)
        )

    except Exception as e:
        logger.error(f"[/history/{session_id}] 错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalError",
                "message": "查询会话历史失败",
                "detail": str(e)
            }
        )


@app.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="获取用户会话列表",
    description="获取指定用户的所有会话，按更新时间倒序排列",
    responses={
        200: {"description": "查询成功"},
    },
    tags=["查询"]
)
async def list_user_sessions(
    his_user_id: str,
    limit: int = 20
) -> SessionListResponse:
    """获取用户会话列表

    Args:
        his_user_id: HIS 医生 ID
        limit: 返回的最大数量（默认 20）

    Returns:
        SessionListResponse: 会话列表

    Example:
        ```bash
        curl "http://localhost:8000/sessions?his_user_id=doctor_123&limit=10"
        ```
    """
    try:
        logger.info(f"[/sessions] user={his_user_id}, limit={limit}")

        sessions = chat_service.list_user_sessions(his_user_id, limit)

        return SessionListResponse(
            his_user_id=his_user_id,
            sessions=sessions,
            total_count=len(sessions)
        )

    except Exception as e:
        logger.error(f"[/sessions] 错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalError",
                "message": "查询会话列表失败",
                "detail": str(e)
            }
        )


# =====================================================
# 管理接口
# =====================================================

@app.delete(
    "/sessions/{session_id}",
    response_model=DeleteSessionResponse,
    summary="删除会话",
    description="删除指定会话及其所有数据（对话历史、审计日志等）",
    responses={
        200: {"description": "删除成功"},
        404: {"model": ErrorResponse, "description": "会话不存在"},
    },
    tags=["管理"]
)
async def delete_session(session_id: str) -> DeleteSessionResponse:
    """删除会话

    ⚠️ **警告**：此操作不可逆，会删除会话的所有数据

    Args:
        session_id: 要删除的会话 ID

    Returns:
        DeleteSessionResponse: 删除结果

    Example:
        ```bash
        curl -X DELETE "http://localhost:8000/sessions/session_001"
        ```
    """
    try:
        logger.info(f"[/sessions/{session_id}] 删除会话")

        success = chat_service.delete_session(session_id)

        if success:
            return DeleteSessionResponse(
                success=True,
                session_id=session_id,
                message="会话删除成功"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "NotFound",
                    "message": f"会话 {session_id} 不存在",
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[/sessions/{session_id}] 错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalError",
                "message": "删除会话失败",
                "detail": str(e)
            }
        )


# =====================================================
# 健康检查
# =====================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查 API 服务状态",
    tags=["系统"]
)
async def health_check() -> HealthResponse:
    """健康检查接口

    Example:
        ```bash
        curl "http://localhost:8000/health"
        ```
    """
    try:
        # 测试数据库连接
        from src.db.connection import test_connection
        test_connection()

        return HealthResponse(
            status="healthy",
            service="HIS 门诊 AI 助手",
            version="1.0.0",
            database="connected"
        )

    except Exception as e:
        logger.error(f"[/health] 错误: {e}")
        return HealthResponse(
            status="unhealthy",
            service="HIS 门诊 AI 助手",
            version="1.0.0",
            database=f"error: {str(e)}"
        )


# =====================================================
# 根路径
# =====================================================

@app.get(
    "/",
    summary="API 信息",
    description="获取 API 基本信息",
    tags=["系统"]
)
async def root():
    """根路径 - API 信息"""
    return {
        "service": "HIS 门诊 AI 助手 API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "chat": "POST /chat/stream",
            "history": "GET /history/{session_id}",
            "sessions": "GET /sessions",
            "delete": "DELETE /sessions/{session_id}",
            "health": "GET /health"
        }
    }


# =====================================================
# 启动说明
# =====================================================

if __name__ == "__main__":
    import uvicorn

    print("""
╔════════════════════════════════════════════════════════════╗
║     🚀 HIS 门诊 AI 助手 API                                ║
╠════════════════════════════════════════════════════════════╣
║                                                              ║
║  API 文档: http://localhost:8000/docs                       ║
║  健康检查: http://localhost:8000/health                     ║
║                                                              ║
║  核心接口:                                                  ║
║  - POST /chat/stream       流式对话（主接口）               ║
║  - GET /history/{id}       获取会话历史                     ║
║  - GET /sessions           获取会话列表                     ║
║  - DELETE /sessions/{id}   删除会话                         ║
║                                                              ║
╚════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式自动重载
        log_level="info"
    )
