"""
后端兼容的 API 端点
为 backend 的 AI Gateway 提供兼容接口
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/chat", tags=["backend_compat"])


# =====================================================
# 请求/响应模型（与 backend 对齐）
# =====================================================

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRespondRequest(BaseModel):
    request_id: str
    session_id: str
    turn_index: int
    user_id: str
    agent_type: str
    locale: str = "zh-CN"
    stream: bool = False
    user_message: str
    history: List[ChatMessage] = []
    attachments: List[dict] = []
    debug: bool = False


class MemoryPatch(BaseModel):
    facts: List[str] = []
    summary_delta: str = ""
    profile_delta: dict = {}


class Citation(BaseModel):
    id: str
    source: str = "unknown"
    snippet: str = ""


class ToolTraceItem(BaseModel):
    name: str
    status: str = "ok"
    latency_ms: int = 0


class RespondMetrics(BaseModel):
    total_ms: int = 0
    llm_ms: int = 0
    tools_ms: int = 0
    model_calls: int = 0


class ErrorObject(BaseModel):
    code: str
    message: str
    retryable: bool = False


class ChatRespondResponse(BaseModel):
    request_id: str
    session_id: str
    turn_index: int
    assistant_message: str
    risk_level: str = "low"
    quick_options: List[str] = []
    memory_patch: MemoryPatch = Field(default_factory=MemoryPatch)
    citations: List[Citation] = []
    tool_trace: List[ToolTraceItem] = []
    metrics: RespondMetrics = Field(default_factory=lambda: RespondMetrics())
    error: ErrorObject = None


# =====================================================
# 端点实现
# =====================================================

@router.post("/respond", response_model=ChatRespondResponse)
async def chat_respond(request: ChatRespondRequest) -> ChatRespondResponse:
    """后端兼容接口 - 调用全科医生智能体"""
    import time
    import asyncio
    from src.agents.general_practitioner import create_general_practitioner

    start_time = time.time()

    try:
        logger.info(f"[BackendCompat] 收到请求: session={request.session_id}, message={request.user_message[:50]}")

        # 创建智能体
        agent = create_general_practitioner()

        # 调用智能体
        result = await agent.run(task=request.user_message)

        # 提取回复
        if result.messages:
            assistant_message = result.messages[-1].content
        else:
            assistant_message = "抱歉，我现在无法回答这个问题。"

        elapsed_ms = int((time.time() - start_time) * 1000)

        return ChatRespondResponse(
            request_id=request.request_id,
            session_id=request.session_id,
            turn_index=request.turn_index,
            assistant_message=assistant_message,
            risk_level="low",
            quick_options=[],
            metrics=RespondMetrics(
                total_ms=elapsed_ms,
                llm_ms=elapsed_ms,
                model_calls=1
            )
        )

    except Exception as e:
        logger.error(f"[BackendCompat] 处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
