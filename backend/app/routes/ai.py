"""
AI 算法服务 API 路由

包含：
- AI 摘要生成
- 智能事件聚合
- 语音转写
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.medical_event import MedicalEvent, EventStatus
from ..services.ai import (
    AISummaryService,
    EventAggregationService,
    SpeechTranscriptionService
)
from ..services.ai.summary_service import get_summary_service
from ..services.ai.aggregation_service import get_aggregation_service
from ..services.ai.transcription_service import get_transcription_service

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


# ============= 请求/响应模型 =============

class GenerateSummaryRequest(BaseModel):
    """生成摘要请求"""
    event_id: str
    force_regenerate: bool = False


class SummaryResponse(BaseModel):
    """摘要响应"""
    event_id: str
    summary: str
    key_points: List[str]
    symptoms: List[str]
    symptom_details: dict
    possible_diagnosis: List[str]
    risk_level: str
    risk_warning: Optional[str]
    recommendations: List[str]
    follow_up_reminders: List[str]
    timeline: List[dict]
    confidence: float
    message: str


class AnalyzeRelationRequest(BaseModel):
    """分析关联请求"""
    event_id_a: str
    event_id_b: str


class RelationAnalysisResponse(BaseModel):
    """关联分析响应"""
    is_related: bool
    relation_type: str
    confidence: float
    reasoning: str
    should_merge: bool
    merge_suggestion: Optional[str] = None


class SmartAggregateRequest(BaseModel):
    """智能聚合请求"""
    session_id: str
    session_type: str  # derma/diagnosis
    department: str
    chief_complaint: Optional[str] = None


class SmartAggregateResponse(BaseModel):
    """智能聚合响应"""
    action: str  # add_to_existing/create_new
    target_event_id: Optional[str]
    confidence: float
    reasoning: str
    should_merge: bool


class FindRelatedRequest(BaseModel):
    """查找相关事件请求"""
    event_id: str
    max_results: int = 5


class RelatedEventItem(BaseModel):
    """相关事件项"""
    event_id: str
    relation_type: str
    confidence: float
    reasoning: str


class FindRelatedResponse(BaseModel):
    """查找相关事件响应"""
    target_event_id: str
    related_events: List[RelatedEventItem]


class MergeEventsRequest(BaseModel):
    """合并事件请求"""
    event_ids: List[str] = Field(..., min_length=2)
    new_title: Optional[str] = None


class MergeEventsResponse(BaseModel):
    """合并事件响应"""
    merged_event_id: str
    merged_title: str
    summary: str
    disease_progression: str
    current_status: str
    overall_risk_level: str
    recommendations: List[str]
    message: str


class TranscribeRequest(BaseModel):
    """转写请求"""
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    language: str = "zh"
    extract_symptoms: bool = True


class TranscriptionSegment(BaseModel):
    """转写分段"""
    start_time: float
    end_time: float
    text: str
    confidence: float


class TranscribeResponse(BaseModel):
    """转写响应"""
    task_id: str
    status: str
    text: str
    duration: float
    confidence: float
    segments: List[TranscriptionSegment]
    extracted_symptoms: List[str]
    language: str
    error_message: Optional[str] = None


class TranscriptionStatusResponse(BaseModel):
    """转写状态响应"""
    task_id: str
    status: str
    text: Optional[str] = None
    error_message: Optional[str] = None


# ============= AI 摘要 API =============

@router.post("/summary", response_model=SummaryResponse)
async def generate_ai_summary(
    request: GenerateSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成 AI 摘要
    
    从病历事件的对话记录、附件等信息中生成结构化摘要
    """
    # 转换 event_id 为整数
    try:
        event_id_int = int(request.event_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的事件ID"
        )
    
    # 获取事件并验证权限
    event = db.query(MedicalEvent).filter(
        MedicalEvent.id == event_id_int,
        MedicalEvent.user_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="病历事件不存在"
        )
    
    # 检查是否已有摘要且不强制重新生成
    if event.summary and event.ai_analysis and not request.force_regenerate:
        return SummaryResponse(
            event_id=event.id,
            summary=event.summary,
            key_points=event.ai_analysis.get("key_points", []),
            symptoms=event.ai_analysis.get("symptoms", []),
            symptom_details=event.ai_analysis.get("symptom_details", {}),
            possible_diagnosis=event.ai_analysis.get("possible_diagnosis", []),
            risk_level=event.ai_analysis.get("risk_level", "low"),
            risk_warning=event.ai_analysis.get("risk_warning"),
            recommendations=event.ai_analysis.get("recommendations", []),
            follow_up_reminders=event.ai_analysis.get("follow_up_reminders", []),
            timeline=event.ai_analysis.get("timeline", []),
            confidence=event.ai_analysis.get("confidence", 0.5),
            message="已有摘要，使用缓存"
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
        
        # 更新事件
        event.summary = result.summary
        event.ai_analysis = result.to_dict()
        db.commit()
        
        logger.info(f"Generated AI summary for event {event.id}")
        
        return SummaryResponse(
            event_id=event.id,
            summary=result.summary,
            key_points=result.key_points,
            symptoms=result.symptoms,
            symptom_details=result.symptom_details,
            possible_diagnosis=result.possible_diagnosis,
            risk_level=result.risk_level,
            risk_warning=result.risk_warning,
            recommendations=result.recommendations,
            follow_up_reminders=result.follow_up_reminders,
            timeline=result.timeline,
            confidence=result.confidence,
            message="摘要生成成功"
        )
        
    except Exception as e:
        logger.error(f"AI summary generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"摘要生成失败: {str(e)}"
        )


@router.get("/summary/{event_id}", response_model=SummaryResponse)
async def get_ai_summary(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取事件的 AI 摘要"""
    # 转换 event_id 为整数
    try:
        event_id_int = int(event_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的事件ID"
        )
    
    event = db.query(MedicalEvent).filter(
        MedicalEvent.id == event_id_int,
        MedicalEvent.user_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="病历事件不存在"
        )
    
    if not event.summary or not event.ai_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="尚未生成摘要，请先调用 POST /ai/summary"
        )
    
    analysis = event.ai_analysis or {}
    
    return SummaryResponse(
        event_id=event.id,
        summary=event.summary,
        key_points=analysis.get("key_points", []),
        symptoms=analysis.get("symptoms", []),
        symptom_details=analysis.get("symptom_details", {}),
        possible_diagnosis=analysis.get("possible_diagnosis", []),
        risk_level=analysis.get("risk_level", "low"),
        risk_warning=analysis.get("risk_warning"),
        recommendations=analysis.get("recommendations", []),
        follow_up_reminders=analysis.get("follow_up_reminders", []),
        timeline=analysis.get("timeline", []),
        confidence=analysis.get("confidence", 0.5),
        message="获取成功"
    )


# ============= 智能聚合 API =============

@router.post("/analyze-relation", response_model=RelationAnalysisResponse)
async def analyze_event_relation(
    request: AnalyzeRelationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    分析两个事件的关联性
    
    判断是否属于同一病情，是否应该合并
    """
    # 转换 event_id 为整数
    try:
        event_id_a_int = int(request.event_id_a)
        event_id_b_int = int(request.event_id_b)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的事件ID"
        )
    
    # 获取两个事件
    event_a = db.query(MedicalEvent).filter(
        MedicalEvent.id == event_id_a_int,
        MedicalEvent.user_id == current_user.id
    ).first()
    
    event_b = db.query(MedicalEvent).filter(
        MedicalEvent.id == event_id_b_int,
        MedicalEvent.user_id == current_user.id
    ).first()
    
    if not event_a or not event_b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    # 调用聚合服务
    aggregation_service = get_aggregation_service()
    
    event_a_dict = {
        "id": event_a.id,
        "title": event_a.title,
        "department": event_a.department,
        "chief_complaint": event_a.chief_complaint,
        "symptoms": event_a.ai_analysis.get("symptoms", []) if event_a.ai_analysis else [],
        "start_time": event_a.start_time.isoformat() if event_a.start_time else "",
        "summary": event_a.summary
    }
    
    event_b_dict = {
        "id": event_b.id,
        "title": event_b.title,
        "department": event_b.department,
        "chief_complaint": event_b.chief_complaint,
        "symptoms": event_b.ai_analysis.get("symptoms", []) if event_b.ai_analysis else [],
        "start_time": event_b.start_time.isoformat() if event_b.start_time else "",
        "summary": event_b.summary
    }
    
    try:
        result = await aggregation_service.analyze_relation(event_a_dict, event_b_dict)
        
        return RelationAnalysisResponse(
            is_related=result.get("is_related", False),
            relation_type=result.get("relation_type", "unrelated"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", ""),
            should_merge=result.get("should_merge", False),
            merge_suggestion=result.get("merge_suggestion")
        )
        
    except Exception as e:
        logger.error(f"Relation analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"关联分析失败: {str(e)}"
        )


@router.post("/smart-aggregate", response_model=SmartAggregateResponse)
async def smart_aggregate_session(
    request: SmartAggregateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    智能聚合分析
    
    判断新会话应归入哪个现有事件或创建新事件
    """
    from datetime import datetime
    
    # 获取现有活跃事件
    existing_events = db.query(MedicalEvent).filter(
        MedicalEvent.user_id == current_user.id,
        MedicalEvent.status == EventStatus.ACTIVE
    ).order_by(MedicalEvent.start_time.desc()).limit(10).all()
    
    # 准备数据
    session_info = {
        "session_id": request.session_id,
        "session_type": request.session_type,
        "department": request.department,
        "chief_complaint": request.chief_complaint or "",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    events_list = [
        {
            "id": e.id,
            "title": e.title,
            "department": e.department,
            "chief_complaint": e.chief_complaint,
            "start_time": e.start_time.isoformat() if e.start_time else "",
            "status": e.status.value if e.status else "active"
        }
        for e in existing_events
    ]
    
    # 调用聚合服务
    aggregation_service = get_aggregation_service()
    
    try:
        result = await aggregation_service.smart_aggregate(session_info, events_list)
        
        return SmartAggregateResponse(
            action=result.suggested_action,
            target_event_id=result.target_event_id,
            confidence=result.confidence,
            reasoning=result.merge_reason,
            should_merge=result.should_merge
        )
        
    except Exception as e:
        logger.error(f"Smart aggregate failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"智能聚合失败: {str(e)}"
        )


@router.post("/find-related", response_model=FindRelatedResponse)
async def find_related_events(
    request: FindRelatedRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查找相关事件
    
    从用户的所有事件中找出与目标事件相关的病历
    """
    # 转换 event_id 为整数
    try:
        event_id_int = int(request.event_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的事件ID"
        )
    
    # 获取目标事件
    target_event = db.query(MedicalEvent).filter(
        MedicalEvent.id == event_id_int,
        MedicalEvent.user_id == current_user.id
    ).first()
    
    if not target_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    # 获取候选事件
    candidates = db.query(MedicalEvent).filter(
        MedicalEvent.user_id == current_user.id,
        MedicalEvent.id != event_id_int
    ).order_by(MedicalEvent.start_time.desc()).limit(20).all()
    
    if not candidates:
        return FindRelatedResponse(
            target_event_id=request.event_id,
            related_events=[]
        )
    
    # 准备数据
    target_dict = {
        "id": target_event.id,
        "title": target_event.title,
        "department": target_event.department,
        "chief_complaint": target_event.chief_complaint,
        "symptoms": target_event.ai_analysis.get("symptoms", []) if target_event.ai_analysis else [],
        "start_time": target_event.start_time.isoformat() if target_event.start_time else "",
        "summary": target_event.summary
    }
    
    candidates_list = [
        {
            "id": e.id,
            "title": e.title,
            "department": e.department,
            "chief_complaint": e.chief_complaint,
            "symptoms": e.ai_analysis.get("symptoms", []) if e.ai_analysis else [],
            "start_time": e.start_time.isoformat() if e.start_time else "",
            "summary": e.summary
        }
        for e in candidates
    ]
    
    # 调用聚合服务
    aggregation_service = get_aggregation_service()
    
    try:
        related = await aggregation_service.find_related_events(target_dict, candidates_list)
        
        return FindRelatedResponse(
            target_event_id=request.event_id,
            related_events=[
                RelatedEventItem(
                    event_id=r.event_id,
                    relation_type=r.relation_type,
                    confidence=r.confidence,
                    reasoning=r.reasoning
                )
                for r in related[:request.max_results]
            ]
        )
        
    except Exception as e:
        logger.error(f"Find related failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查找相关事件失败: {str(e)}"
        )


@router.post("/merge-events", response_model=MergeEventsResponse)
async def merge_events(
    request: MergeEventsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    合并多个事件
    
    将多个相关事件合并为一个，生成综合摘要
    """
    # 转换 event_ids 为整数
    try:
        event_ids_int = [int(eid) for eid in request.event_ids]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的事件ID"
        )
    
    # 获取所有要合并的事件
    events = db.query(MedicalEvent).filter(
        MedicalEvent.id.in_(event_ids_int),
        MedicalEvent.user_id == current_user.id
    ).all()
    
    if len(events) != len(event_ids_int):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部分事件不存在或无权访问"
        )
    
    if len(events) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要两个事件进行合并"
        )
    
    # 准备数据
    events_list = [
        {
            "id": e.id,
            "title": e.title,
            "department": e.department,
            "chief_complaint": e.chief_complaint,
            "start_time": e.start_time.isoformat() if e.start_time else "",
            "end_time": e.end_time.isoformat() if e.end_time else "",
            "summary": e.summary,
            "risk_level": e.risk_level.value if e.risk_level else "low",
            "sessions": e.sessions or []
        }
        for e in events
    ]
    
    # 调用聚合服务生成合并摘要
    aggregation_service = get_aggregation_service()
    
    try:
        merge_result = await aggregation_service.generate_merged_summary(events_list)
        
        # 找到最早的事件作为主事件
        events.sort(key=lambda x: x.start_time or x.created_at)
        main_event = events[0]
        
        # 合并会话记录
        all_sessions = []
        for e in events:
            if e.sessions:
                all_sessions.extend(e.sessions)
        
        # 更新主事件
        main_event.title = request.new_title or merge_result.merged_title
        main_event.summary = merge_result.summary
        main_event.sessions = all_sessions
        main_event.session_count = len(all_sessions)
        main_event.ai_analysis = {
            "disease_progression": merge_result.disease_progression,
            "key_milestones": merge_result.key_milestones,
            "current_status": merge_result.current_status,
            "recommendations": merge_result.recommendations,
            "merged_from": [e.id for e in events[1:]]
        }
        
        # 归档其他事件
        for e in events[1:]:
            e.status = EventStatus.ARCHIVED
            e.summary = f"[已合并到 {main_event.id}] " + (e.summary or "")
        
        db.commit()
        
        logger.info(f"Merged events {request.event_ids} into {main_event.id}")
        
        return MergeEventsResponse(
            merged_event_id=main_event.id,
            merged_title=main_event.title,
            summary=merge_result.summary,
            disease_progression=merge_result.disease_progression,
            current_status=merge_result.current_status,
            overall_risk_level=merge_result.overall_risk_level,
            recommendations=merge_result.recommendations,
            message=f"成功合并 {len(events)} 个事件"
        )
        
    except Exception as e:
        logger.error(f"Merge events failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"合并事件失败: {str(e)}"
        )


# ============= 语音转写 API =============

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    request: TranscribeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    转写音频
    
    将语音录音转换为文本，并提取症状信息
    """
    if not request.audio_url and not request.audio_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供 audio_url 或 audio_base64"
        )
    
    transcription_service = get_transcription_service()
    
    try:
        result = await transcription_service.transcribe(
            audio_url=request.audio_url,
            audio_base64=request.audio_base64,
            language=request.language,
            extract_symptoms=request.extract_symptoms
        )
        
        return TranscribeResponse(
            task_id=result.task_id,
            status=result.status.value,
            text=result.text,
            duration=result.duration,
            confidence=result.confidence,
            segments=[
                TranscriptionSegment(
                    start_time=s.start_time,
                    end_time=s.end_time,
                    text=s.text,
                    confidence=s.confidence
                )
                for s in result.segments
            ],
            extracted_symptoms=result.extracted_symptoms,
            language=result.language,
            error_message=result.error_message
        )
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"转写失败: {str(e)}"
        )


@router.post("/transcribe/upload", response_model=TranscribeResponse)
async def transcribe_upload(
    file: UploadFile = File(...),
    language: str = Form("zh"),
    extract_symptoms: bool = Form(True),
    current_user: User = Depends(get_current_user)
):
    """
    上传音频文件进行转写
    """
    transcription_service = get_transcription_service()
    
    # 验证文件
    is_valid, error_msg = transcription_service.validate_audio_file(
        file.filename or "audio",
        file.size or 0
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    try:
        # 读取文件内容
        audio_data = await file.read()
        import base64
        audio_base64 = base64.b64encode(audio_data).decode()
        
        result = await transcription_service.transcribe(
            audio_base64=audio_base64,
            language=language,
            extract_symptoms=extract_symptoms
        )
        
        return TranscribeResponse(
            task_id=result.task_id,
            status=result.status.value,
            text=result.text,
            duration=result.duration,
            confidence=result.confidence,
            segments=[
                TranscriptionSegment(
                    start_time=s.start_time,
                    end_time=s.end_time,
                    text=s.text,
                    confidence=s.confidence
                )
                for s in result.segments
            ],
            extracted_symptoms=result.extracted_symptoms,
            language=result.language,
            error_message=result.error_message
        )
        
    except Exception as e:
        logger.error(f"Upload transcription failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"转写失败: {str(e)}"
        )


@router.get("/transcribe/{task_id}", response_model=TranscriptionStatusResponse)
async def get_transcription_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取转写任务状态"""
    transcription_service = get_transcription_service()
    
    result = await transcription_service.get_task_status(task_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return TranscriptionStatusResponse(
        task_id=result.task_id,
        status=result.status.value,
        text=result.text if result.status.value == "completed" else None,
        error_message=result.error_message
    )
