"""
异常预警服务

负责：
- 监测打卡数据中的异常值
- 创建预警记录
- 发送通知给患者和家属
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models.medical_order import (
    Alert, AlertType, AlertSeverity, FamilyBond, NotificationLevel,
    TaskInstance, TaskStatus, CompletionRecord
)

logger = logging.getLogger(__name__)


class AlertService:
    """预警服务"""

    # 预警阈值配置（类属性）
    GLUCOSE_LOW_THRESHOLD = 3.9  # mmol/L
    GLUCOSE_HIGH_THRESHOLD = 11.1  # mmol/L
    BP_HIGH_THRESHOLD_SYSTOLIC = 140  # mmHg
    BP_HIGH_THRESHOLD_DIASTOLIC = 90  # mmHg
    TEMP_FEVER_THRESHOLD = 37.3  # °C

    def __init__(self, db: Session):
        self.db = db

    def check_completion_record(self, record: CompletionRecord) -> List[Alert]:
        """
        检查打卡记录是否触发预警

        返回触发的预警列表
        """
        alerts = []

        if not record.value:
            return alerts

        value = record.value
        completion_type = record.completion_type

        # 根据打卡类型检查不同的阈值
        if completion_type == "value":
            # 通用数值录入，根据数据判断类型
            if "glucose" in str(value).lower() or "血糖" in str(value).lower():
                alert = self._check_glucose_value(value, record)
                if alert:
                    alerts.append(alert)
            elif "pressure" in str(value).lower() or "血压" in str(value).lower():
                alert = self._check_blood_pressure_value(value, record)
                if alert:
                    alerts.append(alert)
            elif "temp" in str(value).lower() or "体温" in str(value).lower() or "temperature" in str(value).lower():
                alert = self._check_temperature_value(value, record)
                if alert:
                    alerts.append(alert)

        # 保存预警到数据库
        for alert in alerts:
            self.db.add(alert)
        self.db.commit()

        return alerts

    def _check_glucose_value(self, value: Dict, record: CompletionRecord) -> Optional[Alert]:
        """检查血糖值"""
        glucose_value = value.get("value")

        if glucose_value is None:
            return None

        try:
            glucose_value = float(glucose_value)
        except (ValueError, TypeError):
            return None

        # 低血糖预警（紧急）
        if glucose_value < AlertService.GLUCOSE_LOW_THRESHOLD:
            return Alert(
                patient_id=record.task_instance.patient_id,
                alert_type=AlertType.GLUCOSE_LOW,
                severity=AlertSeverity.CRITICAL,
                title="低血糖预警",
                message=f"检测到低血糖：{glucose_value} mmol/L，低于正常值 {AlertService.GLUCOSE_LOW_THRESHOLD} mmol/L",
                task_instance_id=record.task_instance_id,
                completion_record_id=record.id,
                value_data=value,
                notification_sent=False
            )

        # 高血糖预警（警告）
        if glucose_value > AlertService.GLUCOSE_HIGH_THRESHOLD:
            return Alert(
                patient_id=record.task_instance.patient_id,
                alert_type=AlertType.GLUCOSE_HIGH,
                severity=AlertSeverity.WARNING,
                title="高血糖预警",
                message=f"检测到高血糖：{glucose_value} mmol/L，高于正常值 {AlertService.GLUCOSE_HIGH_THRESHOLD} mmol/L",
                task_instance_id=record.task_instance_id,
                completion_record_id=record.id,
                value_data=value,
                notification_sent=False
            )

        return None

    def _check_blood_pressure_value(self, value: Dict, record: CompletionRecord) -> Optional[Alert]:
        """检查血压值"""
        systolic = value.get("systolic")  # 收缩压
        diastolic = value.get("diastolic")  # 舒张压

        if systolic is None or diastolic is None:
            return None

        try:
            systolic = int(systolic)
            diastolic = int(diastolic)
        except (ValueError, TypeError):
            return None

        # 高血压预警
        if systolic >= AlertService.BP_HIGH_THRESHOLD_SYSTOLIC or diastolic >= AlertService.BP_HIGH_THRESHOLD_DIASTOLIC:
            severity = AlertSeverity.CRITICAL if systolic >= 180 or diastolic >= 120 else AlertSeverity.WARNING
            return Alert(
                patient_id=record.task_instance.patient_id,
                alert_type=AlertType.BLOOD_PRESSURE_HIGH,
                severity=severity,
                title="血压偏高预警",
                message=f"检测到血压偏高：{systolic}/{diastolic} mmHg",
                task_instance_id=record.task_instance_id,
                completion_record_id=record.id,
                value_data=value,
                notification_sent=False
            )

        return None

    def _check_temperature_value(self, value: Dict, record: CompletionRecord) -> Optional[Alert]:
        """检查体温"""
        temp_value = value.get("value")

        if temp_value is None:
            return None

        try:
            temp_value = float(temp_value)
        except (ValueError, TypeError):
            return None

        # 发烧预警
        if temp_value > AlertService.TEMP_FEVER_THRESHOLD:
            severity = AlertSeverity.CRITICAL if temp_value >= 39 else AlertSeverity.WARNING
            return Alert(
                patient_id=record.task_instance.patient_id,
                alert_type=AlertType.TEMPERATURE_HIGH,
                severity=severity,
                title="发烧预警" if temp_value >= 39 else "体温偏高",
                message=f"检测到体温异常：{temp_value} °C",
                task_instance_id=record.task_instance_id,
                completion_record_id=record.id,
                value_data=value,
                notification_sent=False
            )

        return None

    def check_overdue_tasks(self, patient_id: int) -> List[Alert]:
        """
        检查超时任务并生成预警

        返回新生成的预警列表
        """
        # 查找超时任务
        overdue_tasks = self.db.query(TaskInstance).filter(
            TaskInstance.patient_id == patient_id,
            TaskInstance.status == TaskStatus.OVERDUE,
            TaskInstance.scheduled_date >= datetime.now().date() - timedelta(days=7)  # 只检查最近7天
        ).all()

        alerts = []

        for task in overdue_tasks:
            # 检查是否已经为这个任务创建过预警
            existing_alert = self.db.query(Alert).filter(
                Alert.task_instance_id == task.id,
                Alert.alert_type == AlertType.TASK_OVERDUE
            ).first()

            if existing_alert:
                continue

            alert = Alert(
                patient_id=patient_id,
                alert_type=AlertType.TASK_OVERDUE,
                severity=AlertSeverity.WARNING,
                title="任务超时提醒",
                message=f"任务「{task.order.title if task.order else '未命名'}」未按时完成",
                task_instance_id=task.id,
                value_data={
                    "scheduled_date": task.scheduled_date.isoformat(),
                    "scheduled_time": task.scheduled_time.strftime("%H:%M")
                },
                notification_sent=False
            )
            alerts.append(alert)
            self.db.add(alert)

        self.db.commit()
        return alerts

    def check_low_compliance(self, patient_id: int, days: int = 7) -> Optional[Alert]:
        """
        检查依从性是否过低

        如果7天内依从率低于60%，生成预警
        """
        from ..services.compliance_service import ComplianceService

        service = ComplianceService(self.db)
        weekly = service.calculate_weekly_compliance(patient_id)

        if weekly["average_rate"] < 0.6:  # 60% 阈值
            # 检查最近是否已创建过类似预警
            recent_alert = self.db.query(Alert).filter(
                Alert.patient_id == patient_id,
                Alert.alert_type == AlertType.COMPLIANCE_LOW,
                Alert.created_at >= datetime.now() - timedelta(days=1)
            ).first()

            if recent_alert:
                return None

            return Alert(
                patient_id=patient_id,
                alert_type=AlertType.COMPLIANCE_LOW,
                severity=AlertSeverity.WARNING,
                title="医嘱执行率偏低",
                message=f"近7天医嘱执行率为 {weekly['average_rate']:.0%}，建议按时完成医嘱任务",
                value_data={
                    "average_rate": weekly["average_rate"],
                    "days": days
                },
                notification_sent=False
            )

        return None

    def get_active_alerts(self, patient_id: int, limit: int = 50) -> List[Alert]:
        """
        获取患者的活跃预警（未确认的预警）
        """
        alerts = self.db.query(Alert).filter(
            Alert.patient_id == patient_id,
            Alert.is_acknowledged == False
        ).order_by(
            Alert.severity.desc(),
            Alert.created_at.desc()
        ).limit(limit).all()

        return alerts

    def acknowledge_alert(self, alert_id: int, patient_id: int) -> Optional[Alert]:
        """
        确认预警
        """
        alert = self.db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.patient_id == patient_id
        ).first()

        if not alert:
            return None

        alert.is_acknowledged = True
        alert.acknowledged_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(alert)

        return alert

    def get_family_alerts(self, patient_id: int) -> List[Alert]:
        """
        获取需要通知家属的预警

        根据家属关系配置的通知级别过滤
        """
        # 查找该患者的家属关系
        family_bonds = self.db.query(FamilyBond).filter(
            FamilyBond.patient_id == patient_id
        ).all()

        if not family_bonds:
            return []

        # 获取患者未确认的预警
        alerts = self.db.query(Alert).filter(
            Alert.patient_id == patient_id,
            Alert.is_acknowledged == False
        ).order_by(
            Alert.severity.desc(),
            Alert.created_at.desc()
        ).all()

        # 根据通知级别过滤
        filtered_alerts = []
        for alert in alerts:
            for bond in family_bonds:
                if bond.notification_level == NotificationLevel.ALL:
                    filtered_alerts.append(alert)
                    break
                elif bond.notification_level == NotificationLevel.ABNORMAL:
                    if alert.severity in [AlertSeverity.WARNING, AlertSeverity.CRITICAL]:
                        filtered_alerts.append(alert)
                        break

        return filtered_alerts

    def mark_notification_sent(self, alert_ids: List[int]) -> int:
        """
        标记预警已发送通知
        """
        count = self.db.query(Alert).filter(
            Alert.id.in_(alert_ids)
        ).update({
            "notification_sent": True,
            "notification_sent_at": datetime.utcnow()
        })

        self.db.commit()
        return count
