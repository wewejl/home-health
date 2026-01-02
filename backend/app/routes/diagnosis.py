"""
AI诊室API路由
"""
import uuid
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, AsyncGenerator

from ..database import get_db
from ..models import DiagnosisSession, User
from ..schemas.diagnosis import (
    StartDiagnosisRequest,
    ContinueDiagnosisRequest,
    DiagnosisResponse,
    DiagnosisSessionListResponse,
    DiagnosisSessionSchema,
    QuickOptionSchema,
    DiseaseSchema,
    RecommendationsSchema
)
from ..services.diagnosis_agent import DiagnosisAgent, create_initial_state
from ..dependencies import get_current_user

router = APIRouter(prefix="/diagnosis", tags=["AI诊室"])


def state_to_db(state: dict, session: DiagnosisSession):
    """将状态同步到数据库模型"""
    session.stage = state.get("stage", "greeting")
    session.progress = state.get("progress", 0)
    session.questions_asked = state.get("questions_asked", 0)
    session.chief_complaint = state.get("chief_complaint", "")
    session.symptoms = state.get("symptoms", [])
    session.symptom_details = state.get("symptom_details", {})
    session.messages = state.get("messages", [])
    session.current_question = state.get("current_question", "")
    session.quick_options = state.get("quick_options", [])
    session.reasoning = state.get("reasoning", "")
    session.possible_diseases = state.get("possible_diseases", [])
    session.risk_level = state.get("risk_level")
    session.recommendations = state.get("recommendations", {})
    session.can_conclude = state.get("can_conclude", False)


def db_to_state(session: DiagnosisSession) -> dict:
    """从数据库模型恢复状态"""
    return {
        "consultation_id": session.id,
        "user_id": session.user_id,
        "stage": session.stage or "greeting",
        "progress": session.progress or 0,
        "questions_asked": session.questions_asked or 0,
        "chief_complaint": session.chief_complaint or "",
        "symptoms": session.symptoms or [],
        "symptom_details": session.symptom_details or {},
        "messages": session.messages or [],
        "current_question": session.current_question or "",
        "quick_options": session.quick_options or [],
        "reasoning": session.reasoning or "",
        "possible_diseases": session.possible_diseases or [],
        "risk_level": session.risk_level or "low",
        "recommendations": session.recommendations or {},
        "can_conclude": session.can_conclude or False,
        "force_conclude": False
    }


def build_response(state: dict) -> DiagnosisResponse:
    """构建API响应"""
    is_diagnosis = state["stage"] == "completed"
    
    response_data = {
        "type": "diagnosis" if is_diagnosis else "question",
        "consultation_id": state["consultation_id"],
        "message": state["current_question"],
        "progress": state["progress"],
        "stage": state["stage"],
    }
    
    if is_diagnosis:
        # 诊断结果
        recommendations = state.get("recommendations", {})
        response_data.update({
            "summary": recommendations.get("summary", ""),
            "diseases": [
                DiseaseSchema(
                    name=d.get("name", ""),
                    probability=d.get("probability", ""),
                    description=d.get("description", "")
                ) for d in state.get("possible_diseases", [])
            ],
            "risk_level": state.get("risk_level", "low"),
            "risk_warning": recommendations.get("risk_warning"),
            "recommendations": RecommendationsSchema(
                summary=recommendations.get("summary"),
                risk_warning=recommendations.get("risk_warning"),
                department=recommendations.get("department"),
                urgency=recommendations.get("urgency"),
                lifestyle=recommendations.get("lifestyle", [])
            ),
            "quick_options": None,
            "can_conclude": None
        })
    else:
        # 问诊问题
        response_data.update({
            "quick_options": [
                QuickOptionSchema(
                    text=opt.get("text", ""),
                    value=opt.get("value", ""),
                    category=opt.get("category", "")
                ) for opt in state.get("quick_options", [])
            ],
            "can_conclude": state.get("can_conclude", False),
            "reasoning": state.get("reasoning", "")
        })
    
    return DiagnosisResponse(**response_data)


@router.post("/start")
async def start_diagnosis(
    request: StartDiagnosisRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    开始AI问诊（支持流式输出）
    
    创建新的问诊会话并返回初始问候语
    如果Accept头包含text/event-stream，返回SSE流式响应
    否则返回普通JSON响应
    """
    consultation_id = str(uuid.uuid4())
    
    # 创建数据库记录
    db_session = DiagnosisSession(
        id=consultation_id,
        user_id=current_user.id,
        stage="greeting",
        progress=0
    )
    db.add(db_session)
    db.commit()  # 立即提交，确保会话记录存在
    db.refresh(db_session)  # 刷新以获取数据库生成的字段
    
    # 创建初始状态
    state = create_initial_state(
        consultation_id=consultation_id,
        user_id=current_user.id,
        chief_complaint=request.chief_complaint or ""
    )
    
    # 检查是否请求流式响应
    accept_header = http_request.headers.get("accept", "")
    want_stream = "text/event-stream" in accept_header
    
    if want_stream:
        # 流式响应
        return StreamingResponse(
            stream_start_diagnosis_response(
                state=state,
                db_session=db_session,
                db=db
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # 普通JSON响应（保持向后兼容）
        agent = DiagnosisAgent()
        state = await agent.run(state)
        
        # 同步到数据库
        state_to_db(state, db_session)
        db.commit()
        
        return build_response(state)


async def stream_start_diagnosis_response(
    state: dict,
    db_session: DiagnosisSession,
    db: Session
) -> AsyncGenerator[str, None]:
    """
    生成开始问诊的SSE流式响应
    
    事件类型:
    - event:meta - 初始元数据（consultation_id, stage等）
    - event:chunk - 文本片段
    - event:complete - 完成，包含完整的DiagnosisResponse
    - event:error - 错误信息
    """
    chunk_queue = asyncio.Queue()
    final_state = None
    error_occurred = None
    
    async def on_chunk(chunk: str):
        """SSE chunk回调"""
        await chunk_queue.put(("chunk", chunk))
    
    async def run_agent():
        """运行智能体"""
        nonlocal final_state, error_occurred
        try:
            agent = DiagnosisAgent()
            final_state = await agent.run(
                state,
                on_chunk=on_chunk
            )
            # 同步到数据库
            state_to_db(final_state, db_session)
            db.commit()
        except Exception as e:
            error_occurred = str(e)
        finally:
            await chunk_queue.put(("done", None))
    
    # 启动智能体任务
    agent_task = asyncio.create_task(run_agent())
    
    # 发送初始元数据
    meta_data = {
        "consultation_id": state["consultation_id"],
        "stage": state["stage"],
        "progress": state["progress"]
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
    
    # 等待任务完成
    await agent_task
    
    # 发送最终结果或错误
    if error_occurred:
        error_data = {"error": error_occurred}
        yield f"event: error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    elif final_state:
        response = build_response(final_state)
        response_dict = response.model_dump()
        yield f"event: complete\ndata: {json.dumps(response_dict, ensure_ascii=False)}\n\n"


@router.post("/{consultation_id}/continue")
async def continue_diagnosis(
    consultation_id: str,
    request: ContinueDiagnosisRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    继续AI问诊（支持流式输出）
    
    发送用户消息并获取AI回复
    如果Accept头包含text/event-stream，返回SSE流式响应
    否则返回普通JSON响应
    """
    # 获取会话
    db_session = db.query(DiagnosisSession).filter(
        DiagnosisSession.id == consultation_id,
        DiagnosisSession.user_id == current_user.id
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="问诊会话不存在")
    
    if db_session.stage == "completed":
        raise HTTPException(status_code=400, detail="问诊已完成")
    
    # 恢复状态
    state = db_to_state(db_session)
    
    # 使用传入的历史记录覆盖状态
    state["messages"] = [
        {
            "role": msg.role,
            "content": msg.message,
            "timestamp": msg.timestamp
        }
        for msg in request.history
    ]
    state["questions_asked"] = sum(1 for msg in request.history if msg.role == "user")
    
    user_message = request.current_input.message
    
    # 检查是否请求流式响应
    accept_header = http_request.headers.get("accept", "")
    want_stream = "text/event-stream" in accept_header
    
    if want_stream:
        # 流式响应
        return StreamingResponse(
            stream_diagnosis_response(
                state=state,
                user_message=user_message,
                force_conclude=request.force_conclude,
                db_session=db_session,
                db=db
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # 普通JSON响应（保持向后兼容）
        agent = DiagnosisAgent()
        state = await agent.run(
            state,
            user_input=user_message,
            force_conclude=request.force_conclude
        )
        # 同步到数据库
        state_to_db(state, db_session)
        db.commit()
        
        return build_response(state)


async def stream_diagnosis_response(
    state: dict,
    user_message: str,
    force_conclude: bool,
    db_session: DiagnosisSession,
    db: Session
) -> AsyncGenerator[str, None]:
    """
    生成SSE流式响应
    
    事件类型:
    - event:meta - 初始元数据（progress, stage等）
    - event:chunk - 文本片段
    - event:complete - 完成，包含完整的DiagnosisResponse
    - event:error - 错误信息
    """
    chunk_queue = asyncio.Queue()
    final_state = None
    error_occurred = None
    
    async def on_chunk(chunk: str):
        """SSE chunk回调"""
        await chunk_queue.put(("chunk", chunk))
    
    async def run_agent():
        """运行智能体"""
        nonlocal final_state, error_occurred
        try:
            agent = DiagnosisAgent()
            final_state = await agent.run(
                state,
                user_input=user_message,
                force_conclude=force_conclude,
                on_chunk=on_chunk
            )
            # 同步到数据库
            state_to_db(final_state, db_session)
            db.commit()
        except Exception as e:
            error_occurred = str(e)
        finally:
            await chunk_queue.put(("done", None))
    
    # 启动智能体任务
    agent_task = asyncio.create_task(run_agent())
    
    # 发送初始元数据
    meta_data = {
        "consultation_id": state["consultation_id"],
        "stage": state["stage"],
        "progress": state["progress"]
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
    
    # 等待任务完成
    await agent_task
    
    # 发送最终结果或错误
    if error_occurred:
        error_data = {"error": error_occurred}
        yield f"event: error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    elif final_state:
        response = build_response(final_state)
        response_dict = response.model_dump()
        yield f"event: complete\ndata: {json.dumps(response_dict, ensure_ascii=False)}\n\n"


@router.get("/{consultation_id}", response_model=DiagnosisResponse)
async def get_diagnosis_session(
    consultation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取问诊会话详情
    """
    db_session = db.query(DiagnosisSession).filter(
        DiagnosisSession.id == consultation_id,
        DiagnosisSession.user_id == current_user.id
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="问诊会话不存在")
    
    state = db_to_state(db_session)
    return build_response(state)


@router.get("", response_model=DiagnosisSessionListResponse)
async def list_diagnosis_sessions(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的问诊会话列表
    """
    query = db.query(DiagnosisSession).filter(
        DiagnosisSession.user_id == current_user.id
    ).order_by(DiagnosisSession.updated_at.desc())
    
    total = query.count()
    sessions = query.offset(offset).limit(limit).all()
    
    return DiagnosisSessionListResponse(
        sessions=[
            DiagnosisSessionSchema(
                consultation_id=s.id,
                stage=s.stage,
                progress=s.progress,
                chief_complaint=s.chief_complaint,
                created_at=s.created_at,
                updated_at=s.updated_at
            ) for s in sessions
        ],
        total=total
    )


@router.delete("/{consultation_id}")
async def delete_diagnosis_session(
    consultation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除问诊会话
    """
    db_session = db.query(DiagnosisSession).filter(
        DiagnosisSession.id == consultation_id,
        DiagnosisSession.user_id == current_user.id
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="问诊会话不存在")
    
    db.delete(db_session)
    db.commit()
    
    return {"message": "删除成功"}
