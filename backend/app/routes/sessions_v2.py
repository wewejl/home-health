"""
统一会话接口 V2

使用新的多智能体架构：
- AgentRouterV2 路由器
- BaseAgentV2 基类
- AgentResponse 统一响应格式
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
from typing import List, Optional, Dict, Any, AsyncGenerator, Union
import uuid
import json
import asyncio
from ..database import get_db, SessionLocal
from ..schemas.session import SessionCreate, SessionResponse, EnhancedSessionCreate
from ..schemas.message import MessageCreate, MessageResponse, MessageListResponse, EnhancedMessageCreate
from ..schemas.agent_response import AgentResponse
from ..models.session import Session as SessionModel
from ..models.message import Message, SenderType
from ..models.doctor import Doctor
from ..models.user import User
from ..dependencies import get_current_user
from ..services.agent_router_v2 import AgentRouterV2

router = APIRouter(prefix="/v2/sessions", tags=["sessions-v2"])


@router.post("", response_model=SessionResponse)
async def create_session_v2(
    request: Union[SessionCreate, EnhancedSessionCreate],
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建会话 (V2)
    
    使用新的 AgentRouterV2 架构
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
        agent_type = AgentRouterV2.infer_agent_type(dept_name)
    if not agent_type:
        agent_type = "general"
    
    # 验证智能体类型
    if not AgentRouterV2.is_valid_agent_type(agent_type):
        raise HTTPException(status_code=400, detail=f"不支持的智能体类型: {agent_type}")

    session_id = str(uuid.uuid4())
    session = SessionModel(
        id=session_id,
        user_id=current_user.id,
        doctor_id=request.doctor_id,
        agent_type=agent_type,
        agent_state={}  # V2: 初始状态为空字典
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
async def send_message_v2(
    session_id: str,
    request: Union[MessageCreate, EnhancedMessageCreate],
    http_request: Request,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送消息 (V2)
    
    返回 AgentResponse 统一格式
    """
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 获取 V2 智能体
    agent_type = session.agent_type or "general"
    try:
        agent = AgentRouterV2.get_agent(agent_type)
    except ValueError:
        raise HTTPException(status_code=500, detail=f"智能体类型错误: {agent_type}")

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

    # 检查是否请求流式响应
    accept_header = http_request.headers.get("accept", "")
    want_stream = "text/event-stream" in accept_header

    if want_stream:
        return StreamingResponse(
            stream_agent_response_v2(
                agent=agent,
                state=state,
                user_input=content,
                attachments=attachments_data,
                action=action,
                session_id=session.id,
                agent_type=agent_type
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
        response: AgentResponse = await agent.run(
            state=state,
            user_input=content,
            attachments=attachments_data,
            action=action
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


async def stream_agent_response_v2(
    agent,
    state: Dict,
    user_input: str,
    attachments: list,
    action: str,
    session_id: str,
    agent_type: str
) -> AsyncGenerator[str, None]:
    """
    生成 SSE 流式响应 (V2)
    
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
                on_chunk=on_chunk
            )
        except Exception as e:
            error_occurred = str(e)
            print(f"[stream_agent_response_v2] Error: {e}")
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
            print(f"[stream_agent_response_v2] 保存状态时出错: {e}")
        finally:
            db_save.close()
        
        # 发送完成事件 - AgentResponse 格式
        complete_data = final_response.model_dump()
        yield f"event: complete\ndata: {json.dumps(complete_data, ensure_ascii=False)}\n\n"


@router.get("/agents", response_model=Dict[str, Any])
async def list_agents_v2():
    """获取所有可用智能体及其能力 (V2)"""
    return AgentRouterV2.list_agents()


@router.get("/agents/{agent_type}/capabilities", response_model=Dict[str, Any])
async def get_agent_capabilities_v2(agent_type: str):
    """获取指定智能体的能力配置 (V2)"""
    capabilities = AgentRouterV2.get_capabilities(agent_type)
    if not capabilities:
        raise HTTPException(status_code=404, detail=f"智能体不存在: {agent_type}")
    return capabilities
