"""
远程查房系统 API 路由

提供患者看板和患者详情的查询接口
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.session import Session as SessionModel
from ..models.message import Message, SenderType
from ..models.medical_order import (
    MedicalOrder, TaskInstance, TaskStatus,
    OrderStatus, CompletionRecord, Alert, AlertSeverity, AlertType
)
from ..schemas.rounding import (
    PatientCardResponse, PatientListResponse,
    ChatMessageResponse, RoundingTaskResponse, PatientDetailResponse
)

router = APIRouter(prefix="/rounding", tags=["rounding"])


# ============================================
# 辅助函数
# ============================================

def calculate_completion_rate(total: int, completed: int) -> int:
    """计算完成率"""
    return round((completed / total * 100)) if total > 0 else 0


def get_patient_status(completion_rate: int, has_abnormal_value: bool, overdue_count: int) -> str:
    """判断患者状态"""
    if has_abnormal_value or completion_rate < 50 or overdue_count > 0:
        return "danger"
    if completion_rate < 80 or has_abnormal_value:
        return "warning"
    return "success"


def format_time_ago(dt: datetime) -> str:
    """格式化时间为'X小时前'"""
    if not dt:
        return "未知"

    now = datetime.now(dt.tzinfo)
    diff = now - dt

    if diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}分钟前"
    elif diff < timedelta(hours=24):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}小时前"
    else:
        days = diff.days
        return f"{days}天前"


# ============================================
# 患者列表接口
# ============================================

@router.get("/patients", response_model=PatientListResponse)
def get_rounding_patients(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取远程查房患者列表

    返回当前医生管理的所有患者及其今日状态概览
    """
    # TODO: 这里应该根据医生管理关系过滤患者
    # 暂时返回当前用户作为患者（测试用）
    # 实际应该有 doctor-patient 关系表

    # 获取有活动医嘱的患者（有任务实例的患者）
    today = date.today()

    # 查询今天有任务的患者
    patients_with_tasks = db.query(TaskInstance.patient_id).distinct().all()

    patients_data = []

    for patient_id in [p[0] for p in patients_with_tasks]:
        patient = db.query(User).filter(User.id == patient_id).first()
        if not patient:
            continue

        # 获取今日任务
        today_tasks = db.query(TaskInstance).filter(
            TaskInstance.patient_id == patient_id,
            TaskInstance.scheduled_date == today
        ).all()

        if not today_tasks:
            continue

        total_tasks = len(today_tasks)
        completed_tasks = len([t for t in today_tasks if t.status == TaskStatus.COMPLETED])
        overdue_tasks = len([t for t in today_tasks if t.status == TaskStatus.OVERDUE])
        completion_rate = calculate_completion_rate(total_tasks, completed_tasks)

        # 检查异常数值
        has_abnormal_value = False
        alerts = []

        # 检查今日完成的监测值是否异常
        completed_records = db.query(CompletionRecord).join(TaskInstance).filter(
            TaskInstance.patient_id == patient_id,
            TaskInstance.scheduled_date == today,
            TaskInstance.status == TaskStatus.COMPLETED
        ).all()

        for record in completed_records:
            if record.value:
                # 检查血糖异常
                if record.value.get("type") == "blood_glucose":
                    value = record.value.get("value")
                    if value and value > 10:  # 餐后血糖>10为异常
                        has_abnormal_value = True
                        alerts.append(f"血糖异常 {value} mmol/L")
                # 可以添加其他监测项的异常判断

        # 检查超时任务
        if overdue_tasks > 0:
            alerts.append(f"{overdue_tasks}个任务未完成")

        # 获取最近活动时间（最近消息时间）
        last_session = db.query(SessionModel).filter(
            SessionModel.user_id == patient_id
        ).order_by(SessionModel.updated_at.desc()).first()

        last_seen = format_time_ago(last_session.updated_at) if last_session else "从未活跃"
        last_consultation = format_time_ago(last_session.created_at) if last_session else last_seen

        # 获取今日异常预警
        active_alerts = db.query(Alert).filter(
            Alert.patient_id == patient_id,
            Alert.is_acknowledged == False
        ).order_by(Alert.created_at.desc()).limit(3).all()

        for alert in active_alerts:
            alert_msg = alert.title
            if alert.value_data:
                # 简化异常值显示
                if alert.value_data.get("value"):
                    alert_msg += f": {alert.value_data['value']}"
            alerts.append(alert_msg)

        # 判断风险等级（可以根据医嘱类型、异常频率等）
        risk_level = "low"
        if completion_rate < 50 or has_abnormal_value:
            risk_level = "high"
        elif completion_rate < 80:
            risk_level = "medium"

        patients_data.append(PatientCardResponse(
            id=patient.id,
            name=patient.nickname or patient.username,
            nickname=patient.nickname,
            avatar=patient.avatar,
            last_seen=last_seen,
            last_consultation=last_consultation,
            completion_rate=completion_rate,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            status=get_patient_status(completion_rate, has_abnormal_value, overdue_tasks),
            alerts=alerts[:3],  # 最多显示3条预警
            risk_level=risk_level
        ))

    # 按状态排序：异常的排前面
    patients_data.sort(key=lambda p: {
        "danger": 0,
        "warning": 1,
        "success": 2
    }.get(p.status, 2))

    # 计算统计数据
    stats = {
        "total": len(patients_data),
        "abnormal": len([p for p in patients_data if p.status == "danger"]),
        "high_risk": len([p for p in patients_data if p.risk_level == "high"])
    }

    return PatientListResponse(
        patients=patients_data,
        stats=stats
    )


@router.get("/patients/{patient_id}", response_model=PatientDetailResponse)
def get_patient_detail(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取患者详情

    返回患者的完整信息，包括对话记录、医嘱任务、依从性数据
    """
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    today = date.today()

    # 获取今日任务
    today_tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == patient_id,
        TaskInstance.scheduled_date == today
    ).order_by(TaskInstance.scheduled_time).all()

    total_tasks = len(today_tasks)
    completed_tasks = len([t for t in today_tasks if t.status == TaskStatus.COMPLETED])
    completion_rate = calculate_completion_rate(total_tasks, completed_tasks)

    # 获取最近对话（最近5条）
    recent_session = db.query(SessionModel).filter(
        SessionModel.user_id == patient_id
    ).order_by(SessionModel.updated_at.desc()).first()

    recent_messages = []
    if recent_session:
        messages = db.query(Message).filter(
            Message.session_id == recent_session.id
        ).order_by(Message.created_at.desc()).limit(5).all()

        for msg in messages:
            time_str = msg.created_at.strftime("%H:%M") if msg.created_at else ""
            recent_messages.append(ChatMessageResponse(
                id=msg.id,
                content=msg.content,
                is_ai=msg.sender == SenderType.ai,
                time=time_str,
                created_at=msg.created_at
            ))

    # 构建任务响应
    task_responses = []
    for task in today_tasks:
        # 获取完成记录
        completion_record = db.query(CompletionRecord).filter(
            CompletionRecord.task_instance_id == task.id
        ).first()

        task_responses.append(RoundingTaskResponse(
            id=task.id,
            title=task.order.title if task.order else "未命名任务",
            order_type=task.order.order_type.value if task.order else "unknown",
            scheduled_time=task.scheduled_time.strftime("%H:%M") if task.scheduled_time else "",
            status=task.status.value,
            completed_at=task.completed_at.strftime("%H:%M") if task.completed_at else None,
            value=completion_record.value if completion_record else None,
            notes=completion_record.notes if completion_record else None
        ))

    # 获取预警信息
    alerts_data = []
    active_alerts = db.query(Alert).filter(
        Alert.patient_id == patient_id,
        Alert.is_acknowledged == False
    ).order_by(Alert.created_at.desc()).limit(5).all()

    for alert in active_alerts:
        alert_msg = {
            "type": alert.alert_type.value,
            "severity": alert.severity.value,
            "message": alert.message,
            "value": alert.value_data
        }
        alerts_data.append(alert_msg)

    # 获取最近7天的依从性数据
    daily_compliance = []
    for i in range(7):
        check_date = today - timedelta(days=i)
        day_tasks = db.query(TaskInstance).filter(
            TaskInstance.patient_id == patient_id,
            TaskInstance.scheduled_date == check_date
        ).all()

        day_total = len(day_tasks)
        day_completed = len([t for t in day_tasks if t.status == TaskStatus.COMPLETED])
        day_rate = calculate_completion_rate(day_total, day_completed)

        daily_compliance.append({
            "date": check_date.strftime("%m-%d"),
            "rate": day_rate
        })

    # 反转顺序，最近的在前
    daily_compliance.reverse()

    # 计算平均完成率
    avg_rate = int(sum(d["rate"] for d in daily_compliance) / len(daily_compliance)) if daily_compliance else 0

    return PatientDetailResponse(
        id=patient.id,
        name=patient.nickname or patient.username,
        nickname=patient.nickname,
        avatar=patient.avatar,
        condition=None,  # TODO: 可以从用户数据中获取患者类型标签
        last_seen=format_time_ago(recent_session.updated_at) if recent_session else "未知",
        last_consultation=format_time_ago(recent_session.created_at) if recent_session else "未知",
        alerts=alerts_data,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        completion_rate=completion_rate,
        recent_messages=recent_messages,
        today_tasks=task_responses,
        compliance_rate=avg_rate,
        daily_compliance=[{
            "date": d["date"],
            "rate": d["rate"]
        } for d in daily_compliance]
    )


# ============================================
# 筛选接口
# ============================================

@router.get("/patients/abnormal", response_model=List[PatientCardResponse])
def get_abnormal_patients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取异常患者列表

    返回今日有异常的患者（完成率低、有异常数值、有任务超时）
    """
    today = date.today()

    # 获取所有今日任务
    today_tasks = db.query(TaskInstance).filter(
        TaskInstance.scheduled_date == today
    ).all()

    patient_ids = set(t.patient_id for t in today_tasks)
    abnormal_patient_ids = set()

    # 检查每个患者是否有异常
    for patient_id in patient_ids:
        patient_tasks = [t for t in today_tasks if t.patient_id == patient_id]
        total = len(patient_tasks)
        completed = len([t for t in patient_tasks if t.status == TaskStatus.COMPLETED])
        overdue = len([t for t in patient_tasks if t.status == TaskStatus.OVERDUE])

        # 完成率低于50% 或 有超时任务
        if calculate_completion_rate(total, completed) < 50 or overdue > 0:
            abnormal_patient_ids.add(patient_id)
            continue

        # 检查异常数值
        completed_record_ids = [t.id for t in patient_tasks if t.status == TaskStatus.COMPLETED]
        if completed_record_ids:
            abnormal_records = db.query(CompletionRecord).filter(
                CompletionRecord.task_instance_id.in_(completed_record_ids)
            ).all()

            for record in abnormal_records:
                if record.value and record.value.get("type") == "blood_glucose":
                    value = record.value.get("value")
                    if value and value > 10:
                        abnormal_patient_ids.add(patient_id)
                        break

    # 构建响应
    patients_data = []
    for patient_id in abnormal_patient_ids:
        patient = db.query(User).filter(User.id == patient_id).first()
        if not patient:
            continue

        patient_tasks = [t for t in today_tasks if t.patient_id == patient_id]
        total_tasks = len(patient_tasks)
        completed_tasks = len([t for t in patient_tasks if t.status == TaskStatus.COMPLETED])
        completion_rate = calculate_completion_rate(total_tasks, completed_tasks)

        # 获取预警
        alerts = []
        active_alerts = db.query(Alert).filter(
            Alert.patient_id == patient_id,
            Alert.is_acknowledged == False
        ).limit(3).all()

        for alert in active_alerts:
            alerts.append(alert.title or alert.message)

        last_session = db.query(SessionModel).filter(
            SessionModel.user_id == patient_id
        ).order_by(SessionModel.updated_at.desc()).first()

        patients_data.append(PatientCardResponse(
            id=patient.id,
            name=patient.nickname or patient.username,
            avatar=patient.avatar,
            last_seen=format_time_ago(last_session.updated_at) if last_session else "未知",
            last_consultation=format_time_ago(last_session.created_at) if last_session else "未知",
            completion_rate=completion_rate,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            status="danger",
            alerts=alerts[:3],
            risk_level="high"
        ))

    return patients_data


# ============================================
# 统计接口
# ============================================

@router.get("/stats", response_model=Dict[str, Any])
def get_rounding_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取远程查房统计数据

    返回患者总数、异常患者数、高风险患者数等
    """
    today = date.today()

    # 有任务的患者
    patients_with_tasks = db.query(TaskInstance.patient_id).distinct().count()

    # 异常患者数
    abnormal_patients = 0

    # 高风险患者数
    high_risk_patients = 0

    # 这里可以计算更详细的统计
    # 简化起见，使用患者列表接口的统计

    return {
        "total_patients": patients_with_tasks,
        "abnormal_patients": abnormal_patients,
        "high_risk_patients": high_risk_patients,
        "date": today.isoformat()
    }
