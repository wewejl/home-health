"""
医生工作台 API 路由

医生角色专用功能：
- 查看患者列表
- 查看患者对话记录
- 创建和管理医嘱
- 查看患者任务执行情况
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List
from datetime import datetime, timedelta, date

from ..database import get_db
from ..models.admin_user import AdminUser
from ..models.user import User
from ..models.session import Session as ConsultationSession
from ..models.message import Message, SenderType
from ..models.medical_order import (
    MedicalOrder, TaskInstance, OrderStatus, OrderType,
    ScheduleType, TaskStatus
)
from .admin_auth import get_current_doctor
from ..schemas.admin import (
    PatientListItem, PatientDetailResponse,
    ConsultationSession as ConsultationSessionSchema,
    ConsultationMessage, ConsultationDetailResponse
)
from ..schemas.medical_order import (
    MedicalOrderCreateRequest, MedicalOrderResponse,
    TaskInstanceResponse, TaskListResponse
)
from ..services.medical_order_service import MedicalOrderService

router = APIRouter(prefix="/api/doctor", tags=["doctor-workstation"])


# ============= 辅助函数 =============

def calculate_age(birthday: Optional[date]) -> Optional[int]:
    """根据生日计算年龄"""
    if not birthday:
        return None
    today = date.today()
    return today.year - birthday.year - (
        (today.month, today.day) < (birthday.month, birthday.day)
    )


# ============= 患者管理 =============

@router.get("/patients", response_model=List[PatientListItem])
def get_patients(
    search: Optional[str] = Query(None, description="搜索关键词（姓名/手机号）"),
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取医生的患者列表

    返回与该医生管理的 AI 分身有过咨询的患者
    """
    # TODO: 关联医生与 AI 分身后，这里需要过滤
    # 当前返回所有有咨询记录的患者

    # 获取所有有咨询记录的患者 ID
    patient_ids = db.query(ConsultationSession.user_id).distinct().all()
    patient_ids = [p[0] for p in patient_ids]

    if not patient_ids:
        return []

    # 构建查询
    query = db.query(User).filter(User.id.in_(patient_ids))

    # 搜索过滤
    if search:
        query = query.filter(
            (User.nickname.ilike(f"%{search}%")) |
            (User.phone.ilike(f"%{search}%"))
        )

    patients = query.order_by(desc(User.created_at)).all()

    # 为每个患者计算统计数据
    result = []
    for patient in patients:
        # 最后咨询时间
        last_session = db.query(ConsultationSession).filter(
            ConsultationSession.user_id == patient.id
        ).order_by(desc(ConsultationSession.updated_at)).first()

        # 进行中的医嘱数
        active_orders = db.query(MedicalOrder).filter(
            MedicalOrder.patient_id == patient.id,
            MedicalOrder.status == OrderStatus.ACTIVE
        ).count()

        # 最近7天完成率
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_tasks = db.query(TaskInstance).filter(
            TaskInstance.patient_id == patient.id,
            TaskInstance.scheduled_date >= week_ago.date()
        ).all()

        completed_count = sum(1 for t in week_tasks if t.status == TaskStatus.COMPLETED)
        completion_rate = completed_count / len(week_tasks) if week_tasks else 0.0

        result.append(PatientListItem(
            id=patient.id,
            nickname=patient.nickname,
            phone=patient.phone,
            gender=patient.gender,
            age=calculate_age(patient.birthday),
            last_consultation_at=last_session.updated_at if last_session else None,
            active_orders_count=active_orders,
            completion_rate=round(completion_rate, 2)
        ))

    return result


@router.get("/patients/{patient_id}", response_model=PatientDetailResponse)
def get_patient_detail(
    patient_id: int,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取患者详情"""
    patient = db.query(User).filter(User.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 最后咨询时间
    last_session = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient_id
    ).order_by(desc(ConsultationSession.updated_at)).first()

    # 进行中的医嘱数
    active_orders = db.query(MedicalOrder).filter(
        MedicalOrder.patient_id == patient_id,
        MedicalOrder.status == OrderStatus.ACTIVE
    ).count()

    # 最近7天完成率
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == patient_id,
        TaskInstance.scheduled_date >= week_ago.date()
    ).all()

    completed_count = sum(1 for t in week_tasks if t.status == TaskStatus.COMPLETED)
    completion_rate = completed_count / len(week_tasks) if week_tasks else 0.0

    return PatientDetailResponse(
        id=patient.id,
        nickname=patient.nickname,
        phone=patient.phone,
        gender=patient.gender,
        age=calculate_age(patient.birthday),
        avatar_url=patient.avatar_url,
        is_profile_completed=patient.is_profile_completed,
        last_consultation_at=last_session.updated_at if last_session else None,
        active_orders_count=active_orders,
        completion_rate=round(completion_rate, 2),
        created_at=patient.created_at
    )


# ============= 对话记录 =============

@router.get("/patients/{patient_id}/consultations", response_model=List[ConsultationSessionSchema])
def get_patient_consultations(
    patient_id: int,
    limit: int = Query(10, ge=1, le=50),
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取患者的对话列表

    返回该患者的所有对话会话
    """
    # 验证患者存在
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 获取对话会话
    sessions = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient_id
    ).order_by(ConsultationSession.updated_at.desc()).limit(limit).all()

    # 为每个会话计算消息数量
    result = []
    for session in sessions:
        message_count = db.query(Message).filter(
            Message.session_id == session.id
        ).count()

        result.append(ConsultationSessionSchema(
            id=session.id,
            user_id=session.user_id,
            doctor_id=session.doctor_id,
            agent_type=session.agent_type,
            last_message=session.last_message,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count
        ))

    return result


@router.get("/consultations/{session_id}", response_model=ConsultationDetailResponse)
def get_consultation_detail(
    session_id: str,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取对话详情（含消息列表）

    返回指定会话的所有消息
    """
    # 获取会话
    session = db.query(ConsultationSession).filter(
        ConsultationSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="对话不存在")

    # 获取消息
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at).all()

    return ConsultationDetailResponse(
        session=ConsultationSessionSchema(
            id=session.id,
            user_id=session.user_id,
            doctor_id=session.doctor_id,
            agent_type=session.agent_type,
            last_message=session.last_message,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=len(messages)
        ),
        messages=[
            ConsultationMessage(
                id=msg.id,
                sender=msg.sender.value,
                content=msg.content,
                created_at=msg.created_at
            )
            for msg in messages
        ]
    )


# ============= 医嘱管理 =============

@router.post("/orders", response_model=MedicalOrderResponse, status_code=201)
def create_order(
    request: MedicalOrderCreateRequest,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    为患者创建医嘱

    doctor_id 自动设置为当前医生
    """
    # 验证患者存在
    patient = db.query(User).filter(User.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    service = MedicalOrderService(db)

    order_data = request.model_dump()
    order_data["doctor_id"] = doctor.id  # 设置为当前医生

    order = service.create_draft_order(order_data)

    return MedicalOrderResponse.model_validate(order)


@router.get("/patients/{patient_id}/orders", response_model=List[MedicalOrderResponse])
def get_patient_orders(
    patient_id: int,
    status_filter: Optional[str] = None,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取患者的医嘱列表"""
    query = db.query(MedicalOrder).filter(
        MedicalOrder.patient_id == patient_id
    )

    if status_filter:
        try:
            status = OrderStatus(status_filter)
            query = query.filter(MedicalOrder.status == status)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的状态值")

    orders = query.order_by(MedicalOrder.created_at.desc()).all()

    return [MedicalOrderResponse.model_validate(o) for o in orders]


@router.put("/orders/{order_id}", response_model=MedicalOrderResponse)
def update_order(
    order_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    end_date: Optional[date] = None,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """更新医嘱"""
    order = db.query(MedicalOrder).filter(MedicalOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    if title is not None:
        order.title = title
    if description is not None:
        order.description = description
    if end_date is not None:
        order.end_date = end_date

    db.commit()
    db.refresh(order)

    return MedicalOrderResponse.model_validate(order)


@router.delete("/orders/{order_id}")
def delete_order(
    order_id: int,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """停用医嘱"""
    order = db.query(MedicalOrder).filter(MedicalOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    order.status = OrderStatus.STOPPED
    db.commit()

    return {"message": "医嘱已停用"}


# ============= 任务执行情况 =============

@router.get("/patients/{patient_id}/tasks", response_model=TaskListResponse)
def get_patient_tasks(
    patient_id: int,
    task_date: date,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取患者指定日期的任务列表"""
    tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == patient_id,
        TaskInstance.scheduled_date == task_date
    ).all()

    pending = [t for t in tasks if t.status == TaskStatus.PENDING]
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    overdue = [t for t in tasks if t.status == TaskStatus.OVERDUE]

    def build_response(task):
        data = TaskInstanceResponse.model_validate(task).model_dump()
        if task.order:
            data["order_title"] = task.order.title
            data["order_type"] = task.order.order_type.value
        return TaskInstanceResponse(**data)

    total = len(tasks)
    completed_count = len(completed)

    from ..schemas.medical_order import ComplianceResponse

    summary = ComplianceResponse(
        date=task_date.isoformat(),
        total=total,
        completed=completed_count,
        overdue=len(overdue),
        pending=len(pending),
        rate=round(completed_count / total, 2) if total > 0 else 0
    )

    return TaskListResponse(
        date=task_date.isoformat(),
        pending=[build_response(t) for t in pending],
        completed=[build_response(t) for t in completed],
        overdue=[build_response(t) for t in overdue],
        summary=summary
    )
