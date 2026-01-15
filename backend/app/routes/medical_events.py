"""
病历事件 API 路由

包含：
- 病历事件 CRUD
- 附件管理
- 备注管理
- 数据聚合
- 导出功能
- 共享链接

权限控制：用户只能访问自己的病历数据
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.medical_event import (
    MedicalEvent, EventAttachment, EventNote, ExportRecord, ExportAccessLog,
    EventStatus, RiskLevel, AgentType, AttachmentType
)
from ..schemas.medical_event import (
    MedicalEventCreateRequest, MedicalEventUpdateRequest,
    MedicalEventSummarySchema, MedicalEventDetailSchema, MedicalEventListResponse,
    AttachmentSchema, AttachmentCreateRequest, NoteSchema, NoteCreateRequest, NoteUpdateRequest,
    ExportCreateRequest, ExportRecordSchema, ExportResponse, ShareLinkAccessRequest, ShareLinkResponse,
    AggregateSessionRequest, AggregateResponse, GenerateSummaryRequest, GenerateSummaryResponse,
    AIAnalysisSchema, SessionRecordSchema, SessionSummarySchema
)

router = APIRouter(prefix="/medical-events", tags=["medical-events"])
logger = logging.getLogger(__name__)


# ============= 权限检查辅助函数 =============

def get_event_with_permission(
    event_id: str,
    user: User,
    db: Session,
    allow_archived: bool = True
) -> MedicalEvent:
    """获取事件并验证权限"""
    event = db.query(MedicalEvent).filter(MedicalEvent.id == event_id).first()
    
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="病历事件不存在")
    
    if event.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此病历事件")
    
    if not allow_archived and event.status == EventStatus.archived:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已归档的事件不可操作")
    
    return event


# ============= 病历事件 CRUD =============

@router.post("", response_model=MedicalEventDetailSchema, status_code=status.HTTP_201_CREATED)
def create_medical_event(
    request: MedicalEventCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建病历事件
    
    用户首次与某科室智能体对话时自动创建，或手动创建
    """
    event = MedicalEvent(
        user_id=current_user.id,
        title=request.title,
        department=request.department,
        agent_type=AgentType(request.agent_type),
        chief_complaint=request.chief_complaint,
        risk_level=RiskLevel(request.risk_level),
        status=EventStatus.active,
        ai_analysis={},
        sessions=[]
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    logger.info(f"Created medical event {event.id} for user {current_user.id}")
    return _build_event_detail(event)


@router.get("", response_model=MedicalEventListResponse)
def list_medical_events(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    department: Optional[str] = Query(None, description="科室筛选"),
    agent_type: Optional[str] = Query(None, description="智能体类型"),
    event_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    risk_level: Optional[str] = Query(None, description="风险等级"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|updated_at|start_time)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取病历事件列表
    
    支持搜索和多维度筛选，只返回当前用户的数据
    """
    query = db.query(MedicalEvent).filter(MedicalEvent.user_id == current_user.id)
    
    # 关键词搜索
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                MedicalEvent.title.ilike(search_pattern),
                MedicalEvent.summary.ilike(search_pattern),
                MedicalEvent.chief_complaint.ilike(search_pattern),
                MedicalEvent.department.ilike(search_pattern)
            )
        )
    
    # 筛选条件
    if department:
        query = query.filter(MedicalEvent.department == department)
    if agent_type:
        query = query.filter(MedicalEvent.agent_type == AgentType(agent_type))
    if event_status:
        query = query.filter(MedicalEvent.status == EventStatus(event_status))
    if risk_level:
        query = query.filter(MedicalEvent.risk_level == RiskLevel(risk_level))
    if start_date:
        query = query.filter(MedicalEvent.start_time >= start_date)
    if end_date:
        query = query.filter(MedicalEvent.start_time <= end_date)
    
    # 总数
    total = query.count()
    
    # 排序
    sort_column = getattr(MedicalEvent, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # 分页
    events = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return MedicalEventListResponse(
        events=[_build_event_summary(e) for e in events],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{event_id}", response_model=MedicalEventDetailSchema)
def get_medical_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取病历事件详情"""
    event = get_event_with_permission(event_id, current_user, db)
    return _build_event_detail(event)


@router.put("/{event_id}", response_model=MedicalEventDetailSchema)
def update_medical_event(
    event_id: str,
    request: MedicalEventUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新病历事件"""
    event = get_event_with_permission(event_id, current_user, db, allow_archived=False)
    
    update_data = request.model_dump(exclude_unset=True)
    
    if "status" in update_data:
        update_data["status"] = EventStatus(update_data["status"])
    if "risk_level" in update_data:
        update_data["risk_level"] = RiskLevel(update_data["risk_level"])
    
    for key, value in update_data.items():
        setattr(event, key, value)
    
    db.commit()
    db.refresh(event)
    
    logger.info(f"Updated medical event {event_id}")
    return _build_event_detail(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medical_event(
    event_id: str,
    confirm: bool = Query(..., description="需设为true确认删除"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除病历事件
    
    需要 confirm=true 二次确认
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请确认删除操作（设置 confirm=true）"
        )
    
    event = get_event_with_permission(event_id, current_user, db)
    
    db.delete(event)
    db.commit()
    
    logger.info(f"Deleted medical event {event_id}")


@router.post("/{event_id}/archive", response_model=MedicalEventDetailSchema)
def archive_medical_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """归档病历事件"""
    event = get_event_with_permission(event_id, current_user, db)
    
    event.status = EventStatus.archived
    event.end_time = datetime.utcnow()
    db.commit()
    db.refresh(event)
    
    return _build_event_detail(event)


# ============= 附件管理 =============

@router.post("/{event_id}/attachments", response_model=AttachmentSchema, status_code=status.HTTP_201_CREATED)
def add_attachment(
    event_id: str,
    request: AttachmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加附件到病历事件"""
    event = get_event_with_permission(event_id, current_user, db, allow_archived=False)
    
    attachment = EventAttachment(
        event_id=event_id,
        type=AttachmentType(request.type),
        url=request.url,
        thumbnail_url=request.thumbnail_url,
        filename=request.filename,
        file_size=request.file_size,
        mime_type=request.mime_type,
        metadata=request.metadata or {},
        description=request.description
    )
    
    db.add(attachment)
    event.attachment_count += 1
    db.commit()
    db.refresh(attachment)
    
    return AttachmentSchema.model_validate(attachment)


@router.delete("/{event_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    event_id: str,
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除附件"""
    event = get_event_with_permission(event_id, current_user, db, allow_archived=False)
    
    attachment = db.query(EventAttachment).filter(
        EventAttachment.id == attachment_id,
        EventAttachment.event_id == event_id
    ).first()
    
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")
    
    db.delete(attachment)
    event.attachment_count = max(0, event.attachment_count - 1)
    db.commit()


# ============= 备注管理 =============

@router.post("/{event_id}/notes", response_model=NoteSchema, status_code=status.HTTP_201_CREATED)
def add_note(
    event_id: str,
    request: NoteCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加备注"""
    event = get_event_with_permission(event_id, current_user, db)
    
    note = EventNote(
        event_id=event_id,
        content=request.content,
        is_important=request.is_important
    )
    
    db.add(note)
    db.commit()
    db.refresh(note)
    
    return NoteSchema.model_validate(note)


@router.put("/{event_id}/notes/{note_id}", response_model=NoteSchema)
def update_note(
    event_id: str,
    note_id: str,
    request: NoteUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新备注"""
    get_event_with_permission(event_id, current_user, db)
    
    note = db.query(EventNote).filter(
        EventNote.id == note_id,
        EventNote.event_id == event_id
    ).first()
    
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="备注不存在")
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)
    
    db.commit()
    db.refresh(note)
    
    return NoteSchema.model_validate(note)


@router.delete("/{event_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    event_id: str,
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除备注"""
    get_event_with_permission(event_id, current_user, db)
    
    note = db.query(EventNote).filter(
        EventNote.id == note_id,
        EventNote.event_id == event_id
    ).first()
    
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="备注不存在")
    
    db.delete(note)
    db.commit()


# ============= 辅助函数：科室名称和类型映射 =============

def get_department_name(agent_type: str) -> str:
    """获取科室中文名称"""
    mapping = {
        "dermatology": "皮肤科",
        "cardiology": "心血管科",
        "orthopedics": "骨科",
        "general": "全科",
        "neurology": "神经科",
        "endocrinology": "内分泌科",
        "gastroenterology": "消化科",
        "respiratory": "呼吸科",
        # 后端短名
        "derma": "皮肤科",
        "cardio": "心血管科",
        "ortho": "骨科",
        "neuro": "神经科",
        "endo": "内分泌科",
        "gastro": "消化科",
        "diagnosis": "全科",
    }
    return mapping.get(agent_type, "全科")


def get_agent_type_enum(agent_type: str) -> AgentType:
    """将字符串转换为AgentType枚举"""
    mapping = {
        "dermatology": AgentType.derma,
        "cardiology": AgentType.cardio,
        "orthopedics": AgentType.ortho,
        "general": AgentType.general,
        "neurology": AgentType.neuro,
        "endocrinology": AgentType.endo,
        "gastroenterology": AgentType.gastro,
        "respiratory": AgentType.respiratory,
        # 后端短名
        "derma": AgentType.derma,
        "cardio": AgentType.cardio,
        "ortho": AgentType.ortho,
        "neuro": AgentType.neuro,
        "endo": AgentType.endo,
        "gastro": AgentType.gastro,
        "diagnosis": AgentType.general,
    }
    return mapping.get(agent_type, AgentType.general)


# ============= 数据聚合 =============

@router.post("/aggregate", response_model=AggregateResponse)
def aggregate_session(
    request: AggregateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    聚合会话到病历事件 (重构版本)
    
    核心改动：
    1. 从统一的 sessions 表查询会话数据
    2. 从 messages 表获取完整对话历史
    3. 从 agent_state 提取症状、主诉等信息
    4. 不再创建假数据，会话不存在时返回404错误
    
    会话结束时自动调用，将对话记录关联到现有事件或创建新事件
    支持所有科室类型
    """
    from ..models.session import Session as SessionModel
    from ..models.message import Message
    
    # 1. 查询统一会话表
    session = db.query(SessionModel).filter(
        SessionModel.id == request.session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话不存在: {request.session_id}"
        )
    
    # 2. 获取消息历史
    messages = db.query(Message).filter(
        Message.session_id == request.session_id
    ).order_by(Message.created_at).all()
    
    # 3. 从 agent_state 提取信息
    state = session.agent_state or {}
    chief_complaint = state.get("chief_complaint", "")
    symptoms = state.get("symptoms", [])
    risk_level = state.get("risk_level", "low")
    stage = state.get("stage", "completed")
    
    # 4. 数据完整性验证
    # 检查是否收集到足够的信息才允许聚合
    validation_errors = []
    
    if not chief_complaint:
        validation_errors.append("尚未明确主诉")
    if not symptoms or len(symptoms) == 0:
        validation_errors.append("尚未收集到症状信息")
    if stage == "greeting":
        validation_errors.append("对话刚开始，请先描述您的问题")
    elif stage == "collecting" and len(messages) < 5:
        validation_errors.append("对话信息太少，请继续描述症状")
    
    if validation_errors:
        error_detail = "会话信息不完整: " + "、".join(validation_errors) + "。请继续对话后再生成病历。"
        logger.warning(f"Session {request.session_id} validation failed: {validation_errors}, messages={len(messages)}, stage={stage}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )
    
    # 4. 获取科室信息
    # 优先使用请求中的 session_type，如果未指定则使用会话的 agent_type
    effective_agent_type = request.session_type or session.agent_type or "general"
    department = get_department_name(effective_agent_type)
    agent_type_enum = get_agent_type_enum(effective_agent_type)
    
    # 5. 构建完整的会话数据
    session_data = {
        "session_id": session.id,
        "session_type": effective_agent_type,
        "timestamp": session.created_at.isoformat() if session.created_at else datetime.utcnow().isoformat(),
        "summary": f"{department}问诊 - {chief_complaint}" if chief_complaint else f"{department}问诊",
        "chief_complaint": chief_complaint,
        "symptoms": symptoms,
        "risk_level": risk_level,
        "stage": stage,
        "message_count": len(messages),
        "messages": [
            {
                "role": msg.sender.value if msg.sender else "user",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if msg.created_at else "",
                "type": msg.message_type or "text"
            }
            for msg in messages[:50]  # 限制消息数量，避免JSON过大
        ],
        # 科室特定数据（从 agent_state 提取）
        "skin_analyses": state.get("skin_analyses", []),
        "ecg_interpretations": state.get("ecg_interpretations", []),
        "possible_diseases": state.get("possible_diseases", []),
        "possible_conditions": state.get("possible_conditions", []),
        "recommendations": state.get("recommendations", {}),
        "symptom_details": state.get("symptom_details", {})
    }
    
    # 6. 查找当天同科室的现有事件
    today = datetime.utcnow().date()
    existing_event = db.query(MedicalEvent).filter(
        MedicalEvent.user_id == current_user.id,
        MedicalEvent.agent_type == agent_type_enum,
        MedicalEvent.status == EventStatus.active,
        MedicalEvent.start_time >= datetime.combine(today, datetime.min.time())
    ).first()
    
    is_new_event = False
    
    if existing_event:
        # 添加到现有事件
        sessions_list = existing_event.sessions or []
        # 检查是否已存在该会话
        existing_session_idx = next(
            (i for i, s in enumerate(sessions_list) if s.get("session_id") == request.session_id),
            None
        )
        if existing_session_idx is not None:
            # 更新现有会话数据
            sessions_list[existing_session_idx] = session_data
        else:
            # 添加新会话
            sessions_list.append(session_data)
        
        existing_event.sessions = sessions_list
        existing_event.session_count = len(sessions_list)
        
        # 更新主诉（如果当前会话有主诉且事件没有主诉）
        if chief_complaint and not existing_event.chief_complaint:
            existing_event.chief_complaint = chief_complaint
        
        # 更新风险等级（取最高级别）
        risk_priority = {"low": 0, "medium": 1, "high": 2, "emergency": 3}
        current_risk = existing_event.risk_level.value if existing_event.risk_level else "low"
        if risk_priority.get(risk_level, 0) > risk_priority.get(current_risk, 0):
            existing_event.risk_level = RiskLevel(risk_level)
        
        event = existing_event
    else:
        # 创建新事件
        event = MedicalEvent(
            user_id=current_user.id,
            title=f"{department} {today.strftime('%Y-%m-%d')}",
            department=department,
            agent_type=agent_type_enum,
            chief_complaint=chief_complaint,
            risk_level=RiskLevel(risk_level) if risk_level in ["low", "medium", "high", "emergency"] else RiskLevel.low,
            status=EventStatus.active,
            sessions=[session_data],
            session_count=1
        )
        db.add(event)
        is_new_event = True
    
    db.commit()
    db.refresh(event)
    
    logger.info(f"Successfully aggregated session {request.session_id} to event {event.id} (new={is_new_event})")
    
    # 构建会话摘要
    has_images = any(
        msg.message_type == "image" or 
        (msg.attachments and any(a.get("type") == "image" for a in msg.attachments))
        for msg in messages
    )
    
    return AggregateResponse(
        event_id=str(event.id),
        message="会话已聚合到病历事件",
        is_new_event=is_new_event,
        session_summary=SessionSummarySchema(
            chief_complaint=chief_complaint,
            symptoms=symptoms if isinstance(symptoms, list) else [],
            risk_level=risk_level,
            message_count=len(messages),
            has_images=has_images
        )
    )


@router.post("/{event_id}/generate-summary", response_model=GenerateSummaryResponse)
async def generate_summary(
    event_id: str,
    force_regenerate: bool = Query(False, description="强制重新生成"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成事件摘要和AI分析
    
    调用AI生成结构化摘要
    """
    from ..services.ai.summary_service import get_summary_service
    
    event = get_event_with_permission(event_id, current_user, db)
    
    if event.summary and event.ai_analysis and not force_regenerate:
        return GenerateSummaryResponse(
            event_id=event.id,
            summary=event.summary,
            ai_analysis=AIAnalysisSchema(**event.ai_analysis) if event.ai_analysis else AIAnalysisSchema(),
            message="已有摘要，无需重新生成"
        )
    
    # 准备数据
    sessions = event.sessions or []
    attachments = [
        {
            "type": att.type.value if att.type else "unknown",
            "filename": att.filename,
            "description": att.description
        }
        for att in event.attachments
    ]
    notes = [
        {
            "content": note.content,
            "is_important": note.is_important,
            "created_at": note.created_at.isoformat() if note.created_at else ""
        }
        for note in event.notes
    ]
    
    # 调用 AI 摘要服务
    summary_service = get_summary_service()
    
    try:
        result = await summary_service.generate_summary(
            chief_complaint=event.chief_complaint or "",
            department=event.department or "",
            sessions=sessions,
            attachments=attachments,
            notes=notes,
            existing_analysis=event.ai_analysis
        )
        
        # 构建 AI 分析结果
        ai_analysis = {
            "symptoms": result.symptoms,
            "possible_diagnosis": result.possible_diagnosis,
            "recommendations": result.recommendations,
            "follow_up_reminders": result.follow_up_reminders,
            "timeline": result.timeline,
            "key_points": result.key_points,
            "symptom_details": result.symptom_details,
            "risk_level": result.risk_level,
            "risk_warning": result.risk_warning,
            "confidence": result.confidence
        }
        
        event.summary = result.summary
        event.ai_analysis = ai_analysis
        db.commit()
        db.refresh(event)
        
        logger.info(f"Generated AI summary for event {event_id}")
        
        return GenerateSummaryResponse(
            event_id=event.id,
            summary=result.summary,
            ai_analysis=AIAnalysisSchema(**ai_analysis),
            message="摘要生成成功"
        )
        
    except Exception as e:
        logger.error(f"AI summary generation failed: {e}")
        # 降级处理：返回基础摘要
        summary_parts = []
        if event.chief_complaint:
            summary_parts.append(f"主诉：{event.chief_complaint}")
        summary_parts.append(f"科室：{event.department}")
        summary_parts.append(f"会话数：{event.session_count}")
        summary_parts.append(f"附件数：{event.attachment_count}")
        
        summary = "；".join(summary_parts)
        ai_analysis = {
            "symptoms": [],
            "possible_diagnosis": [],
            "recommendations": ["建议继续观察", "如症状加重请及时就医"],
            "follow_up_reminders": [],
            "timeline": []
        }
        
        event.summary = summary
        event.ai_analysis = ai_analysis
        db.commit()
        db.refresh(event)
        
        return GenerateSummaryResponse(
            event_id=event.id,
            summary=summary,
            ai_analysis=AIAnalysisSchema(**ai_analysis),
            message="摘要生成成功（降级模式）"
        )


# ============= 导出功能 =============

@router.post("/export", response_model=ExportResponse)
def create_export(
    request: ExportCreateRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建导出任务
    
    支持单个或多个事件导出为 PDF 或生成共享链接
    需要二次确认（通过请求体确认）
    """
    # 验证所有事件的权限
    events = []
    for eid in request.event_ids:
        event = get_event_with_permission(eid, current_user, db)
        events.append(event)
    
    # 创建导出记录
    export_record = ExportRecord(
        user_id=current_user.id,
        event_id=request.event_ids[0] if len(request.event_ids) == 1 else None,
        export_type=request.export_type,
        event_ids=request.event_ids,
        export_options=request.options.model_dump() if request.options else {}
    )
    
    # 处理共享链接
    if request.export_type == "share_link":
        export_record.share_token = ExportRecord.generate_share_token()
        if request.share_password:
            export_record.share_password = request.share_password
        if request.expires_in_days:
            export_record.expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
        if request.max_views:
            export_record.max_views = request.max_views
    
    # TODO: PDF生成逻辑
    if request.export_type == "pdf":
        # 这里应该调用PDF生成服务
        export_record.file_url = f"/api/exports/{export_record.id}/download"
    
    db.add(export_record)
    
    # 更新事件导出计数
    for event in events:
        event.export_count += 1
        if event.status == EventStatus.active:
            event.status = EventStatus.exported
    
    db.commit()
    db.refresh(export_record)
    
    # 构建响应
    base_url = str(http_request.base_url).rstrip("/")
    share_url = None
    if export_record.share_token:
        share_url = f"{base_url}/api/medical-events/share/{export_record.share_token}"
    
    return ExportResponse(
        export_id=export_record.id,
        export_type=export_record.export_type,
        file_url=export_record.file_url,
        share_url=share_url,
        share_token=export_record.share_token,
        expires_at=export_record.expires_at,
        message="导出创建成功"
    )


@router.get("/exports", response_model=list[ExportRecordSchema])
def list_exports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取导出记录列表"""
    exports = db.query(ExportRecord).filter(
        ExportRecord.user_id == current_user.id
    ).order_by(ExportRecord.created_at.desc()).all()
    
    return [_build_export_record(e) for e in exports]


@router.delete("/exports/{export_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_export(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除/失效导出记录"""
    export = db.query(ExportRecord).filter(
        ExportRecord.id == export_id,
        ExportRecord.user_id == current_user.id
    ).first()
    
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="导出记录不存在")
    
    export.is_active = False
    db.commit()


@router.get("/share/{token}", response_model=ShareLinkResponse)
def access_share_link(
    token: str,
    password: Optional[str] = Query(None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    访问共享链接（无需登录）
    
    验证链接有效性、密码、过期时间、访问次数
    """
    export = db.query(ExportRecord).filter(
        ExportRecord.share_token == token,
        ExportRecord.is_active == True
    ).first()
    
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="链接不存在或已失效")
    
    # 验证过期时间
    if export.expires_at and export.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="链接已过期")
    
    # 验证访问次数
    if export.max_views and export.view_count >= export.max_views:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="链接已达最大访问次数")
    
    # 验证密码
    if export.share_password and export.share_password != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="密码错误")
    
    # 获取事件数据
    events = db.query(MedicalEvent).filter(
        MedicalEvent.id.in_(export.event_ids)
    ).all()
    
    # 记录访问
    export.view_count += 1
    export.last_viewed_at = datetime.utcnow()
    
    access_log = ExportAccessLog(
        export_id=export.id,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(access_log)
    db.commit()
    
    return ShareLinkResponse(
        events=[_build_event_detail(e) for e in events],
        export_info=_build_export_record(export),
        accessed_at=datetime.utcnow()
    )


# ============= 辅助函数 =============

def _build_event_summary(event: MedicalEvent) -> MedicalEventSummarySchema:
    """构建事件摘要"""
    # 安全获取枚举值，防止无效数据导致500错误
    try:
        agent_type_value = event.agent_type.value if event.agent_type else "general"
    except (AttributeError, ValueError):
        logger.warning(f"Invalid agent_type for event {event.id}: {event.agent_type}")
        agent_type_value = "general"
    
    try:
        status_value = event.status.value if event.status else "active"
    except (AttributeError, ValueError):
        logger.warning(f"Invalid status for event {event.id}: {event.status}")
        status_value = "active"
    
    try:
        risk_level_value = event.risk_level.value if event.risk_level else "low"
    except (AttributeError, ValueError):
        logger.warning(f"Invalid risk_level for event {event.id}: {event.risk_level}")
        risk_level_value = "low"
    
    return MedicalEventSummarySchema(
        id=str(event.id),
        title=event.title or f"病历事件 {event.id}",
        department=event.department or "全科",
        agent_type=agent_type_value,
        status=status_value,
        risk_level=risk_level_value,
        start_time=event.start_time,
        end_time=event.end_time,
        summary=event.summary,
        chief_complaint=event.chief_complaint,
        attachment_count=event.attachment_count or 0,
        session_count=event.session_count or 0,
        created_at=event.created_at,
        updated_at=event.updated_at
    )


def _build_event_detail(event: MedicalEvent) -> MedicalEventDetailSchema:
    """构建事件详情"""
    # 安全解析 AI 分析
    ai_analysis = None
    if event.ai_analysis:
        try:
            ai_analysis = AIAnalysisSchema(**event.ai_analysis)
        except Exception as e:
            logger.warning(f"Failed to parse ai_analysis for event {event.id}: {e}")
    
    # 安全解析会话记录
    sessions = []
    if event.sessions:
        for s in event.sessions:
            try:
                sessions.append(SessionRecordSchema(**s))
            except Exception as e:
                logger.warning(f"Failed to parse session for event {event.id}: {e}")
    
    # 安全解析附件和备注
    attachments = []
    for a in event.attachments:
        try:
            attachments.append(AttachmentSchema.model_validate(a))
        except Exception as e:
            logger.warning(f"Failed to parse attachment {a.id} for event {event.id}: {e}")
    
    notes = []
    for n in event.notes:
        try:
            notes.append(NoteSchema.model_validate(n))
        except Exception as e:
            logger.warning(f"Failed to parse note {n.id} for event {event.id}: {e}")
    
    # 安全获取枚举值
    try:
        agent_type_value = event.agent_type.value if event.agent_type else "general"
    except (AttributeError, ValueError):
        logger.warning(f"Invalid agent_type for event {event.id}: {event.agent_type}")
        agent_type_value = "general"
    
    try:
        status_value = event.status.value if event.status else "active"
    except (AttributeError, ValueError):
        logger.warning(f"Invalid status for event {event.id}: {event.status}")
        status_value = "active"
    
    try:
        risk_level_value = event.risk_level.value if event.risk_level else "low"
    except (AttributeError, ValueError):
        logger.warning(f"Invalid risk_level for event {event.id}: {event.risk_level}")
        risk_level_value = "low"
    
    return MedicalEventDetailSchema(
        id=str(event.id),
        title=event.title or f"病历事件 {event.id}",
        department=event.department or "全科",
        agent_type=agent_type_value,
        status=status_value,
        risk_level=risk_level_value,
        start_time=event.start_time,
        end_time=event.end_time,
        summary=event.summary,
        chief_complaint=event.chief_complaint,
        ai_analysis=ai_analysis,
        sessions=sessions,
        attachments=attachments,
        notes=notes,
        attachment_count=event.attachment_count or 0,
        session_count=event.session_count or 0,
        export_count=event.export_count or 0,
        created_at=event.created_at,
        updated_at=event.updated_at
    )


def _build_export_record(export: ExportRecord) -> ExportRecordSchema:
    """构建导出记录"""
    return ExportRecordSchema(
        id=export.id,
        export_type=export.export_type,
        file_url=export.file_url,
        share_token=export.share_token,
        has_password=bool(export.share_password),
        expires_at=export.expires_at,
        view_count=export.view_count or 0,
        max_views=export.max_views,
        is_active=export.is_active,
        created_at=export.created_at,
        event_ids=export.event_ids or []
    )
