"""
统一会话接口

简化版本：直接转发到远程 AI 服务（home-health-ai）
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
from typing import List, Optional, Dict, Any, AsyncGenerator, Union
import uuid
import json
import asyncio
import logging
from ..database import get_db, SessionLocal
from ..schemas.session import SessionCreate, SessionResponse, EnhancedSessionCreate
from ..schemas.message import MessageCreate, MessageResponse, MessageListResponse, EnhancedMessageCreate
from ..schemas.agent_response import AgentResponse
from ..models.session import Session as SessionModel
from ..models.message import Message, SenderType
from ..models.doctor import Doctor
from ..models.user import User
from ..dependencies import get_current_user
from ..services.ai_gateway import (
    AIGatewayClient,
    AIGatewayClientError,
    build_chat_respond_request,
    build_history_from_db_messages,
)
from ..config import get_settings

router = APIRouter(prefix="/sessions", tags=["sessions"])
settings = get_settings()
logger = logging.getLogger(__name__)


def _risk_to_disposition(risk_level: str) -> str:
    if risk_level == "emergency":
        return "er"
    if risk_level == "high":
        return "urgent_clinic"
    if risk_level == "medium":
        return "clinic"
    return "home"


def _trim_cache(cache: Dict[str, Any], max_entries: int = 30) -> Dict[str, Any]:
    if len(cache) <= max_entries:
        return cache
    keep_keys = list(cache.keys())[-max_entries:]
    return {k: cache[k] for k in keep_keys}


async def _single_complete_stream(
    response: AgentResponse,
    session_id: str,
    agent_type: str,
) -> AsyncGenerator[str, None]:
    meta_data = {"session_id": session_id, "agent_type": agent_type}
    yield f"event: meta\ndata: {json.dumps(meta_data, ensure_ascii=False)}\n\n"
    if response.message:
        chunk_data = {"text": response.message}
        yield f"event: chunk\ndata: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
    yield f"event: complete\ndata: {json.dumps(response.model_dump(), ensure_ascii=False)}\n\n"


async def _run_remote_ai_turn(
    *,
    session: SessionModel,
    db: DBSession,
    base_state: Dict[str, Any],
    content: str,
    attachments_data: List[Dict[str, Any]],
    debug_mode: bool,
    http_request: Request,
    user_id: int,
    agent_type: str,
) -> AgentResponse:
    request_id = http_request.headers.get("x-request-id") or f"req_{uuid.uuid4().hex}"
    turn_index = int(base_state.get("turn_index", 0)) + 1
    idempotency_key = f"{session.id}:{turn_index}:{request_id}"

    # 幂等性缓存：防止同一请求重复调用 AI
    cache = base_state.get("remote_ai_idempotency_cache", {})
    if isinstance(cache, dict):
        cached = cache.get(idempotency_key)
        if isinstance(cached, dict) and isinstance(cached.get("response"), dict):
            try:
                return AgentResponse.model_validate(cached["response"])
            except Exception:
                pass

    history_rows = db.query(Message).filter(
        Message.session_id == session.id
    ).order_by(Message.created_at.asc()).all()
    history = build_history_from_db_messages(history_rows, limit=20)

    locale = (
        http_request.headers.get("accept-language", "").split(",")[0].strip()
        or "zh-CN"
    )
    timezone = http_request.headers.get("x-timezone")
    channel = http_request.headers.get("x-client-channel", "web")
    gateway_request = build_chat_respond_request(
        request_id=request_id,
        session_id=session.id,
        turn_index=turn_index,
        user_id=str(user_id),
        agent_type=agent_type,
        user_message=content,
        history=history,
        attachments=attachments_data,
        locale=locale,
        stream=False,
        timezone=timezone,
        channel=channel,
        debug=debug_mode,
    )

    ai_client = AIGatewayClient()
    ai_response = await ai_client.respond(gateway_request, transport_request_id=request_id)

    message = (ai_response.assistant_message or "").strip()
    if not message:
        raise AIGatewayClientError(
            code="AI_BAD_RESPONSE",
            message="empty assistant_message from remote ai",
            retryable=False,
        )
    risk_level = ai_response.risk_level or "low"
    quick_options = (ai_response.quick_options or [])[:3]

    if risk_level == "emergency":
        stage, progress = "diagnosing", 100
    elif risk_level == "high":
        stage, progress = "diagnosing", 92
    elif quick_options:
        stage, progress = "collecting", min(80, 30 + turn_index * 8)
    else:
        stage, progress = "diagnosing", min(95, 60 + turn_index * 6)

    state_messages = []
    for row in history:
        state_messages.append({
            "type": "human" if row.role == "user" else "ai",
            "content": row.content,
        })
    state_messages.append({"type": "ai", "content": message})

    max_ctx = int(settings.AGENTIC_MAX_CONTEXT_TURNS or 0)
    if max_ctx > 0 and len(state_messages) > max_ctx:
        state_messages = state_messages[-max_ctx:]

    next_state = dict(base_state)
    next_state.update(
        {
            "session_id": session.id,
            "user_id": user_id,
            "agent_type": agent_type,
            "agentic_engine": True,
            "messages": state_messages,
            "last_user_message": content,
            "turn_index": turn_index,
            "stage": stage,
            "progress": progress,
            "risk_level": risk_level,
            "disposition": _risk_to_disposition(risk_level),
            "quick_options": quick_options,
            "current_response": message,
            "remote_ai_request_id": ai_response.request_id,
            "remote_ai_memory_patch": ai_response.memory_patch.model_dump(),
            "remote_ai_tool_trace": [item.model_dump() for item in ai_response.tool_trace],
            "remote_ai_metrics": ai_response.metrics.model_dump(),
        }
    )

    if isinstance(cache, dict):
        cache[idempotency_key] = {
            "response": {},
        }
        cache = _trim_cache(cache)
        next_state["remote_ai_idempotency_cache"] = cache

    specialty_data = {
        "agentic": {
            "mode": "remote_ai",
            "disposition": _risk_to_disposition(risk_level),
            "request_id": ai_response.request_id,
            "citations": [item.model_dump() for item in ai_response.citations],
            "tool_trace": [item.model_dump() for item in ai_response.tool_trace],
            "metrics": ai_response.metrics.model_dump(),
            "error": ai_response.error.model_dump() if ai_response.error else None,
            "degraded": ai_response.error is not None,
        }
    }

    response = AgentResponse(
        message=message,
        stage=stage,
        progress=progress,
        quick_options=quick_options,
        risk_level=risk_level,
        specialty_data=specialty_data,
        next_state=next_state,
        current_thought=None,
        reasoning_history=[],
        show_thinking=False,
    )

    if isinstance(cache, dict):
        cache[idempotency_key] = {"response": response.model_dump()}
        next_state["remote_ai_idempotency_cache"] = _trim_cache(cache)
        response.next_state = next_state

    return response


@router.post("", response_model=SessionResponse)
async def create_session(
    request: Union[SessionCreate, EnhancedSessionCreate],
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建会话

    简化版本：直接使用全科智能体
    """
    doctor = None

    if request.doctor_id:
        doctor = db.query(Doctor).filter(Doctor.id == request.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="医生不存在")

    # 固定使用全科智能体
    agent_type = "general"

    session_id = str(uuid.uuid4())

    session = SessionModel(
        id=session_id,
        user_id=current_user.id,
        doctor_id=request.doctor_id,
        agent_type=agent_type,
        agent_state={}
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionResponse(
        session_id=session.id,
        doctor_id=session.doctor_id,
        doctor_name=doctor.name if doctor else "AI全科医生",
        agent_type=session.agent_type,
        last_message=session.last_message,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at
    )


@router.post("/{session_id}/messages")
async def send_message(
    session_id: str,
    request: Union[MessageCreate, EnhancedMessageCreate],
    http_request: Request,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送消息

    返回 AgentResponse 统一格式

    测试模式：无需认证，可直接访问任何会话
    """
    from ..dependencies import TEST_MODE

    if TEST_MODE:
        session = db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()
    else:
        session = db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.user_id == current_user.id
        ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 获取会话智能体类型（固定为 general）
    agent_type = (session.agent_type or "general").lower()

    # 解析请求参数
    content = request.content
    attachments = getattr(request, 'attachments', None) or []
    action = getattr(request, 'action', 'conversation') or 'conversation'

    # 转换 attachments
    attachments_data = []
    if attachments:
        for att in attachments:
            if hasattr(att, 'model_dump'):
                attachments_data.append(att.model_dump())
            elif isinstance(att, dict):
                attachments_data.append(att)

    # 保存用户消息
    user_message = Message(
        session_id=session_id,
        sender=SenderType.user,
        content=content,
        message_type="text" if not attachments_data else "image",
        attachments=attachments_data if attachments_data else None
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # 恢复智能体状态
    state = session.agent_state or {}
    state["session_id"] = session.id
    state["user_id"] = current_user.id
    state["agent_type"] = agent_type

    # 检查是否请求流式响应
    accept_header = http_request.headers.get("accept", "")
    want_stream = "text/event-stream" in accept_header
    debug_mode = http_request.query_params.get("debug", "false").lower() in {"1", "true", "yes", "on"}

    # 转发到远程 AI 服务
    try:
        response = await _run_remote_ai_turn(
            session=session,
            db=db,
            base_state=state,
            content=content,
            attachments_data=attachments_data,
            debug_mode=debug_mode,
            http_request=http_request,
            user_id=current_user.id,
            agent_type=agent_type,
        )
    except AIGatewayClientError as exc:
        logger.warning("remote ai request failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"AI服务暂时不可用（{exc.code}），请稍后重试",
        )
    except Exception as exc:
        logger.exception("remote ai unknown error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI服务暂时不可用，请稍后重试",
        )

    # 保存 AI 消息
    ai_message = Message(
        session_id=session_id,
        sender=SenderType.ai,
        content=response.message,
        message_type="text",
        structured_data=response.specialty_data,
    )
    db.add(ai_message)

    # 更新会话状态
    session.agent_state = response.next_state
    session.last_message = response.message[:100] if response.message else ""
    db.commit()
    db.refresh(ai_message)

    if want_stream:
        return StreamingResponse(
            _single_complete_stream(response, session.id, agent_type),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    return response.model_dump()


@router.get("", response_model=List[SessionResponse])
def get_sessions(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户会话列表

    返回当前用户的所有会话
    """
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id
    ).order_by(SessionModel.updated_at.desc()).all()

    result = []
    for session in sessions:
        doctor = db.query(Doctor).filter(Doctor.id == session.doctor_id).first() if session.doctor_id else None
        result.append(SessionResponse(
            session_id=session.id,
            doctor_id=session.doctor_id,
            doctor_name=doctor.name if doctor else "AI全科医生",
            agent_type=session.agent_type or "general",
            last_message=session.last_message,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at
        ))
    return result


@router.get("/{session_id}/messages", response_model=MessageListResponse)
def get_session_messages(
    session_id: str,
    limit: int = 20,
    before: Optional[int] = None,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取会话消息列表

    支持分页加载
    """
    from ..dependencies import TEST_MODE

    if TEST_MODE:
        session = db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()
    else:
        session = db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.user_id == current_user.id
        ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    query = db.query(Message).filter(Message.session_id == session_id)

    if before:
        query = query.filter(Message.id < before)

    messages = query.order_by(Message.created_at.desc()).limit(limit + 1).all()

    has_more = len(messages) > limit
    messages = messages[:limit]
    messages.reverse()

    return MessageListResponse(
        messages=[MessageResponse.model_validate(m) for m in messages],
        has_more=has_more
    )


@router.get("/agents", response_model=Dict[str, Any])
async def list_agents():
    """获取所有可用智能体及其能力"""
    return {
        "general": {
            "display_name": "全科AI医生",
            "description": "全科医疗咨询智能体",
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
            "version": "1.0"
        }
    }


@router.get("/agents/{agent_type}/capabilities", response_model=Dict[str, Any])
async def get_agent_capabilities(agent_type: str):
    """获取指定智能体的能力配置"""
    return {
        "display_name": "全科AI医生",
        "description": "全科医疗咨询智能体",
        "actions": ["conversation"],
        "accepts_media": [],
        "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
        "version": "1.0"
    }
