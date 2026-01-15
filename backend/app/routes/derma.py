"""
皮肤科AI智能体API路由
支持：皮肤影像分析、报告解读、智能问诊对话
"""
import uuid
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, AsyncGenerator

from ..database import get_db
from ..models import DermaSession, User
from ..schemas.derma import (
    StartDermaSessionRequest,
    ContinueDermaRequest,
    DermaResponse,
    DermaSessionListResponse,
    DermaSessionSchema,
    DermaQuickOptionSchema,
    SkinAnalysisResultSchema,
    SkinConditionSchema,
    ReportInterpretationSchema,
    ReportIndicatorSchema
)
from ..services.dermatology import DermaAgentWrapper
from ..services.dermatology.derma_agent import DermaTaskType
from ..services.dermatology.react_state import create_react_initial_state
from ..dependencies import get_current_user_or_admin
from ..models.medical_event import MedicalEvent, EventStatus, AgentType

router = APIRouter(prefix="/derma", tags=["皮肤科AI"])


def auto_aggregate_to_event(session_id: str, user_id: int, db: Session) -> dict:
    """
    自动聚合会话到病历事件
    
    规则：
    1. 同一天同科室归并到现有事件
    2. 不同天或不同科室创建新事件
    """
    from datetime import datetime
    
    # 获取皮肤科会话信息
    session = db.query(DermaSession).filter(DermaSession.id == session_id).first()
    if not session:
        raise ValueError(f"会话不存在: {session_id}")
    
    department = "皮肤科"
    agent_type = AgentType.DERMA
    chief_complaint = session.chief_complaint or ""
    
    session_data = {
        "session_id": session.id,
        "session_type": "derma",
        "timestamp": session.created_at.isoformat() if session.created_at else datetime.now().isoformat(),
        "summary": f"皮肤问诊 - {chief_complaint}" if chief_complaint else "皮肤问诊",
        "risk_level": session.risk_level,
        "stage": session.stage
    }
    
    # 查找当天同科室的现有事件
    today = datetime.utcnow().date()
    existing_event = db.query(MedicalEvent).filter(
        MedicalEvent.user_id == user_id,
        MedicalEvent.agent_type == agent_type,
        MedicalEvent.status == EventStatus.ACTIVE,
        MedicalEvent.start_time >= datetime.combine(today, datetime.min.time())
    ).first()
    
    is_new_event = False
    
    if existing_event:
        # 添加到现有事件（避免重复添加）
        sessions_list = existing_event.sessions or []
        if not any(s.get("session_id") == session_id for s in sessions_list):
            sessions_list.append(session_data)
            existing_event.sessions = sessions_list
            existing_event.session_count = len(sessions_list)
            db.commit()
        event = existing_event
    else:
        # 创建新事件
        title = f"{department} {chief_complaint} {today.strftime('%Y-%m-%d')}" if chief_complaint else f"{department} {today.strftime('%Y-%m-%d')}"
        event = MedicalEvent(
            user_id=user_id,
            title=title,
            department=department,
            agent_type=agent_type,
            chief_complaint=chief_complaint,
            status=EventStatus.ACTIVE,
            sessions=[session_data],
            session_count=1
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        is_new_event = True
    
    return {
        "event_id": event.id,
        "is_new_event": is_new_event,
        "message": "会话已聚合到病历事件"
    }


def state_to_db(state: dict, session: DermaSession):
    """将状态同步到数据库模型"""
    session.stage = state.get("stage", "greeting")
    session.progress = state.get("progress", 0)
    session.questions_asked = state.get("questions_asked", 0)
    session.chief_complaint = state.get("chief_complaint", "")
    session.symptoms = state.get("symptoms", [])
    session.symptom_details = state.get("symptom_details", {})
    session.skin_location = state.get("skin_location", "")
    session.duration = state.get("duration", "")
    session.messages = state.get("messages", [])
    session.current_response = state.get("current_response", "")
    session.quick_options = state.get("quick_options", [])
    session.skin_analyses = state.get("skin_analyses", [])
    session.latest_analysis = state.get("latest_analysis")
    session.report_interpretations = state.get("report_interpretations", [])
    session.latest_interpretation = state.get("latest_interpretation")
    session.possible_conditions = state.get("possible_conditions", [])
    session.risk_level = state.get("risk_level", "low")
    session.care_advice = state.get("care_advice", "")
    session.need_offline_visit = state.get("need_offline_visit", False)
    session.current_task = state.get("current_task", "conversation")
    session.awaiting_image = state.get("awaiting_image", False)


def db_to_state(session: DermaSession) -> dict:
    """从数据库模型恢复状态"""
    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "stage": session.stage or "greeting",
        "progress": session.progress or 0,
        "questions_asked": session.questions_asked or 0,
        "chief_complaint": session.chief_complaint or "",
        "symptoms": session.symptoms or [],
        "symptom_details": session.symptom_details or {},
        "skin_location": session.skin_location or "",
        "duration": session.duration or "",
        "messages": session.messages or [],
        "current_response": session.current_response or "",
        "quick_options": session.quick_options or [],
        "skin_analyses": session.skin_analyses or [],
        "latest_analysis": session.latest_analysis,
        "report_interpretations": session.report_interpretations or [],
        "latest_interpretation": session.latest_interpretation,
        "possible_conditions": session.possible_conditions or [],
        "risk_level": session.risk_level or "low",
        "care_advice": session.care_advice or "",
        "need_offline_visit": session.need_offline_visit or False,
        "current_task": session.current_task or DermaTaskType.CONVERSATION,
        "awaiting_image": session.awaiting_image or False
    }


def build_response(state: dict) -> DermaResponse:
    """构建API响应"""
    task_type = state.get("current_task", DermaTaskType.CONVERSATION)
    if isinstance(task_type, DermaTaskType):
        task_type = task_type.value
    
    response_data = {
        "type": task_type,
        "session_id": state["session_id"],
        "message": state["current_response"],
        "progress": state.get("progress", 0),  # ReAct 模式没有 progress
        "stage": state.get("stage", "conversation"),  # ReAct 模式没有固定 stage
        "awaiting_image": state.get("awaiting_image", False),
        "quick_options": [
            DermaQuickOptionSchema(
                text=opt.get("text", ""),
                value=opt.get("value", ""),
                category=opt.get("category", "")
            ) for opt in state.get("quick_options", [])
        ],
        "risk_level": state.get("risk_level"),
        "need_offline_visit": state.get("need_offline_visit"),
        "care_advice": state.get("care_advice"),
        # 病历事件关联字段
        "event_id": state.get("event_id"),
        "is_new_event": state.get("is_new_event"),
        "should_show_dossier_prompt": state.get("should_show_dossier_prompt", False)
    }
    
    # 添加皮肤分析结果
    if state.get("latest_analysis"):
        analysis = state["latest_analysis"]
        response_data["skin_analysis"] = SkinAnalysisResultSchema(
            lesion_description=analysis.get("lesion_description", ""),
            possible_conditions=[
                SkinConditionSchema(
                    name=c.get("name", ""),
                    confidence=c.get("confidence", 0.0),
                    description=c.get("description", "")
                ) for c in analysis.get("possible_conditions", [])
            ],
            risk_level=analysis.get("risk_level", "medium"),
            care_advice=analysis.get("care_advice", ""),
            need_offline_visit=analysis.get("need_offline_visit", True),
            visit_urgency=analysis.get("visit_urgency"),
            additional_questions=analysis.get("additional_questions", [])
        )
    
    # 添加报告解读结果
    if state.get("latest_interpretation"):
        interp = state["latest_interpretation"]
        response_data["report_interpretation"] = ReportInterpretationSchema(
            report_type=interp.get("report_type", ""),
            report_date=interp.get("report_date"),
            indicators=[
                ReportIndicatorSchema(
                    name=ind.get("name", ""),
                    value=ind.get("value", ""),
                    reference_range=ind.get("reference_range"),
                    status=ind.get("status", "normal"),
                    explanation=ind.get("explanation")
                ) for ind in interp.get("indicators", [])
            ],
            summary=interp.get("summary", ""),
            abnormal_findings=interp.get("abnormal_findings", []),
            health_advice=interp.get("health_advice", []),
            need_follow_up=interp.get("need_follow_up", False),
            follow_up_suggestion=interp.get("follow_up_suggestion")
        )
    
    return DermaResponse(**response_data)


@router.post("/start")
async def start_derma_session(
    request: StartDermaSessionRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user_or_admin),
    db: Session = Depends(get_db)
):
    """
    开始皮肤科问诊会话（支持流式输出）
    """
    session_id = str(uuid.uuid4())
    
    # 创建数据库记录
    db_session = DermaSession(
        id=session_id,
        user_id=current_user.id,
        stage="greeting",
        progress=0
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # 创建初始状态
    state = create_react_initial_state(
        session_id=session_id,
        user_id=current_user.id
    )
    if request.chief_complaint:
        state["chief_complaint"] = request.chief_complaint
    
    # 检查是否请求流式响应
    accept_header = http_request.headers.get("accept", "")
    want_stream = "text/event-stream" in accept_header
    
    if want_stream:
        return StreamingResponse(
            stream_derma_response(
                state=state,
                session_id=session_id
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        agent = DermaAgentWrapper()
        state = await agent.run(state)
        state_to_db(state, db_session)
        db.commit()
        return build_response(state)


async def stream_derma_response(
    state: dict,
    session_id: str,  # 改为传 session_id，而不是 db_session 对象
    user_input: str = None,
    image_url: str = None,
    image_base64: str = None,
    task_type: DermaTaskType = None
) -> AsyncGenerator[str, None]:
    """
    生成SSE流式响应
    
    注意：由于 FastAPI StreamingResponse 的生命周期问题，
    在生成器内部创建独立的数据库会话来保存状态
    """
    from ..database import SessionLocal  # 导入数据库会话工厂
    
    chunk_queue = asyncio.Queue()
    final_state = None
    error_occurred = None
    
    async def on_chunk(chunk: str):
        await chunk_queue.put(("chunk", chunk))
    
    async def on_step(step_type: str, content: str):
        """处理 CrewAI 步骤回调"""
        await chunk_queue.put(("step", {"type": step_type, "content": content}))
    
    async def run_agent():
        nonlocal final_state, error_occurred
        try:
            agent = DermaAgentWrapper()
            final_state = await agent.run(
                state,
                user_input=user_input,
                attachments=[{"type": "image", "url": image_url, "base64": image_base64}] if image_url or image_base64 else None,
                action=task_type.value if task_type else "conversation",
                on_chunk=on_chunk
            )
        except Exception as e:
            error_occurred = str(e)
            print(f"[stream_derma_response] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await chunk_queue.put(("done", None))
    
    agent_task = asyncio.create_task(run_agent())
    
    # 发送初始元数据
    meta_data = {
        "session_id": state["session_id"],
        "stage": state["stage"],
        "progress": state["progress"]
    }
    yield f"event: meta\ndata: {json.dumps(meta_data, ensure_ascii=False)}\n\n"
    
    # 流式输出chunks和steps
    while True:
        event_type, data = await chunk_queue.get()
        if event_type == "done":
            break
        elif event_type == "chunk":
            chunk_data = {"text": data}
            yield f"event: chunk\ndata: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
        elif event_type == "step":
            # 发送思考过程步骤
            yield f"event: step\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    await agent_task
    
    if error_occurred:
        error_data = {"error": error_occurred}
        yield f"event: error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    elif final_state:
        # 创建独立的数据库会话来保存状态（关键修复！）
        db_save = SessionLocal()
        try:
            # 重新查询 session 对象
            db_session = db_save.query(DermaSession).filter(
                DermaSession.id == session_id
            ).first()
            
            if db_session:
                print(f"[stream_derma_response] 保存状态到数据库:")
                print(f"  - chief_complaint: {final_state.get('chief_complaint', '')}")
                print(f"  - skin_location: {final_state.get('skin_location', '')}")
                print(f"  - questions_asked: {final_state.get('questions_asked', 0)}")
                print(f"  - stage: {final_state.get('stage', '')}")
                state_to_db(final_state, db_session)
                db_save.commit()
                print(f"[stream_derma_response] 数据库 commit 完成")
                
                # 对话结束时自动聚合到病历事件
                if final_state.get("stage") == "completed" or final_state.get("should_show_dossier_prompt"):
                    print(f"[stream_derma_response] 对话完成，自动聚合到病历事件...")
                    try:
                        aggregate_result = auto_aggregate_to_event(
                            session_id=session_id,
                            user_id=db_session.user_id,
                            db=db_save
                        )
                        final_state["event_id"] = aggregate_result.get("event_id")
                        final_state["is_new_event"] = aggregate_result.get("is_new_event", False)
                        final_state["should_show_dossier_prompt"] = True
                        print(f"[stream_derma_response] 病历事件聚合成功: event_id={aggregate_result.get('event_id')}, is_new={aggregate_result.get('is_new_event')}")
                    except Exception as agg_err:
                        print(f"[stream_derma_response] 病历事件聚合失败: {agg_err}")
                        # 聚合失败不阻塞对话，仅记录日志
            else:
                print(f"[stream_derma_response] 错误: 找不到会话 {session_id}")
        except Exception as e:
            print(f"[stream_derma_response] 保存状态时出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db_save.close()
        
        response = build_response(final_state)
        response_dict = response.model_dump()
        yield f"event: complete\ndata: {json.dumps(response_dict, ensure_ascii=False)}\n\n"


@router.post("/{session_id}/continue")
async def continue_derma_session(
    session_id: str,
    request: ContinueDermaRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user_or_admin),
    db: Session = Depends(get_db)
):
    """
    继续皮肤科问诊（统一接口，支持流式输出）
    
    支持三种任务类型：
    - conversation: 纯文本问诊对话
    - skin_analysis: 皮肤影像分析（需提供 image_url 或 image_base64）
    - report_interpret: 报告解读（需提供 image_url 或 image_base64，可选 report_type）
    
    请求体示例（JSON）：
    ```json
    {
        "history": [...],
        "current_input": {"message": "请帮我分析这张皮肤照片"},
        "task_type": "skin_analysis",
        "image_base64": "data:image/jpeg;base64,/9j/4AAQ..."
    }
    ```
    """
    db_session = db.query(DermaSession).filter(
        DermaSession.id == session_id,
        DermaSession.user_id == current_user.id
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 解析参数
    task_type = DermaTaskType(request.task_type) if request.task_type else DermaTaskType.CONVERSATION
    image_url = request.image_url
    image_base64 = request.image_base64
    
    # 验证图像参数
    if task_type in [DermaTaskType.SKIN_ANALYSIS, DermaTaskType.REPORT_INTERPRET]:
        if not image_url and not image_base64:
            task_name = "皮肤影像分析" if task_type == DermaTaskType.SKIN_ANALYSIS else "报告解读"
            raise HTTPException(
                status_code=400, 
                detail=f"{task_name}需要提供图像，请传入 image_url 或 image_base64"
            )
    
    # 恢复状态（包含所有累积的结构化信息）
    state = db_to_state(db_session)
    
    print(f"[continue_derma_session] 从数据库恢复的状态:")
    print(f"  - chief_complaint: {state.get('chief_complaint', '')}")
    print(f"  - skin_location: {state.get('skin_location', '')}")
    print(f"  - duration: {state.get('duration', '')}")
    print(f"  - symptoms: {state.get('symptoms', [])}")
    print(f"  - questions_asked (from DB): {state.get('questions_asked', 0)}")
    
    # 使用传入的历史记录更新消息（用于 Agent 上下文）
    state["messages"] = [
        {
            "role": msg.role,
            "content": msg.message,
            "timestamp": msg.timestamp
        }
        for msg in request.history
    ]
    
    # ⚠️ 重要：保持数据库中的 questions_asked，不要用前端历史重新计算
    # 数据库中的值是权威的，因为它跟踪了所有对话轮次
    # 前端可能只传了最近几条消息，不能作为计数依据
    print(f"[continue_derma_session] 保持数据库中的追问轮次: {state.get('questions_asked', 0)}")
    
    user_message = request.current_input.message
    
    # 检查是否请求流式响应
    accept_header = http_request.headers.get("accept", "")
    want_stream = "text/event-stream" in accept_header
    
    if want_stream:
        return StreamingResponse(
            stream_derma_response(
                state=state,
                session_id=session_id,
                user_input=user_message,
                image_url=image_url,
                image_base64=image_base64,
                task_type=task_type
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        agent = DermaAgentWrapper()
        state = await agent.run(
            state,
            user_input=user_message,
            attachments=[{"type": "image", "url": image_url, "base64": image_base64}] if image_url or image_base64 else None,
            action=task_type.value if task_type else "conversation"
        )
        state_to_db(state, db_session)
        db.commit()
        
        # 对话结束时自动聚合到病历事件
        if state.get("stage") == "completed" or state.get("should_show_dossier_prompt"):
            try:
                aggregate_result = auto_aggregate_to_event(
                    session_id=session_id,
                    user_id=current_user.id,
                    db=db
                )
                state["event_id"] = aggregate_result.get("event_id")
                state["is_new_event"] = aggregate_result.get("is_new_event", False)
                state["should_show_dossier_prompt"] = True
                print(f"[continue_derma_session] 病历事件聚合成功: event_id={aggregate_result.get('event_id')}")
            except Exception as agg_err:
                print(f"[continue_derma_session] 病历事件聚合失败: {agg_err}")
        
        return build_response(state)


@router.get("/{session_id}", response_model=DermaResponse)
async def get_derma_session(
    session_id: str,
    current_user: User = Depends(get_current_user_or_admin),
    db: Session = Depends(get_db)
):
    """获取皮肤科会话详情"""
    db_session = db.query(DermaSession).filter(
        DermaSession.id == session_id,
        DermaSession.user_id == current_user.id
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    state = db_to_state(db_session)
    return build_response(state)


@router.get("", response_model=DermaSessionListResponse)
async def list_derma_sessions(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user_or_admin),
    db: Session = Depends(get_db)
):
    """获取皮肤科会话列表"""
    query = db.query(DermaSession).filter(
        DermaSession.user_id == current_user.id
    ).order_by(DermaSession.updated_at.desc())
    
    total = query.count()
    sessions = query.offset(offset).limit(limit).all()
    
    return DermaSessionListResponse(
        sessions=[
            DermaSessionSchema(
                session_id=s.id,
                stage=s.stage,
                progress=s.progress,
                chief_complaint=s.chief_complaint,
                has_skin_analysis=bool(s.skin_analyses),
                has_report_interpretation=bool(s.report_interpretations),
                created_at=s.created_at,
                updated_at=s.updated_at
            ) for s in sessions
        ],
        total=total
    )


@router.delete("/{session_id}")
async def delete_derma_session(
    session_id: str,
    current_user: User = Depends(get_current_user_or_admin),
    db: Session = Depends(get_db)
):
    """删除皮肤科会话"""
    db_session = db.query(DermaSession).filter(
        DermaSession.id == session_id,
        DermaSession.user_id == current_user.id
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    db.delete(db_session)
    db.commit()
    
    return {"message": "删除成功"}
