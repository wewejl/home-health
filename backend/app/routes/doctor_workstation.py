"""
医生工作台 API 路由

医生角色专用功能：
- 查看患者列表
- 查看患者对话记录
- 创建和管理医嘱
- 查看患者任务执行情况
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc, func
from typing import Optional, List
from datetime import datetime, timedelta, date

from ..database import get_db
from ..models.admin_user import AdminUser
from ..models.doctor import Doctor
from ..models.user import User
from ..models.doctor_patient_relationship import DoctorPatientRelationship
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
    ConsultationMessage, ConsultationDetailResponse,
    DoctorInfoResponse, ManagedDoctorInfo,
    PatientAssignRequest, PatientAssignResponse, AssignablePatientResponse,
    PatientStatsResponse
)
from ..schemas.medical_order import (
    MedicalOrderCreateRequest, MedicalOrderResponse,
    TaskInstanceResponse, TaskListResponse, ActivateOrderRequest
)
from ..services.medical_order_service import MedicalOrderService

router = APIRouter(prefix="/api/doctor", tags=["doctor-workstation"])


# ============= 患者统计 =============

@router.get("/patient-stats", response_model=PatientStatsResponse)
def get_patient_stats(
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取患者统计数据

    返回：总患者数、活跃患者数、今日新增患者数、低依从性患者数
    """
    # 获取可访问的患者 ID 列表
    patient_ids = _get_accessible_patient_ids(doctor.id, db)

    if not patient_ids:
        return PatientStatsResponse(
            total=0,
            active=0,
            new_today=0,
            low_compliance=0
        )

    # 总患者数
    total = len(patient_ids)

    # 活跃患者数（有进行中医嘱）
    active = db.query(MedicalOrder).filter(
        MedicalOrder.patient_id.in_(patient_ids),
        MedicalOrder.status == OrderStatus.ACTIVE
    ).distinct(MedicalOrder.patient_id).count()

    # 今日新增患者数（今天创建的关联关系）
    from ..models.doctor_patient_relationship import DoctorPatientRelationship
    today = date.today()
    new_today = db.query(DoctorPatientRelationship).filter(
        DoctorPatientRelationship.doctor_id == doctor.id,
        DoctorPatientRelationship.is_active == True,
        func.date(DoctorPatientRelationship.created_at) == today
    ).count()

    # 低依从性患者数（最近7天完成率低于50%）- 优化为单个查询
    week_ago = datetime.utcnow() - timedelta(days=7)

    # 获取所有患者的任务完成情况（单个查询）
    week_tasks = db.query(
        TaskInstance.patient_id,
        TaskInstance.status
    ).filter(
        TaskInstance.patient_id.in_(patient_ids),
        TaskInstance.scheduled_date >= week_ago.date()
    ).all()

    # 在内存中计算低依从性患者数
    patient_task_stats = {}
    for pid, status in week_tasks:
        if pid not in patient_task_stats:
            patient_task_stats[pid] = {"total": 0, "completed": 0}
        patient_task_stats[pid]["total"] += 1
        if status == TaskStatus.COMPLETED:
            patient_task_stats[pid]["completed"] += 1

    low_compliance = sum(
        1 for stats in patient_task_stats.values()
        if stats["total"] > 0 and stats["completed"] / stats["total"] < 0.5
    )

    return PatientStatsResponse(
        total=total,
        active=active,
        new_today=new_today,
        low_compliance=low_compliance
    )


# ============= 医生信息 =============

@router.get("/me", response_model=DoctorInfoResponse)
def get_doctor_info(
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取当前医生信息，包括管理的 AI 分身列表
    """
    # 使用 joinedload 预加载 department（优化 N+1 查询）
    from ..models.doctor import Doctor
    doctor_with_dept = db.query(AdminUser).options(
        joinedload(AdminUser.department)
    ).filter(AdminUser.id == doctor.id).first()

    # 获取管理的 AI 分身详情 - 预加载 department
    managed_doctors = []
    if doctor_with_dept.managed_doctor_ids:
        doctors = db.query(Doctor).options(
            joinedload(Doctor.department)
        ).filter(
            Doctor.id.in_(doctor_with_dept.managed_doctor_ids)
        ).all()

        managed_doctors = [
            ManagedDoctorInfo(
                id=d.id,
                name=d.name,
                title=d.title,
                department=d.department.name if d.department else None
            )
            for d in doctors
        ]

    return DoctorInfoResponse(
        id=doctor_with_dept.id,
        username=doctor_with_dept.username,
        email=doctor_with_dept.email,
        role=doctor_with_dept.role,
        department_id=doctor_with_dept.department_id,
        department_name=doctor_with_dept.department.name if doctor_with_dept.department else None,
        managed_doctors=managed_doctors
    )


# ============= 辅助函数 =============

def calculate_age(birthday: Optional[date]) -> Optional[int]:
    """根据生日计算年龄"""
    if not birthday:
        return None
    today = date.today()
    return today.year - birthday.year - (
        (today.month, today.day) < (birthday.month, birthday.day)
    )


def _verify_patient_access(
    doctor_id: int,
    patient_id: int,
    db: Session,
    check_relationship_only: bool = False
) -> bool:
    """
    验证医生是否有权访问指定患者

    医生可以访问以下患者：
    1. 通过 doctor_patient_relationships 表关联的活跃患者
    2. 同科室内 AI 分身接待过的患者（通过 admin_users.department_id 关联）

    Args:
        doctor_id: 医生 ID (admin_users.id)
        patient_id: 患者 ID (users.id)
        db: 数据库会话
        check_relationship_only: 是否仅检查显式关联，不检查科室关联

    Returns:
        bool: 是否有访问权限
    """
    # 1. 检查显式关联关系
    relationship = db.query(DoctorPatientRelationship).filter(
        DoctorPatientRelationship.doctor_id == doctor_id,
        DoctorPatientRelationship.patient_id == patient_id,
        DoctorPatientRelationship.is_active == True
    ).first()

    if relationship:
        return True

    if check_relationship_only:
        return False

    # 2. 检查科室关联：医生管理的 AI 分身接待过的患者
    doctor = db.query(AdminUser).filter(AdminUser.id == doctor_id).first()
    if not doctor or not doctor.managed_doctor_ids:
        return False

    # 检查患者是否咨询过医生管理的 AI 分身
    session_exists = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient_id,
        ConsultationSession.doctor_id.in_(doctor.managed_doctor_ids)
    ).first()

    return session_exists is not None


def _get_accessible_patient_ids(doctor_id: int, db: Session) -> List[int]:
    """
    获取医生可访问的所有患者 ID 列表

    Returns:
        List[int]: 患者 ID 列表
    """
    doctor = db.query(AdminUser).filter(AdminUser.id == doctor_id).first()
    if not doctor:
        return []

    patient_ids = set()

    # 1. 获取显式关联的患者
    relationships = db.query(DoctorPatientRelationship).filter(
        DoctorPatientRelationship.doctor_id == doctor_id,
        DoctorPatientRelationship.is_active == True
    ).all()

    for rel in relationships:
        patient_ids.add(rel.patient_id)

    # 2. 获取科室关联的患者（通过管理的 AI 分身）
    if doctor.managed_doctor_ids:
        session_patient_ids = db.query(ConsultationSession.user_id).filter(
            ConsultationSession.doctor_id.in_(doctor.managed_doctor_ids)
        ).distinct().all()

        for (pid,) in session_patient_ids:
            patient_ids.add(pid)

    return list(patient_ids)


# ============= 患者管理 =============

@router.get("/patients", response_model=List[PatientListItem])
def get_patients(
    search: Optional[str] = Query(None, description="搜索关键词（姓名/手机号）"),
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取医生的患者列表

    返回与该医生有关联的患者，包括：
    1. 通过 doctor_patient_relationships 表显式关联的患者
    2. 同科室内 AI 分身接待过的患者
    """
    # 获取可访问的患者 ID 列表
    patient_ids = _get_accessible_patient_ids(doctor.id, db)

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

    # 批量获取统计数据（优化为 3 个查询）
    patient_id_list = [p.id for p in patients]

    # 1. 最后咨询时间（单个查询）
    last_sessions = db.query(
        ConsultationSession.user_id,
        func.max(ConsultationSession.updated_at).label('last_updated')
    ).filter(
        ConsultationSession.user_id.in_(patient_id_list)
    ).group_by(ConsultationSession.user_id).all()

    # 构建 patient_id -> last_session_updated_at 映射
    session_map = {user_id: last_updated for user_id, last_updated in last_sessions}

    # 2. 进行中的医嘱数（单个查询）
    active_orders_counts = db.query(
        MedicalOrder.patient_id,
        func.count(MedicalOrder.id)
    ).filter(
        MedicalOrder.patient_id.in_(patient_id_list),
        MedicalOrder.status == OrderStatus.ACTIVE
    ).group_by(MedicalOrder.patient_id).all()

    orders_map = {pid: count for pid, count in active_orders_counts}

    # 3. 最近7天完成率（单个查询）
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_tasks = db.query(
        TaskInstance.patient_id,
        TaskInstance.status
    ).filter(
        TaskInstance.patient_id.in_(patient_id_list),
        TaskInstance.scheduled_date >= week_ago.date()
    ).all()

    # 在内存中计算每个患者的完成率
    task_stats = {}
    for pid, status in week_tasks:
        if pid not in task_stats:
            task_stats[pid] = {"total": 0, "completed": 0}
        task_stats[pid]["total"] += 1
        if status == TaskStatus.COMPLETED:
            task_stats[pid]["completed"] += 1

    # 构建结果
    result = []
    for patient in patients:
        completed_count = task_stats.get(patient.id, {}).get("completed", 0)
        total_tasks = task_stats.get(patient.id, {}).get("total", 0)
        completion_rate = completed_count / total_tasks if total_tasks > 0 else 0.0

        result.append(PatientListItem(
            id=patient.id,
            nickname=patient.nickname,
            phone=patient.phone,
            gender=patient.gender,
            age=calculate_age(patient.birthday),
            last_consultation_at=session_map.get(patient.id),
            active_orders_count=orders_map.get(patient.id, 0),
            completion_rate=round(completion_rate, 2)
        ))

    return result


# ============= 患者分配管理 =============
# 注意：这些路由必须定义在 /patients/{patient_id} 之前，否则会被参数化路由拦截

@router.post("/patients/assign", response_model=PatientAssignResponse, status_code=201)
def assign_patient(
    request: PatientAssignRequest,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    分配患者给当前医生

    创建医生与患者之间的显式关联关系。
    如果关联已存在，则更新其状态为活跃。

    Args:
        request: 包含 patient_id, relationship_type, notes

    Returns:
        PatientAssignResponse: 创建的关联关系
    """
    from ..models.doctor_patient_relationship import RelationshipType

    # 验证患者存在
    patient = db.query(User).filter(User.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 检查是否已存在关联关系
    existing_relationship = db.query(DoctorPatientRelationship).filter(
        DoctorPatientRelationship.doctor_id == doctor.id,
        DoctorPatientRelationship.patient_id == request.patient_id
    ).first()

    if existing_relationship:
        # 如果关联已存在但非活跃，则重新激活
        if not existing_relationship.is_active:
            existing_relationship.is_active = True
            existing_relationship.relationship_type = request.relationship_type
            existing_relationship.notes = request.notes
            db.commit()
            db.refresh(existing_relationship)
            return PatientAssignResponse.model_validate(existing_relationship)

        # 如果关联已是活跃状态，更新信息
        existing_relationship.relationship_type = request.relationship_type
        existing_relationship.notes = request.notes
        db.commit()
        db.refresh(existing_relationship)
        return PatientAssignResponse.model_validate(existing_relationship)

    # 创建新的关联关系
    relationship = DoctorPatientRelationship(
        doctor_id=doctor.id,
        patient_id=request.patient_id,
        relationship_type=request.relationship_type,
        is_active=True,
        notes=request.notes
    )

    db.add(relationship)
    db.commit()
    db.refresh(relationship)

    return PatientAssignResponse.model_validate(relationship)


@router.delete("/patients/{patient_id}/unassign")
def unassign_patient(
    patient_id: int,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    解除与患者的关联关系

    将医生与患者之间的关联关系标记为非活跃。
    不会删除关联记录，只是禁用该关联。

    Args:
        patient_id: 患者 ID

    Returns:
        成功消息
    """
    # 查找活跃的关联关系
    relationship = db.query(DoctorPatientRelationship).filter(
        DoctorPatientRelationship.doctor_id == doctor.id,
        DoctorPatientRelationship.patient_id == patient_id,
        DoctorPatientRelationship.is_active == True
    ).first()

    if not relationship:
        raise HTTPException(status_code=404, detail="未找到与该患者的关联关系")

    # 停用关联关系
    relationship.is_active = False
    db.commit()

    return {"message": "已解除与该患者的关联关系"}


@router.get("/patients/assignable", response_model=List[AssignablePatientResponse])
def get_assignable_patients(
    search: Optional[str] = Query(None, description="搜索关键词（姓名/手机号）"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    获取可分配的患者列表

    返回系统中所有患者，标记哪些已分配给当前医生。
    支持按姓名或手机号搜索。

    Args:
        search: 搜索关键词
        limit: 返回数量限制

    Returns:
        List[AssignablePatientResponse]: 可分配的患者列表
    """
    # 获取当前医生的已分配患者（包含分配时间）- 优化 N+1 查询
    assigned_relationships = db.query(
        DoctorPatientRelationship.patient_id,
        DoctorPatientRelationship.created_at
    ).filter(
        DoctorPatientRelationship.doctor_id == doctor.id,
        DoctorPatientRelationship.is_active == True
    ).all()

    # 构建 patient_id -> assigned_at 映射
    assigned_map = {pid: created_at for pid, created_at in assigned_relationships}
    assigned_ids = set(assigned_map.keys())

    # 构建查询
    query = db.query(User).filter(User.is_active == True)

    # 搜索过滤
    if search:
        query = query.filter(
            (User.nickname.ilike(f"%{search}%")) |
            (User.phone.ilike(f"%{search}%"))
        )

    # 限制返回数量
    patients = query.order_by(desc(User.created_at)).limit(limit).all()

    # 构建结果
    result = [
        AssignablePatientResponse(
            id=patient.id,
            nickname=patient.nickname,
            phone=patient.phone,
            gender=patient.gender,
            age=calculate_age(patient.birthday),
            is_assigned=patient.id in assigned_ids,
            assigned_at=assigned_map.get(patient.id)
        )
        for patient in patients
    ]

    return result


# ============= 患者详情 =============

@router.get("/patients/{patient_id}", response_model=PatientDetailResponse)
def get_patient_detail(
    patient_id: int,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取患者详情"""
    # 验证访问权限
    if not _verify_patient_access(doctor.id, patient_id, db):
        raise HTTPException(status_code=403, detail="无权访问该患者")

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
    # 验证访问权限
    if not _verify_patient_access(doctor.id, patient_id, db):
        raise HTTPException(status_code=403, detail="无权访问该患者")

    # 验证患者存在
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 获取对话会话
    sessions = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient_id
    ).order_by(ConsultationSession.updated_at.desc()).limit(limit).all()

    session_ids = [s.id for s in sessions]

    # 批量获取消息计数（单个查询）- 优化 N+1 查询
    message_counts = db.query(
        Message.session_id,
        func.count(Message.id)
    ).filter(
        Message.session_id.in_(session_ids)
    ).group_by(Message.session_id).all()

    # 构建 session_id -> message_count 映射
    message_count_map = {sid: count for sid, count in message_counts}

    # 构建结果
    result = [
        ConsultationSessionSchema(
            id=session.id,
            user_id=session.user_id,
            doctor_id=session.doctor_id,
            agent_type=session.agent_type,
            last_message=session.last_message,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count_map.get(session.id, 0)
        )
        for session in sessions
    ]

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

    # 验证访问权限
    if not _verify_patient_access(doctor.id, session.user_id, db):
        raise HTTPException(status_code=403, detail="无权访问该对话")

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
    # 验证访问权限
    if not _verify_patient_access(doctor.id, request.patient_id, db):
        raise HTTPException(status_code=403, detail="无权访问该患者")

    # 验证患者存在
    patient = db.query(User).filter(User.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    service = MedicalOrderService(db)

    order_data = request.model_dump()
    order_data["doctor_id"] = doctor.id  # 设置为当前医生

    order = service.create_draft_order(order_data)

    return MedicalOrderResponse.model_validate(order)


@router.post("/orders/{order_id}/activate", response_model=MedicalOrderResponse)
def activate_order(
    order_id: int,
    request: ActivateOrderRequest,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    激活医嘱

    将草稿状态的医嘱激活，生成任务实例
    """
    if not request.confirm:
        raise HTTPException(status_code=400, detail="需要确认激活")

    service = MedicalOrderService(db)

    # 验证医嘱存在
    order = db.query(MedicalOrder).filter(MedicalOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    # 验证访问权限
    if not _verify_patient_access(doctor.id, order.patient_id, db):
        raise HTTPException(status_code=403, detail="无权访问该患者的医嘱")

    try:
        activated = service.activate_order(order_id)
        return MedicalOrderResponse.model_validate(activated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patients/{patient_id}/orders", response_model=List[MedicalOrderResponse])
def get_patient_orders(
    patient_id: int,
    status_filter: Optional[str] = None,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """获取患者的医嘱列表"""
    # 验证访问权限
    if not _verify_patient_access(doctor.id, patient_id, db):
        raise HTTPException(status_code=403, detail="无权访问该患者")

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
    # 验证访问权限
    if not _verify_patient_access(doctor.id, patient_id, db):
        raise HTTPException(status_code=403, detail="无权访问该患者")

    # 使用 selectinload 预加载 order 关系 - 优化 N+1 查询
    tasks = db.query(TaskInstance).options(
        selectinload(TaskInstance.order)
    ).filter(
        TaskInstance.patient_id == patient_id,
        TaskInstance.scheduled_date == task_date
    ).all()

    pending = [t for t in tasks if t.status == TaskStatus.PENDING]
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    overdue = [t for t in tasks if t.status == TaskStatus.OVERDUE]

    def build_response(task):
        data = TaskInstanceResponse.model_validate(task).model_dump()
        # 现在 task.order 已预加载，不会触发额外查询
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
