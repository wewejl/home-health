"""
统一会话接口

使用多智能体架构：
- AgentRouter 路由器（agents/router.py）
- ReActAgent 基类（agents/react_base.py）
- AgentResponse 统一响应格式
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
from ..services.agents.router import AgentRouter
from ..services.ai_gateway import (
    AIGatewayClient,
    AIGatewayClientError,
    build_chat_respond_request,
    build_history_from_db_messages,
)
from ..config import get_settings
from ..agentic import AgenticConsultOrchestrator
from ..triage import TriageOrchestrator

router = APIRouter(prefix="/sessions", tags=["sessions"])
settings = get_settings()
logger = logging.getLogger(__name__)


def migrate_legacy_state(legacy_state: Optional[Dict]) -> Dict:
    """
    将旧版本状态转换为新格式

    旧版本字段 -> 新版本字段映射：
    - questions_asked -> 删除（新版本不需要）
    - session_id -> 删除（新版本从 session 对象获取）
    - user_id -> 删除（新版本从 session 对象获取）
    - stage -> 保留（新版本也使用）
    - chief_complaint -> 保留（新版本也使用）
    - symptoms -> 保留
    - skin_location -> 保留
    - diagnosis_card -> 保留
    - advice_history -> 保留
    """
    if not legacy_state:
        return {}

    # 处理 JSON 字符串情况（旧版本可能存成字符串）
    if isinstance(legacy_state, str):
        try:
            legacy_state = json.loads(legacy_state)
        except:
            return {}

    # 新导诊引擎状态：直接保留，避免多轮对话关键槽位被误删
    triage_markers = {
        "specialty", "symptom_slots", "missing_slots", "turn_index",
        "risk_level", "disposition", "_triage_audit",
    }
    if any(marker in legacy_state for marker in triage_markers):
        return dict(legacy_state)

    # agentic 引擎状态：直接保留（完整会话上下文）
    agentic_markers = {
        "agentic_engine", "agentic_last_plan", "agentic_last_evidence",
    }
    if any(marker in legacy_state for marker in agentic_markers):
        return dict(legacy_state)

    # 旧版本需要保留的状态字段
    # 🆕 新增：保留 messages（对话历史）和思考相关字段
    valid_fields = {
        "stage", "chief_complaint", "symptoms",
        "skin_location", "diagnosis_card", "advice_history",
        "knowledge_refs", "reasoning_steps", "latest_analysis",
        "latest_interpretation", "current_response",
        # 🆕 新增：保留对话历史和思考追踪
        "messages", "current_thought", "reasoning_history",
        "show_thinking", "asked_questions",
        # 保留其他可能需要的字段
        "iteration_count", "agent_decision", "medical_context"
    }

    return {k: v for k, v in legacy_state.items() if k in valid_fields}


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
    # 注意：此处存在轻微竞态条件（读取-检查-写入非原子），
    # 但可接受的权衡：极少数并发请求可能重复调用，远比引入分布式锁的复杂性更低
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


def _shadow_task_done_callback(task: asyncio.Task) -> None:
    try:
        task.result()
    except Exception as exc:  # noqa: BLE001
        logger.warning("hybrid_shadow task failed: %s", exc)


async def _run_remote_ai_shadow_turn(
    *,
    session_id: str,
    user_id: int,
    agent_type: str,
    content: str,
    attachments_data: List[Dict[str, Any]],
    debug_mode: bool,
    request_headers: Dict[str, str],
) -> None:
    db_shadow = SessionLocal()
    try:
        session = db_shadow.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()
        if not session:
            return

        base_state = migrate_legacy_state(session.agent_state)
        # lightweight request-like accessor
        class _ShadowRequest:
            def __init__(self, headers: Dict[str, str]):
                self.headers = headers

        pseudo_request = _ShadowRequest(request_headers)

        response = await _run_remote_ai_turn(
            session=session,
            db=db_shadow,
            base_state=base_state,
            content=content,
            attachments_data=attachments_data,
            debug_mode=debug_mode,
            http_request=pseudo_request,  # type: ignore[arg-type]
            user_id=user_id,
            agent_type=agent_type,
        )

        merged_state = dict(session.agent_state or {})
        merged_state["remote_ai_shadow_last"] = {
            "message": response.message,
            "risk_level": response.risk_level,
            "quick_options": response.quick_options,
            "specialty_data": response.specialty_data,
            "captured_at_turn": int(base_state.get("turn_index", 0)) + 1,
        }
        session.agent_state = merged_state
        db_shadow.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("hybrid_shadow execution failed: %s", exc)
    finally:
        db_shadow.close()


@router.post("", response_model=SessionResponse)
async def create_session(
    request: Union[SessionCreate, EnhancedSessionCreate],
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建会话

    使用科室智能体架构
    """
    doctor = None

    if request.doctor_id:
        doctor = db.query(Doctor).filter(Doctor.id == request.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="医生不存在")

    # 确定智能体类型
    agent_type = getattr(request, 'agent_type', None)
    if not agent_type and doctor:
        dept_name = doctor.department.name if hasattr(doctor, 'department') and doctor.department else ""
        agent_type = AgentRouter.infer_agent_type(dept_name)
    if not agent_type:
        agent_type = "general"

    # 验证智能体类型
    if not AgentRouter.is_valid_agent_type(agent_type):
        raise HTTPException(status_code=400, detail=f"不支持的智能体类型: {agent_type}")

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
        doctor_name=doctor.name if doctor else "AI助手",
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
    # 测试模式：不检查 user_id，直接根据 session_id 查询
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

    # 获取会话智能体类型
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

    # 恢复智能体状态（使用状态转换函数兼容旧会话）
    state = migrate_legacy_state(session.agent_state)
    # 注入会话元数据（新导诊引擎需要；对旧智能体无副作用）
    state["session_id"] = session.id
    state["user_id"] = current_user.id
    state["agent_type"] = agent_type

    # 检查是否请求流式响应
    accept_header = http_request.headers.get("accept", "")
    want_stream = "text/event-stream" in accept_header
    debug_mode = http_request.query_params.get("debug", "false").lower() in {"1", "true", "yes", "on"}

    if settings.ai_engine_mode == "hybrid_shadow":
        shadow_headers = {k.lower(): v for k, v in http_request.headers.items()}
        shadow_task = asyncio.create_task(
            _run_remote_ai_shadow_turn(
                session_id=session.id,
                user_id=current_user.id,
                agent_type=agent_type,
                content=content,
                attachments_data=attachments_data,
                debug_mode=debug_mode,
                request_headers=shadow_headers,
            )
        )
        shadow_task.add_done_callback(_shadow_task_done_callback)

    # 新架构：转发到独立 AI 后端
    if settings.ai_engine_mode == "remote_ai":
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
        except Exception as exc:  # noqa: BLE001
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

    # 旧架构：旧智能体 / 导诊引擎 / agentic 引擎
    agentic_enabled = (
        settings.USE_AGENTIC_ENGINE
        and agent_type in settings.agentic_enabled_specialties_list
    )
    triage_enabled = (
        settings.USE_TRIAGE_ENGINE
        and agent_type in settings.triage_enabled_specialties_list
    )
    if agentic_enabled:
        agent = AgenticConsultOrchestrator()
    elif triage_enabled:
        agent = TriageOrchestrator()
    else:
        try:
            agent = AgentRouter.get_agent(agent_type)
        except ValueError:
            raise HTTPException(status_code=500, detail=f"智能体类型错误: {agent_type}")

    if want_stream:
        return StreamingResponse(
            stream_agent_response(
                agent=agent,
                state=state,
                user_input=content,
                attachments=attachments_data,
                action=action,
                session_id=session.id,
                agent_type=agent_type,
                db_session=db,
                debug=debug_mode,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # 非流式响应
        try:
            response: AgentResponse = await agent.run(
                state=state,
                user_input=content,
                attachments=attachments_data,
                action=action,
                debug=debug_mode,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("agent run failed: %s", exc)
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
            structured_data=response.specialty_data
        )
        db.add(ai_message)
        
        # 更新会话状态
        session.agent_state = response.next_state
        session.last_message = response.message[:100] if response.message else ""
        db.commit()
        db.refresh(ai_message)
        
        # 返回 AgentResponse 格式
        return response.model_dump()


async def stream_agent_response(
    agent,
    state: Dict,
    user_input: str,
    attachments: list,
    action: str,
    session_id: str,
    agent_type: str,
    db_session: Optional[DBSession] = None,
    debug: bool = False,
) -> AsyncGenerator[str, None]:
    """
    生成 SSE 流式响应

    返回 AgentResponse 统一格式
    """
    chunk_queue = asyncio.Queue()
    final_response: Optional[AgentResponse] = None
    error_occurred = None
    
    async def on_chunk(chunk: str):
        await chunk_queue.put(("chunk", chunk))
    
    async def run_agent_task():
        nonlocal final_response, error_occurred
        try:
            final_response = await agent.run(
                state=state,
                user_input=user_input,
                attachments=attachments,
                action=action,
                on_chunk=on_chunk,
                debug=debug,
            )
        except Exception as e:
            error_occurred = str(e)
            print(f"[stream_agent_response] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await chunk_queue.put(("done", None))
    
    agent_task = asyncio.create_task(run_agent_task())
    
    # 发送初始元数据
    meta_data = {
        "session_id": session_id,
        "agent_type": agent_type
    }
    yield f"event: meta\ndata: {json.dumps(meta_data, ensure_ascii=False)}\n\n"
    
    # 流式输出 chunks
    while True:
        event_type, data = await chunk_queue.get()
        if event_type == "done":
            break
        elif event_type == "chunk":
            chunk_data = {"text": data}
            yield f"event: chunk\ndata: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
    
    await agent_task
    
    if error_occurred:
        error_data = {"error": error_occurred}
        yield f"event: error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    elif final_response:
        # 保存到数据库
        db_save = SessionLocal()
        try:
            session_obj = db_save.query(SessionModel).filter(
                SessionModel.id == session_id
            ).first()
            
            if session_obj:
                # 保存 AI 消息
                ai_message = Message(
                    session_id=session_id,
                    sender=SenderType.ai,
                    content=final_response.message,
                    message_type="text",
                    structured_data=final_response.specialty_data
                )
                db_save.add(ai_message)
                
                # 更新会话状态
                session_obj.agent_state = final_response.next_state
                session_obj.last_message = final_response.message[:100] if final_response.message else ""
                db_save.commit()
        except Exception as e:
            print(f"[stream_agent_response] 保存状态时出错: {e}")
        finally:
            db_save.close()
        
        # 发送完成事件 - AgentResponse 格式
        complete_data = final_response.model_dump()
        yield f"event: complete\ndata: {json.dumps(complete_data, ensure_ascii=False)}\n\n"


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
            doctor_name=doctor.name if doctor else "AI助手",
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
    return AgentRouter.list_agents()


@router.get("/agents/{agent_type}/capabilities", response_model=Dict[str, Any])
async def get_agent_capabilities(agent_type: str):
    """获取指定智能体的能力配置"""
    capabilities = AgentRouter.get_capabilities(agent_type)
    if not capabilities:
        raise HTTPException(status_code=404, detail=f"智能体不存在: {agent_type}")
    return capabilities
