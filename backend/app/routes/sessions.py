from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, AsyncGenerator, Union
import uuid
import json
import asyncio
from ..database import get_db
from ..schemas.session import SessionCreate, SessionResponse, EnhancedSessionCreate, AgentCapabilitiesResponse
from ..schemas.message import MessageCreate, MessageResponse, MessageListResponse, EnhancedMessageCreate
from ..models.session import Session as SessionModel
from ..models.message import Message, SenderType
from ..models.doctor import Doctor
from ..models.user import User
from ..dependencies import get_current_user
from ..services.qwen_service import QwenService
from ..services.agent_router import AgentRouter

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    request: Union[SessionCreate, EnhancedSessionCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建会话
    
    支持指定智能体类型：
    - agent_type: "general" | "dermatology" | "cardiology" | ...
    - 如果不指定，根据 doctor 的科室自动推断
    """
    doctor = None
    if request.doctor_id:
        doctor = db.query(Doctor).filter(Doctor.id == request.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="医生不存在")

    # 确定智能体类型
    agent_type = getattr(request, 'agent_type', None)
    if not agent_type and doctor:
        # 根据科室自动推断
        dept_name = doctor.department.name if hasattr(doctor, 'department') and doctor.department else ""
        agent_type = AgentRouter.infer_agent_type(dept_name)
    if not agent_type:
        agent_type = "general"
    
    # 验证智能体类型
    if not AgentRouter.is_valid_agent_type(agent_type):
        raise HTTPException(status_code=400, detail=f"不支持的智能体类型: {agent_type}")
    
    # 获取智能体实例
    agent = AgentRouter.get_agent(agent_type)

    session_id = str(uuid.uuid4())
    session = SessionModel(
        id=session_id,
        user_id=current_user.id,
        doctor_id=request.doctor_id,
        agent_type=agent_type,
        agent_state=None
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # 初始化智能体状态
    initial_state = await agent.create_initial_state(
        session_id=session_id,
        user_id=current_user.id
    )
    session.agent_state = initial_state
    db.commit()

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


@router.get("", response_model=List[SessionResponse])
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
def get_messages(
    session_id: str,
    limit: int = 20,
    before: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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


@router.post("/{session_id}/messages")
async def send_message(
    session_id: str,
    request: Union[MessageCreate, EnhancedMessageCreate],
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送消息
    
    支持：
    - content: 文本内容
    - attachments: [{type: "image", url: "...", base64: "..."}]
    - action: "conversation" | "analyze_skin" | "interpret_report" | ...
    - 流式响应（Accept: text/event-stream）
    """
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 获取智能体
    agent_type = session.agent_type or "general"
    try:
        agent = AgentRouter.get_agent(agent_type)
    except ValueError:
        raise HTTPException(status_code=500, detail=f"智能体类型错误: {agent_type}")

    # 解析请求参数
    content = request.content
    attachments = getattr(request, 'attachments', None) or []
    action = getattr(request, 'action', 'conversation') or 'conversation'
    
    # 转换 attachments 为 dict 列表
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
    state = session.agent_state
    print(f"[send_message] 从数据库恢复的 agent_state:")
    print(f"  - agent_state is None: {state is None}")
    if state:
        print(f"  - chief_complaint: {state.get('chief_complaint', '')}")
        print(f"  - skin_location: {state.get('skin_location', '')}")
        print(f"  - questions_asked: {state.get('questions_asked', 0)}")
        print(f"  - stage: {state.get('stage', '')}")
    else:
        print(f"  - 状态为空，将创建新状态")
    
    if not state:
        state = await agent.create_initial_state(session_id, current_user.id)
        print(f"[send_message] 创建了新的初始状态")

    # 检查是否请求流式响应
    accept_header = http_request.headers.get("accept", "")
    want_stream = "text/event-stream" in accept_header

    if want_stream:
        # 预先获取医生信息（避免在生成器中使用已关闭的数据库会话）
        doctor = db.query(Doctor).filter(Doctor.id == session.doctor_id).first() if session.doctor_id else None
        doctor_info = None
        if doctor:
            doctor_info = {
                "name": doctor.name,
                "title": doctor.title if doctor.title else "主治医师",
                "specialty": doctor.specialty if doctor.specialty else "全科医学",
                "persona_prompt": doctor.ai_persona_prompt if hasattr(doctor, 'ai_persona_prompt') else None,
                "model": doctor.ai_model if hasattr(doctor, 'ai_model') else None,
                "temperature": doctor.ai_temperature if hasattr(doctor, 'ai_temperature') else None,
                "max_tokens": doctor.ai_max_tokens if hasattr(doctor, 'ai_max_tokens') else None
            }
        
        return StreamingResponse(
            stream_agent_response(
                agent=agent,
                state=state,
                user_input=content,
                attachments=attachments_data,
                action=action,
                session_id=session.id,
                agent_type=agent_type,
                doctor_info=doctor_info
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
        doctor = db.query(Doctor).filter(Doctor.id == session.doctor_id).first() if session.doctor_id else None
        
        # 准备额外参数
        extra_kwargs = {}
        if agent_type == "general":
            # 通用智能体需要医生信息和历史记录
            history = db.query(Message).filter(
                Message.session_id == session_id
            ).order_by(Message.created_at.desc()).limit(10).all()
            history.reverse()
            history_data = [{"sender": m.sender.value, "content": m.content} for m in history]
            
            rag_context = ""
            if doctor and hasattr(doctor, 'knowledge_base_id') and doctor.knowledge_base_id:
                from ..services.knowledge_service import KnowledgeService
                rag_context = KnowledgeService.get_context_for_query(
                    db, doctor.knowledge_base_id, content
                )
            
            extra_kwargs = {
                "doctor_info": {
                    "name": doctor.name if doctor else "AI助手",
                    "title": doctor.title if doctor else "主治医师",
                    "specialty": doctor.specialty if doctor else "全科医学",
                    "persona_prompt": doctor.ai_persona_prompt if doctor else None,
                    "model": doctor.ai_model if doctor else None,
                    "temperature": doctor.ai_temperature if doctor else None,
                    "max_tokens": doctor.ai_max_tokens if doctor else None
                } if doctor else None,
                "history": history_data,
                "rag_context": rag_context
            }
        
        updated_state = await agent.run(
            state=state,
            user_input=content,
            attachments=attachments_data,
            action=action,
            **extra_kwargs
        )
        
        # 保存 AI 消息
        ai_content = updated_state.get("current_response", "")
        ai_message = Message(
            session_id=session_id,
            sender=SenderType.ai,
            content=ai_content,
            message_type="text",
            structured_data=extract_structured_data(updated_state)
        )
        db.add(ai_message)
        
        # 更新会话
        session.agent_state = updated_state
        session.last_message = ai_content[:100] if ai_content else ""
        db.commit()
        db.refresh(ai_message)
        
        return {
            "user_message": MessageResponse.model_validate(user_message),
            "ai_message": MessageResponse.model_validate(ai_message)
        }


async def stream_agent_response(
    agent,
    state: Dict,
    user_input: str,
    attachments: list,
    action: str,
    session_id: str,  # 改为传 session_id，而不是 session 对象
    agent_type: str,
    doctor_info: Optional[Dict] = None  # 改为传医生信息字典
) -> AsyncGenerator[str, None]:
    """
    生成 SSE 流式响应
    
    注意：由于 FastAPI StreamingResponse 的生命周期问题，
    在生成器内部创建独立的数据库会话来保存状态
    """
    from ..database import SessionLocal  # 导入数据库会话工厂
    
    chunk_queue = asyncio.Queue()
    final_state = None
    error_occurred = None
    
    async def on_chunk(chunk: str):
        await chunk_queue.put(("chunk", chunk))
    
    async def run_agent_task():
        nonlocal final_state, error_occurred
        try:
            # 准备额外参数
            extra_kwargs = {}
            
            if agent_type == "general":
                # 创建独立的数据库会话来查询历史
                db_temp = SessionLocal()
                try:
                    history = db_temp.query(Message).filter(
                        Message.session_id == session_id
                    ).order_by(Message.created_at.desc()).limit(10).all()
                    history.reverse()
                    history_data = [{"sender": m.sender.value, "content": m.content} for m in history]
                finally:
                    db_temp.close()
                
                extra_kwargs = {
                    "doctor_info": doctor_info,
                    "history": history_data,
                    "rag_context": ""  # RAG context 需要在外部预先计算
                }
            
            final_state = await agent.run(
                state=state,
                user_input=user_input,
                attachments=attachments,
                action=action,
                on_chunk=on_chunk,
                **extra_kwargs
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
        "session_id": state.get("session_id", session_id),
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
    elif final_state:
        # 创建独立的数据库会话来保存状态（关键修复！）
        db_save = SessionLocal()
        try:
            # 重新查询 session 对象
            session_obj = db_save.query(SessionModel).filter(
                SessionModel.id == session_id
            ).first()
            
            if session_obj:
                # 保存 AI 消息
                ai_content = final_state.get("current_response", "")
                ai_message = Message(
                    session_id=session_id,
                    sender=SenderType.ai,
                    content=ai_content,
                    message_type="text",
                    structured_data=extract_structured_data(final_state)
                )
                db_save.add(ai_message)
                
                # 更新会话状态
                print(f"[stream_agent_response] 保存状态到数据库:")
                print(f"  - chief_complaint: {final_state.get('chief_complaint', '')}")
                print(f"  - skin_location: {final_state.get('skin_location', '')}")
                print(f"  - questions_asked: {final_state.get('questions_asked', 0)}")
                # === 调试日志：advice_history ===
                adv_state = final_state.get('advice_history')
                print(f"  - advice_history: 类型={type(adv_state).__name__}, 是None={adv_state is None}, 数量={len(adv_state) if adv_state else 0}")
                diag_state = final_state.get('diagnosis_card')
                print(f"  - diagnosis_card: 类型={type(diag_state).__name__}, 是None={diag_state is None}")
                # === 日志结束 ===
                session_obj.agent_state = final_state
                session_obj.last_message = ai_content[:100] if ai_content else ""
                db_save.commit()
                print(f"[stream_agent_response] 数据库 commit 完成")
            else:
                print(f"[stream_agent_response] 错误: 找不到会话 {session_id}")
        except Exception as e:
            print(f"[stream_agent_response] 保存状态时出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db_save.close()
        
        # 发送完成事件
        complete_data = {
            "message": final_state.get("current_response", ""),
            "structured_data": extract_structured_data(final_state),
            "quick_options": final_state.get("quick_options", []),
            # ReAct Agent 增强字段
            "advice_history": final_state.get("advice_history", []),
            "diagnosis_card": final_state.get("diagnosis_card"),
            "knowledge_refs": final_state.get("knowledge_refs", []),
            "reasoning_steps": final_state.get("reasoning_steps", []),
            # 病历事件关联字段
            "event_id": final_state.get("event_id"),
            "is_new_event": final_state.get("is_new_event"),
            "should_show_dossier_prompt": final_state.get("should_show_dossier_prompt", False),
            "stage": final_state.get("stage", "collecting")
        }
        
        # === 调试日志 ===
        print(f"[DEBUG] complete_data 发送给前端:")
        print(f"[DEBUG] - advice_history: {len(complete_data.get('advice_history', []))} 条")
        print(f"[DEBUG] - diagnosis_card: {'有' if complete_data.get('diagnosis_card') else '无'}")
        # === 日志结束 ===
        
        yield f"event: complete\ndata: {json.dumps(complete_data, ensure_ascii=False)}\n\n"


def extract_structured_data(state: Dict) -> Optional[Dict]:
    """从状态中提取结构化数据"""
    # 皮肤分析结果
    if state.get("latest_analysis"):
        return {
            "type": "skin_analysis",
            "data": state["latest_analysis"]
        }
    # 报告解读结果
    if state.get("latest_interpretation"):
        return {
            "type": "report_interpretation",
            "data": state["latest_interpretation"]
        }
    return None


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
