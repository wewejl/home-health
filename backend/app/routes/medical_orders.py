"""
医嘱执行监督 API 路由

包含：
- 医嘱 CRUD
- 家属关系管理 (放在参数化路由之前)
- 任务查询
- 打卡操作
- 依从性查询

路由顺序很重要：固定路径（如 /family-bonds）必须在参数化路径（如 /{order_id}）之前定义
"""
import logging
from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.medical_order import (
    MedicalOrder, TaskInstance, CompletionRecord, OrderStatus, TaskStatus
)
from ..schemas.medical_order import (
    MedicalOrderCreateRequest, MedicalOrderUpdateRequest, MedicalOrderResponse,
    ActivateOrderRequest, TaskInstanceResponse, TaskListResponse,
    CompletionRecordRequest, CompletionRecordResponse,
    ComplianceResponse, WeeklyComplianceResponse,
    FamilyBondCreateRequest, FamilyBondResponse
)
from ..services.medical_order_service import MedicalOrderService
from ..services.compliance_service import ComplianceService

router = APIRouter(prefix="/medical-orders", tags=["medical-orders"])
logger = logging.getLogger(__name__)


# ============= 医嘱 CRUD =============

@router.post("", response_model=MedicalOrderResponse, status_code=status.HTTP_201_CREATED)
def create_medical_order(
    request: MedicalOrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建医嘱（草稿状态）

    通常由 AI 从问诊对话自动生成，或由医生手动创建
    """
    service = MedicalOrderService(db)

    # 验证患者是当前用户或医生为患者创建
    # TODO: 添加医生权限检查

    order_data = request.model_dump()
    order_data["patient_id"] = current_user.id  # 暂时只允许为自己创建

    order = service.create_draft_order(order_data)

    return MedicalOrderResponse.model_validate(order)


@router.get("", response_model=List[MedicalOrderResponse])
def get_medical_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的医嘱列表"""
    query = db.query(MedicalOrder).filter(
        MedicalOrder.patient_id == current_user.id
    )

    if status_filter:
        query = query.filter(MedicalOrder.status == OrderStatus(status_filter))

    orders = query.order_by(MedicalOrder.created_at.desc()).all()

    return [MedicalOrderResponse.model_validate(o) for o in orders]


# ============= 家属关系管理 =============
# 重要：固定路径必须在参数化路径之前定义！

@router.post("/family-bonds", response_model=FamilyBondResponse, status_code=status.HTTP_201_CREATED)
def create_family_bond(
    request: FamilyBondCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建家属关系

    允许患者为自己添加家属，或家属主动关联患者
    """
    from ..models.medical_order import FamilyBond

    # 查找家属用户
    family_member = db.query(User).filter(
        User.phone == request.family_member_phone
    ).first()

    if not family_member:
        raise HTTPException(status_code=404, detail="家属用户不存在")

    # 不能与自己建立关系
    if family_member.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能与自己建立关系")

    # 检查是否已存在关系
    existing = db.query(FamilyBond).filter(
        FamilyBond.patient_id == request.patient_id,
        FamilyBond.family_member_id == family_member.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="关系已存在")

    # 验证患者权限（暂时只允许为自己创建）
    if request.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="暂不支持为他人创建家属关系")

    bond = FamilyBond(
        patient_id=request.patient_id,
        family_member_id=family_member.id,
        relationship_type=request.relationship,
        notification_level=request.notification_level
    )

    db.add(bond)
    db.commit()
    db.refresh(bond)

    # 获取患者信息
    patient = db.query(User).filter(User.id == bond.patient_id).first()

    return FamilyBondResponse(
        id=bond.id,
        patient_id=bond.patient_id,
        family_member_id=bond.family_member_id,
        relationship_type=bond.relationship_type,
        notification_level=bond.notification_level.value,
        family_member_name=family_member.nickname,
        family_member_phone=family_member.phone,
        patient_name=patient.nickname if patient else None
    )


@router.get("/family-bonds", response_model=List[FamilyBondResponse])
def get_family_bonds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取我的家属关系

    返回：
    - 我作为患者的关系（别人关注我）
    - 我作为家属的关系（我关注别人）
    """
    from ..models.medical_order import FamilyBond

    results = []

    # 查找我是家属的关系（我关注的患者）
    as_family = db.query(FamilyBond).filter(
        FamilyBond.family_member_id == current_user.id
    ).all()

    for bond in as_family:
        patient = db.query(User).filter(User.id == bond.patient_id).first()
        results.append(FamilyBondResponse(
            id=bond.id,
            patient_id=bond.patient_id,
            family_member_id=bond.family_member_id,
            relationship_type=bond.relationship_type,
            notification_level=bond.notification_level.value,
            family_member_name=current_user.nickname,
            family_member_phone=current_user.phone,
            patient_name=patient.nickname if patient else "未知"
        ))

    # 查找我是患者的关系（别人关注我）
    as_patient = db.query(FamilyBond).filter(
        FamilyBond.patient_id == current_user.id
    ).all()

    for bond in as_patient:
        member = db.query(User).filter(User.id == bond.family_member_id).first()
        results.append(FamilyBondResponse(
            id=bond.id,
            patient_id=bond.patient_id,
            family_member_id=bond.family_member_id,
            relationship_type=bond.relationship_type,
            notification_level=bond.notification_level.value,
            family_member_name=member.nickname if member else "未知",
            family_member_phone=member.phone if member else None,
            patient_name=current_user.nickname
        ))

    return results


@router.delete("/family-bonds/{bond_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_family_bond(
    bond_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除家属关系

    只能删除自己是家属的关系
    """
    from ..models.medical_order import FamilyBond

    bond = db.query(FamilyBond).filter(
        FamilyBond.id == bond_id
    ).first()

    if not bond:
        raise HTTPException(status_code=404, detail="关系不存在")

    # 验证权限：只能删除自己作为家属的关系
    if bond.family_member_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己作为家属的关系")

    db.delete(bond)
    db.commit()

    return None


@router.get("/family-bonds/{patient_id}/tasks", response_model=TaskListResponse)
def get_family_member_tasks(
    patient_id: int,
    task_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取家属的任务列表

    需要验证当前用户是该患者的家属
    """
    from ..models.medical_order import FamilyBond

    # 验证有权查看
    bond = db.query(FamilyBond).filter(
        FamilyBond.patient_id == patient_id,
        FamilyBond.family_member_id == current_user.id
    ).first()

    if not bond:
        raise HTTPException(status_code=403, detail="无权查看此患者信息")

    # 获取任务
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
        return data

    total = len(tasks)
    completed_count = len(completed)

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


# ============= 医嘱详情操作 (参数化路由) =============

@router.get("/{order_id}", response_model=MedicalOrderResponse)
def get_medical_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取医嘱详情"""
    order = db.query(MedicalOrder).filter(
        MedicalOrder.id == order_id,
        MedicalOrder.patient_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    return MedicalOrderResponse.model_validate(order)


@router.put("/{order_id}", response_model=MedicalOrderResponse)
def update_medical_order(
    order_id: int,
    request: MedicalOrderUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新医嘱（仅草稿状态可编辑）"""
    order = db.query(MedicalOrder).filter(
        MedicalOrder.id == order_id,
        MedicalOrder.patient_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    if order.status != OrderStatus.DRAFT:
        raise HTTPException(status_code=400, detail="只有草稿状态的医嘱可以编辑")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)

    db.commit()
    db.refresh(order)

    return MedicalOrderResponse.model_validate(order)


@router.post("/{order_id}/activate", response_model=MedicalOrderResponse)
def activate_medical_order(
    order_id: int,
    request: ActivateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """激活医嘱（生成任务实例）"""
    if not request.confirm:
        raise HTTPException(status_code=400, detail="需要确认激活")

    service = MedicalOrderService(db)

    # 验证权限
    order = db.query(MedicalOrder).filter(
        MedicalOrder.id == order_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    if order.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此医嘱")

    activated = service.activate_order(order_id)

    return MedicalOrderResponse.model_validate(activated)


# ============= 任务查询 =============

@router.get("/tasks/{task_date}", response_model=TaskListResponse)
def get_daily_tasks(
    task_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定日期的任务列表

    返回按状态分组的任务
    """
    tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == current_user.id,
        TaskInstance.scheduled_date == task_date
    ).all()

    pending = [t for t in tasks if t.status == TaskStatus.PENDING]
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    overdue = [t for t in tasks if t.status == TaskStatus.OVERDUE]

    # 构建响应
    def build_response(task):
        data = TaskInstanceResponse.model_validate(task).model_dump()
        if task.order:
            data["order_title"] = task.order.title
            data["order_type"] = task.order.order_type.value
        return data

    # 计算依从性
    total = len(tasks)
    completed_count = len(completed)
    overdue_count = len(overdue)
    pending_count = len(pending)
    rate = completed_count / total if total > 0 else 0

    summary = ComplianceResponse(
        date=task_date.isoformat(),
        total=total,
        completed=completed_count,
        overdue=overdue_count,
        pending=pending_count,
        rate=round(rate, 2)
    )

    return TaskListResponse(
        date=task_date.isoformat(),
        pending=[build_response(t) for t in pending],
        completed=[build_response(t) for t in completed],
        overdue=[build_response(t) for t in overdue],
        summary=summary
    )


@router.get("/tasks/{task_date}/pending", response_model=List[TaskInstanceResponse])
def get_pending_tasks(
    task_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取待完成任务"""
    tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == current_user.id,
        TaskInstance.scheduled_date == task_date,
        TaskInstance.status == TaskStatus.PENDING
    ).order_by(TaskInstance.scheduled_time).all()

    return [TaskInstanceResponse.model_validate(t) for t in tasks]


# ============= 打卡操作 =============

@router.post("/tasks/{task_id}/complete", response_model=CompletionRecordResponse)
def complete_task(
    task_id: int,
    request: CompletionRecordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    完成任务打卡

    支持多种打卡类型：
    - check: 简单打卡确认
    - photo: 照片证明
    - value: 数值录入（如血糖）
    - medication: 用药记录
    """
    task = db.query(TaskInstance).filter(
        TaskInstance.id == task_id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")

    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="任务已完成")

    # 覆盖 request 中的 task_instance_id
    request.task_instance_id = task_id

    # 创建打卡记录
    record = CompletionRecord(
        task_instance_id=task_id,
        completed_by=current_user.id,
        completion_type=request.completion_type,
        value=request.value,
        photo_url=request.photo_url,
        notes=request.notes
    )

    # 更新任务状态
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    task.completion_notes = request.notes

    db.add(record)
    db.commit()
    db.refresh(record)

    return CompletionRecordResponse.model_validate(record)


# ============= 依从性查询 =============

@router.get("/compliance/daily", response_model=ComplianceResponse)
def get_daily_compliance(
    task_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定日期的依从性"""
    service = ComplianceService(db)
    compliance = service.calculate_daily_compliance(current_user.id, task_date)
    return ComplianceResponse(**compliance)


@router.get("/compliance/weekly", response_model=WeeklyComplianceResponse)
def get_weekly_compliance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取近7天依从性趋势"""
    service = ComplianceService(db)
    weekly = service.calculate_weekly_compliance(current_user.id)
    return WeeklyComplianceResponse(**weekly)


@router.get("/compliance/order/{order_id}", response_model=dict)
def get_order_compliance(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取医嘱依从性详情"""
    # 验证权限
    order = db.query(MedicalOrder).filter(
        MedicalOrder.id == order_id,
        MedicalOrder.patient_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="医嘱不存在")

    service = ComplianceService(db)
    return service.calculate_order_compliance(order_id)


@router.get("/compliance/abnormal", response_model=List[dict])
def get_abnormal_records(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取异常记录"""
    service = ComplianceService(db)
    return service.get_abnormal_records(current_user.id, days)


# ============= 预警管理 =============

@router.get("/alerts", response_model=List[dict])
def get_alerts(
    active_only: bool = Query(True, description="是否只返回未确认的预警"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的预警列表"""
    from ..services.alert_service import AlertService
    from ..models.medical_order import Alert, AlertSeverity

    query = db.query(Alert).filter(Alert.patient_id == current_user.id)

    if active_only:
        query = query.filter(Alert.is_acknowledged == False)

    alerts = query.order_by(
        Alert.severity.desc(),
        Alert.created_at.desc()
    ).limit(limit).all()

    return [
        {
            "id": alert.id,
            "type": alert.alert_type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "value_data": alert.value_data,
            "is_acknowledged": alert.is_acknowledged,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "task_title": alert.task_instance.order.title if alert.task_instance and alert.task_instance.order else None
        }
        for alert in alerts
    ]


@router.post("/alerts/{alert_id}/acknowledge", status_code=status.HTTP_200_OK)
def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """确认预警"""
    from ..services.alert_service import AlertService

    service = AlertService(db)
    alert = service.acknowledge_alert(alert_id, current_user.id)

    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")

    return {
        "id": alert.id,
        "acknowledged": True,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
    }


@router.post("/alerts/check", response_model=List[dict])
def check_and_create_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    检查并创建预警

    触发检查：
    - 超时任务
    - 低依从性
    """
    from ..services.alert_service import AlertService
    from ..models.medical_order import Alert, AlertSeverity

    service = AlertService(db)

    # 检查超时任务
    task_alerts = service.check_overdue_tasks(current_user.id)

    # 检查依从性
    compliance_alert = service.check_low_compliance(current_user.id)
    if compliance_alert:
        db.add(compliance_alert)
        db.commit()
        task_alerts.append(compliance_alert)

    return [
        {
            "id": alert.id,
            "type": alert.alert_type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "created_at": alert.created_at.isoformat() if alert.created_at else None
        }
        for alert in task_alerts
    ]
