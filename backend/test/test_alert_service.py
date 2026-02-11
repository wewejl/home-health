"""
AlertService 单元测试

测试预警服务的所有方法：
- check_completion_record() 检查打卡异常
- _check_glucose_value() 血糖预警
- _check_blood_pressure_value() 血压预警
- _check_temperature_value() 体温预警
- check_overdue_tasks() 超时任务预警
- check_low_compliance() 低依从性预警
- acknowledge_alert() 确认预警
- get_family_alerts() 家属预警
"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

# 导入服务和模型
try:
    from app.services.alert_service import AlertService
    from app.models.medical_order import (
        Alert, AlertType, AlertSeverity, FamilyBond, NotificationLevel,
        TaskInstance, TaskStatus, CompletionRecord, MedicalOrder
    )
    from app.models.user import User
except ImportError:
    from backend.app.services.alert_service import AlertService
    from backend.app.models.medical_order import (
        Alert, AlertType, AlertSeverity, FamilyBond, NotificationLevel,
        TaskInstance, TaskStatus, CompletionRecord, MedicalOrder
    )
    from backend.app.models.user import User


class TestCheckGlucoseValue:
    """测试血糖预警检查"""

    def test_glucose_low_critical(self, db_session: Session):
        """测试低血糖临界预警"""
        # 创建测试数据
        patient = User(id=2001, phone="13800001001", nickname="患者1")
        db_session.add(patient)

        task = TaskInstance(id=3001, patient_id=2001, scheduled_date=date.today())
        db_session.add(task)
        db_session.commit()

        record = CompletionRecord(
            id=4001,
            task_instance_id=3001,
            completion_type="value",
            value={"value": 3.5}  # 低于 3.9
        )
        # 设置关联
        record.task_instance = task

        service = AlertService(db_session)
        alert = service._check_glucose_value(record.value, record)

        assert alert is not None
        assert alert.alert_type == AlertType.GLUCOSE_LOW
        assert alert.severity == AlertSeverity.CRITICAL
        assert "低血糖" in alert.title

    def test_glucose_high_warning(self, db_session: Session):
        """测试高血糖警告"""
        patient = User(id=2002, phone="13800001002", nickname="患者2")
        db_session.add(patient)

        task = TaskInstance(id=3002, patient_id=2002, scheduled_date=date.today())
        db_session.add(task)
        db_session.commit()

        record = CompletionRecord(
            id=4002,
            task_instance_id=3002,
            completion_type="value",
            value={"value": 12.5}  # 高于 11.1
        )
        record.task_instance = task

        service = AlertService(db_session)
        alert = service._check_glucose_value(record.value, record)

        assert alert is not None
        assert alert.alert_type == AlertType.GLUCOSE_HIGH
        assert alert.severity == AlertSeverity.WARNING
        assert "高血糖" in alert.title

    def test_glucose_normal_no_alert(self, db_session: Session):
        """测试正常血糖不产生预警"""
        patient = User(id=2003, phone="13800001003", nickname="患者3")
        db_session.add(patient)

        task = TaskInstance(id=3003, patient_id=2003, scheduled_date=date.today())
        db_session.add(task)
        db_session.commit()

        record = CompletionRecord(
            id=4003,
            task_instance_id=3003,
            completion_type="value",
            value={"value": 6.5}  # 正常范围
        )
        record.task_instance = task

        service = AlertService(db_session)
        alert = service._check_glucose_value(record.value, record)

        assert alert is None

    def test_glucose_boundary_values(self, db_session: Session):
        """测试血糖边界值"""
        patient = User(id=2004, phone="13800001004", nickname="患者4")
        db_session.add(patient)

        task = TaskInstance(id=3004, patient_id=2004, scheduled_date=date.today())
        db_session.add(task)
        db_session.commit()

        service = AlertService(db_session)

        # 测试低边界 - 3.9 不应该触发低血糖
        record = CompletionRecord(
            id=4004,
            task_instance_id=3004,
            completion_type="value",
            value={"value": 3.9}
        )
        record.task_instance = task
        alert = service._check_glucose_value(record.value, record)
        assert alert is None

        # 测试高边界 - 11.1 不应该触发高血糖
        record.value = {"value": 11.1}
        alert = service._check_glucose_value(record.value, record)
        assert alert is None

        # 3.8 应该触发低血糖
        record.value = {"value": 3.8}
        alert = service._check_glucose_value(record.value, record)
        assert alert is not None
        assert alert.alert_type == AlertType.GLUCOSE_LOW

        # 11.2 应该触发高血糖
        record.value = {"value": 11.2}
        alert = service._check_glucose_value(record.value, record)
        assert alert is not None
        assert alert.alert_type == AlertType.GLUCOSE_HIGH


class TestCheckBloodPressureValue:
    """测试血压预警检查"""

    def test_bp_high_warning(self, db_session: Session):
        """测试血压偏高预警"""
        patient = User(id=2005, phone="13800001005", nickname="患者5")
        db_session.add(patient)

        task = TaskInstance(id=3005, patient_id=2005, scheduled_date=date.today())
        db_session.add(task)
        db_session.commit()

        record = CompletionRecord(
            id=4005,
            task_instance_id=3005,
            completion_type="value",
            value={"systolic": 145, "diastolic": 95}
        )
        record.task_instance = task

        service = AlertService(db_session)
        alert = service._check_blood_pressure_value(record.value, record)

        assert alert is not None
        assert alert.alert_type == AlertType.BLOOD_PRESSURE_HIGH
        assert alert.severity == AlertSeverity.WARNING

    def test_bp_critical_warning(self, db_session: Session):
        """测试血压危象预警"""
        patient = User(id=2006, phone="13800001006", nickname="患者6")
        db_session.add(patient)

        task = TaskInstance(id=3006, patient_id=2006, scheduled_date=date.today())
        db_session.add(task)
        db_session.commit()

        record = CompletionRecord(
            id=4006,
            task_instance_id=3006,
            completion_type="value",
            value={"systolic": 180, "diastolic": 120}
        )
        record.task_instance = task

        service = AlertService(db_session)
        alert = service._check_blood_pressure_value(record.value, record)

        assert alert is not None
        assert alert.alert_type == AlertType.BLOOD_PRESSURE_HIGH
        assert alert.severity == AlertSeverity.CRITICAL

    def test_bp_normal_no_alert(self, db_session: Session):
        """测试正常血压不产生预警"""
        patient = User(id=2007, phone="13800001007", nickname="患者7")
        db_session.add(patient)

        task = TaskInstance(id=3007, patient_id=2007, scheduled_date=date.today())
        db_session.add(task)
        db_session.commit()

        record = CompletionRecord(
            id=4007,
            task_instance_id=3007,
            completion_type="value",
            value={"systolic": 120, "diastolic": 80}
        )
        record.task_instance = task

        service = AlertService(db_session)
        alert = service._check_blood_pressure_value(record.value, record)

        assert alert is None


class TestCheckTemperatureValue:
    """测试体温预警检查"""

    def test_temperature_fever_warning(self, db_session: Session):
        """测试发烧预警"""
        patient = User(id=2008, phone="13800001008", nickname="患者8")
        db_session.add(patient)

        task = TaskInstance(id=3008, patient_id=2008, scheduled_date=date.today())
        db_session.add(task)
        db_session.commit()

        record = CompletionRecord(
            id=4008,
            task_instance_id=3008,
            completion_type="value",
            value={"value": 38.5}
        )
        record.task_instance = task

        service = AlertService(db_session)
        alert = service._check_temperature_value(record.value, record)

        assert alert is not None
        assert alert.alert_type == AlertType.TEMPERATURE_HIGH
        assert alert.severity == AlertSeverity.WARNING
        assert "发烧" not in alert.title  # 低于39度

    def test_temperature_critical_fever(self, db_session: Session):
        """测试高烧预警"""
        patient = User(id=2009, phone="13800001009", nickname="患者9")
        db_session.add(patient)

        task = TaskInstance(id=3009, patient_id=2009, scheduled_date=date.today())
        db_session.add(task)
        db_session.commit()

        record = CompletionRecord(
            id=4009,
            task_instance_id=3009,
            completion_type="value",
            value={"value": 39.5}
        )
        record.task_instance = task

        service = AlertService(db_session)
        alert = service._check_temperature_value(record.value, record)

        assert alert is not None
        assert alert.alert_type == AlertType.TEMPERATURE_HIGH
        assert alert.severity == AlertSeverity.CRITICAL
        assert "发烧" in alert.title

    def test_temperature_normal_no_alert(self, db_session: Session):
        """测试正常体温不产生预警"""
        patient = User(id=2010, phone="13800001010", nickname="患者10")
        db_session.add(patient)

        task = TaskInstance(id=3010, patient_id=2010, scheduled_date=date.today())
        db_session.add(task)
        db_session.commit()

        record = CompletionRecord(
            id=4010,
            task_instance_id=3010,
            completion_type="value",
            value={"value": 36.5}
        )
        record.task_instance = task

        service = AlertService(db_session)
        alert = service._check_temperature_value(record.value, record)

        assert alert is None


class TestCheckCompletionRecord:
    """测试打卡记录检查"""

    def test_check_completion_record_no_value(self, db_session: Session):
        """测试没有值的记录不产生预警"""
        service = AlertService(db_session)

        record = CompletionRecord(
            id=4011,
            completion_type="value",
            value=None
        )

        alerts = service.check_completion_record(record)
        assert alerts == []

    def test_check_completion_record_glucose_keyword(self, db_session: Session):
        """测试通过关键字识别血糖检查"""
        patient = User(id=2011, phone="13800001011", nickname="患者11")
        db_session.add(patient)

        task = TaskInstance(id=3011, patient_id=2011, scheduled_date=date.today())
        db_session.add(task)
        db_session.commit()

        service = AlertService(db_session)

        record = CompletionRecord(
            id=4011,
            task_instance_id=3011,
            completion_type="value",
            value={"glucose": 3.5}  # 使用 glucose 关键字
        )
        record.task_instance = task

        # 清除之前的预警
        db_session.query(Alert).delete()
        db_session.commit()

        alerts = service.check_completion_record(record)
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.GLUCOSE_LOW


class TestCheckOverdueTasks:
    """测试超时任务预警"""

    def test_check_overdue_tasks_no_existing_alert(self, db_session: Session):
        """测试为没有预警的超时任务创建预警"""
        patient = User(id=2012, phone="13800001012", nickname="患者12")
        db_session.add(patient)

        order = MedicalOrder(id=2012, patient_id=2012, title="测试医嘱12", start_date=date.today())
        db_session.add(order)
        db_session.commit()

        task = TaskInstance(
            id=3012,
            patient_id=2012,
            order_id=2012,
            scheduled_date=date.today() - timedelta(days=1),
            status=TaskStatus.OVERDUE
        )
        db_session.add(task)
        db_session.commit()

        service = AlertService(db_session)
        alerts = service.check_overdue_tasks(patient_id=2012)

        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.TASK_OVERDUE

    def test_check_overdue_tasks_existing_alert_skipped(self, db_session: Session):
        """测试已存在预警的任务不重复创建"""
        patient = User(id=2013, phone="13800001013", nickname="患者13")
        db_session.add(patient)

        order = MedicalOrder(id=2013, patient_id=2013, title="测试医嘱13", start_date=date.today())
        db_session.add(order)
        db_session.commit()

        task = TaskInstance(
            id=3013,
            patient_id=2013,
            order_id=2013,
            scheduled_date=date.today() - timedelta(days=1),
            status=TaskStatus.OVERDUE
        )
        db_session.add(task)
        db_session.commit()

        # 创建已存在的预警
        existing_alert = Alert(
            patient_id=2013,
            alert_type=AlertType.TASK_OVERDUE,
            task_instance_id=3013
        )
        db_session.add(existing_alert)
        db_session.commit()

        service = AlertService(db_session)
        alerts = service.check_overdue_tasks(patient_id=2013)

        # 不应该创建新预警
        assert len(alerts) == 0


class TestCheckLowCompliance:
    """测试低依从性预警"""

    def test_low_compliance_creates_alert(self, db_session: Session):
        """测试低依从性创建预警"""
        patient = User(id=2014, phone="13800001014", nickname="患者14")
        db_session.add(patient)
        db_session.commit()

        service = AlertService(db_session)

        # 模拟依从性低于60%
        with pytest.MonkeyPatch().context() as m:
            # Mock ComplianceService
            mock_compliance_service = MagicMock()
            mock_compliance_service.calculate_weekly_compliance.return_value = {
                "average_rate": 0.5  # 50% 低于60%
            }

            m.setattr("app.services.alert_service.ComplianceService", lambda db: mock_compliance_service)

            alert = service.check_low_compliance(patient_id=2014)

            assert alert is not None
            assert alert.alert_type == AlertType.COMPLIANCE_LOW

    def test_good_compliance_no_alert(self, db_session: Session):
        """测试良好依从性不创建预警"""
        patient = User(id=2015, phone="13800001015", nickname="患者15")
        db_session.add(patient)
        db_session.commit()

        service = AlertService(db_session)

        with pytest.MonkeyPatch().context() as m:
            mock_compliance_service = MagicMock()
            mock_compliance_service.calculate_weekly_compliance.return_value = {
                "average_rate": 0.8  # 80% 高于60%
            }

            m.setattr("app.services.alert_service.ComplianceService", lambda db: mock_compliance_service)

            alert = service.check_low_compliance(patient_id=2015)

            assert alert is None


class TestAcknowledgeAlert:
    """测试确认预警"""

    def test_acknowledge_alert_success(self, db_session: Session):
        """测试成功确认预警"""
        patient = User(id=2016, phone="13800001016", nickname="患者16")
        db_session.add(patient)
        db_session.commit()

        alert = Alert(
            patient_id=2016,
            alert_type=AlertType.GLUCOSE_LOW,
            severity=AlertSeverity.CRITICAL,
            title="测试预警",
            is_acknowledged=False
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        service = AlertService(db_session)
        result = service.acknowledge_alert(alert_id=alert.id, patient_id=2016)

        assert result is not None
        assert result.is_acknowledged is True
        assert result.acknowledged_at is not None

    def test_acknowledge_alert_not_found(self, db_session: Session):
        """测试确认不存在的预警"""
        service = AlertService(db_session)
        result = service.acknowledge_alert(alert_id=99999, patient_id=2016)

        assert result is None

    def test_acknowledge_alert_wrong_patient(self, db_session: Session):
        """测试确认其他患者的预警失败"""
        patient1 = User(id=2017, phone="13800001017", nickname="患者17")
        db_session.add(patient1)

        patient2 = User(id=2018, phone="13800001018", nickname="患者18")
        db_session.add(patient2)
        db_session.commit()

        alert = Alert(
            patient_id=2017,  # 属于患者17
            alert_type=AlertType.GLUCOSE_LOW,
            title="测试预警"
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        service = AlertService(db_session)
        # 患者18尝试确认患者17的预警
        result = service.acknowledge_alert(alert_id=alert.id, patient_id=2018)

        assert result is None


class TestGetActiveAlerts:
    """测试获取活跃预警"""

    def test_get_active_alerts_unacknowledged(self, db_session: Session):
        """测试获取未确认的预警"""
        patient = User(id=2019, phone="13800001019", nickname="患者19")
        db_session.add(patient)
        db_session.commit()

        # 创建未确认的预警
        alert1 = Alert(
            patient_id=2019,
            alert_type=AlertType.GLUCOSE_LOW,
            severity=AlertSeverity.CRITICAL,
            title="预警1",
            is_acknowledged=False
        )
        alert2 = Alert(
            patient_id=2019,
            alert_type=AlertType.TEMPERATURE_HIGH,
            severity=AlertSeverity.WARNING,
            title="预警2",
            is_acknowledged=False
        )
        db_session.add_all([alert1, alert2])
        db_session.commit()

        service = AlertService(db_session)
        alerts = service.get_active_alerts(patient_id=2019)

        assert len(alerts) == 2

    def test_get_active_alerts_excludes_acknowledged(self, db_session: Session):
        """测试已确认的预警不被返回"""
        patient = User(id=2020, phone="13800001020", nickname="患者20")
        db_session.add(patient)
        db_session.commit()

        # 创建已确认的预警
        alert = Alert(
            patient_id=2020,
            alert_type=AlertType.GLUCOSE_LOW,
            title="已确认预警",
            is_acknowledged=True
        )
        db_session.add(alert)
        db_session.commit()

        service = AlertService(db_session)
        alerts = service.get_active_alerts(patient_id=2020)

        assert len(alerts) == 0


class TestGetFamilyAlerts:
    """测试家属预警"""

    def test_get_family_alerts_no_bond(self, db_session: Session):
        """测试没有家属关系时返回空"""
        service = AlertService(db_session)
        alerts = service.get_family_alerts(patient_id=2021)

        assert alerts == []

    def test_get_family_alerts_notification_all(self, db_session: Session):
        """测试通知级别为ALL时返回所有预警"""
        patient = User(id=2021, phone="13800001021", nickname="患者21")
        db_session.add(patient)
        db_session.commit()

        # 创建家属关系
        bond = FamilyBond(
            patient_id=2021,
            family_phone="13800009999",
            notification_level=NotificationLevel.ALL
        )
        db_session.add(bond)
        db_session.commit()

        # 创建预警
        alert = Alert(
            patient_id=2021,
            alert_type=AlertType.GLUCOSE_LOW,
            severity=AlertSeverity.INFO,
            title="信息预警",
            is_acknowledged=False
        )
        db_session.add(alert)
        db_session.commit()

        service = AlertService(db_session)
        alerts = service.get_family_alerts(patient_id=2021)

        assert len(alerts) == 1

    def test_get_family_alerts_notification_abnormal_only(self, db_session: Session):
        """测试通知级别为ABNORMAL时只返回异常预警"""
        patient = User(id=2022, phone="13800001022", nickname="患者22")
        db_session.add(patient)
        db_session.commit()

        # 创建家属关系 - 仅异常通知
        bond = FamilyBond(
            patient_id=2022,
            family_phone="13800009998",
            notification_level=NotificationLevel.ABNORMAL
        )
        db_session.add(bond)
        db_session.commit()

        # 创建不同级别的预警
        info_alert = Alert(
            patient_id=2022,
            alert_type=AlertType.TASK_OVERDUE,
            severity=AlertSeverity.INFO,
            title="信息预警",
            is_acknowledged=False
        )
        warning_alert = Alert(
            patient_id=2022,
            alert_type=AlertType.GLUCOSE_LOW,
            severity=AlertSeverity.WARNING,
            title="警告预警",
            is_acknowledged=False
        )
        db_session.add_all([info_alert, warning_alert])
        db_session.commit()

        service = AlertService(db_session)
        alerts = service.get_family_alerts(patient_id=2022)

        # 只应该返回WARNING和CRITICAL级别的预警
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.WARNING


class TestMarkNotificationSent:
    """测试标记通知已发送"""

    def test_mark_notification_sent(self, db_session: Session):
        """测试标记通知已发送"""
        patient = User(id=2023, phone="13800001023", nickname="患者23")
        db_session.add(patient)
        db_session.commit()

        # 创建预警
        alert1 = Alert(id=5001, patient_id=2023, alert_type=AlertType.GLUCOSE_LOW, notification_sent=False)
        alert2 = Alert(id=5002, patient_id=2023, alert_type=AlertType.TEMPERATURE_HIGH, notification_sent=False)
        db_session.add_all([alert1, alert2])
        db_session.commit()

        service = AlertService(db_session)
        count = service.mark_notification_sent([5001, 5002])

        assert count == 2

        # 验证标记已更新
        db_session.refresh(alert1)
        db_session.refresh(alert2)
        assert alert1.notification_sent is True
        assert alert2.notification_sent is True
