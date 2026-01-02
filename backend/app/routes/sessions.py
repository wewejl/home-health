from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from ..database import get_db
from ..schemas.session import SessionCreate, SessionResponse
from ..schemas.message import MessageCreate, MessageResponse, MessageListResponse
from ..models.session import Session as SessionModel
from ..models.message import Message, SenderType
from ..models.doctor import Doctor
from ..models.user import User
from ..dependencies import get_current_user
from ..services.qwen_service import QwenService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
def create_session(
    request: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doctor = None
    if request.doctor_id:
        doctor = db.query(Doctor).filter(Doctor.id == request.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="医生不存在")

    session_id = str(uuid.uuid4())
    session = SessionModel(
        id=session_id,
        user_id=current_user.id,
        doctor_id=request.doctor_id
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionResponse(
        session_id=session.id,
        doctor_id=session.doctor_id,
        doctor_name=doctor.name if doctor else "AI助手",
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
    request: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    user_message = Message(
        session_id=session_id,
        sender=SenderType.user,
        content=request.content
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    doctor = db.query(Doctor).filter(Doctor.id == session.doctor_id).first() if session.doctor_id else None

    history = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at.desc()).limit(10).all()
    history.reverse()
    history_data = [{"sender": m.sender.value, "content": m.content} for m in history]

    # 获取 RAG 上下文
    rag_context = ""
    if doctor and doctor.knowledge_base_id:
        from ..services.knowledge_service import KnowledgeService
        rag_context = KnowledgeService.get_context_for_query(
            db, doctor.knowledge_base_id, request.content
        )

    ai_content = await QwenService.get_ai_response(
        user_message=request.content,
        doctor_name=doctor.name if doctor else "AI助手",
        doctor_title=doctor.title if doctor else "主治医师",
        specialty=doctor.specialty if doctor else "全科医学",
        history=history_data,
        persona_prompt=doctor.ai_persona_prompt if doctor else None,
        rag_context=rag_context,
        model=doctor.ai_model if doctor else None,
        temperature=doctor.ai_temperature if doctor else None,
        max_tokens=doctor.ai_max_tokens if doctor else None
    )

    ai_message = Message(
        session_id=session_id,
        sender=SenderType.ai,
        content=ai_content
    )
    db.add(ai_message)

    session.last_message = ai_content[:100]
    db.commit()
    db.refresh(ai_message)

    return {
        "user_message": MessageResponse.model_validate(user_message),
        "ai_message": MessageResponse.model_validate(ai_message)
    }
