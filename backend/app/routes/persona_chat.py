"""
医生分身对话式采集 API 路由

Phase 3: 对话式采集医生特征，生成 ai_persona_prompt
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import json

from ..database import get_db
from ..models.doctor import Doctor
from ..models.admin_user import AdminUser
from ..services.persona_collection_service import PersonaCollectionService, CollectionState
from .admin_auth import get_current_admin

router = APIRouter(prefix="/admin/doctors", tags=["admin-persona-chat"])


class PersonaChatRequest(BaseModel):
    """对话式采集请求"""
    message: str
    state: Optional[str] = None  # JSON 序列化的 CollectionState


@router.post("/{doctor_id}/persona-chat/start")
async def start_persona_collection(
    doctor_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """
    开始医生分身对话式采集

    返回初始问候语和空状态
    """
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")

    initial_state = CollectionState()
    greeting = await PersonaCollectionService.start_collection(
        doctor_name=doctor.name,
        specialty=doctor.specialty or "全科医学"
    )

    return {
        "message": greeting,
        "state": json.dumps(initial_state.to_dict(), ensure_ascii=False),
        "stage": "greeting",
        "is_complete": False
    }


@router.post("/{doctor_id}/persona-chat")
async def persona_chat_message(
    doctor_id: int,
    request: PersonaChatRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """
    对话式采集 - 处理消息并更新状态

    支持的操作：
    - 接收用户输入
    - 返回下一阶段问题
    - 完成时生成 ai_persona_prompt
    """
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")

    # 解析状态
    try:
        state_dict = json.loads(request.state) if request.state else {}
        state = CollectionState.from_dict(state_dict)
    except:
        state = CollectionState()

    # 处理输入
    result = await PersonaCollectionService.process_input(
        user_input=request.message,
        state=state,
        doctor_name=doctor.name,
        specialty=doctor.specialty or "全科医学"
    )

    # 如果完成，保存到医生记录
    if result["is_complete"] and result["generated_prompt"]:
        doctor.ai_persona_prompt = result["generated_prompt"]
        if hasattr(doctor, 'persona_completed'):
            doctor.persona_completed = True
        db.commit()

    return {
        "message": result["response"],
        "state": json.dumps(result["state"], ensure_ascii=False),
        "stage": result["stage"],
        "is_complete": result["is_complete"],
        "generated_prompt": result.get("generated_prompt")
    }


@router.get("/{doctor_id}/persona-status")
def get_persona_status(
    doctor_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """获取医生分身配置状态"""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")

    return {
        "doctor_id": doctor.id,
        "name": doctor.name,
        "persona_completed": getattr(doctor, 'persona_completed', False),
        "has_persona_prompt": bool(doctor.ai_persona_prompt),
        "ai_model": doctor.ai_model,
        "ai_temperature": doctor.ai_temperature
    }


@router.post("/{doctor_id}/persona-chat/reset")
async def reset_persona_collection(
    doctor_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """重置医生分身采集状态"""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")

    if hasattr(doctor, 'persona_completed'):
        doctor.persona_completed = False
    doctor.ai_persona_prompt = None
    db.commit()

    return {
        "message": "医生分身配置已重置",
        "doctor_id": doctor_id
    }
