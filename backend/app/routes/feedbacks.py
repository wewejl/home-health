from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.session import Session as SessionModel
from ..models.feedback import SessionFeedback
from ..models.user import User
from ..schemas.feedback import FeedbackCreate, FeedbackResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/sessions", tags=["feedbacks"])


@router.post("/{session_id}/feedback", response_model=FeedbackResponse)
def create_session_feedback(
    session_id: str,
    request: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    feedback = SessionFeedback(
        session_id=session_id,
        message_id=request.message_id,
        user_id=current_user.id,
        rating=request.rating,
        feedback_type=request.feedback_type,
        feedback_text=request.feedback_text
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return FeedbackResponse.model_validate(feedback)


@router.post("/messages/{message_id}/feedback", response_model=FeedbackResponse)
def create_message_feedback(
    message_id: int,
    request: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from ..models.message import Message
    
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    session = db.query(SessionModel).filter(
        SessionModel.id == message.session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=403, detail="无权限")
    
    feedback = SessionFeedback(
        session_id=message.session_id,
        message_id=message_id,
        user_id=current_user.id,
        rating=request.rating,
        feedback_type=request.feedback_type,
        feedback_text=request.feedback_text
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return FeedbackResponse.model_validate(feedback)
