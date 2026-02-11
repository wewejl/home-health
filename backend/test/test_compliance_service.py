"""
ComplianceService 单元测试

测试依从性计算服务的所有方法：
- calculate_daily_compliance() 日依从性
- calculate_weekly_compliance() 周依从性趋势
- calculate_order_compliance() 医嘱周期依从性
- get_abnormal_records() 异常记录获取
"""
import pytest
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

# 导入服务
try:
    from app.services.compliance_service import ComplianceService
    from app.models.medical_order import TaskInstance, TaskStatus, MedicalOrder
    from app.models.user import User
except ImportError:
    from backend.app.services.compliance_service import ComplianceService
    from backend.app.models.medical_order import TaskInstance, TaskStatus, MedicalOrder
    from backend.app.models.user import User


class TestCalculateDailyCompliance:
    """测试日依从性计算"""

    def test_calculate_daily_compliance_no_tasks(self, db_session: Session):
        """测试没有任务时的日依从性"""
        service = ComplianceService(db_session)
        result = service.calculate_daily_compliance(patient_id=999, target_date=date.today())

        assert result["total"] == 0
        assert result["completed"] == 0
        assert result["overdue"] == 0
        assert result["pending"] == 0
        assert result["rate"] == 0

    def test_calculate_daily_compliance_all_completed(self, db_session: Session):
        """测试所有任务都完成的情况"""
        # 创建测试患者和医嘱
        patient = User(id=1001, phone="13800000001", nickname="测试患者1")
        db_session.add(patient)

        order = MedicalOrder(id=1001, patient_id=1001, title="测试医嘱", start_date=date.today())
        db_session.add(order)
        db_session.commit()

        # 创建任务
        for i in range(5):
            task = TaskInstance(
                id=2000 + i,
                patient_id=1001,
                order_id=1001,
                scheduled_date=date.today(),
                status=TaskStatus.COMPLETED
            )
            db_session.add(task)
        db_session.commit()

        service = ComplianceService(db_session)
        result = service.calculate_daily_compliance(patient_id=1001, target_date=date.today())

        assert result["total"] == 5
        assert result["completed"] == 5
        assert result["overdue"] == 0
        assert result["pending"] == 0
        assert result["rate"] == 1.0

    def test_calculate_daily_compliance_mixed_status(self, db_session: Session):
        """测试混合状态的日依从性"""
        # 创建测试患者和医嘱
        patient = User(id=1002, phone="13800000002", nickname="测试患者2")
        db_session.add(patient)

        order = MedicalOrder(id=1002, patient_id=1002, title="测试医嘱2", start_date=date.today())
        db_session.add(order)
        db_session.commit()

        # 创建混合状态的任务
        tasks_data = [
            (TaskStatus.COMPLETED, 2),  # 2个完成
            (TaskStatus.OVERDUE, 1),     # 1个超时
            (TaskStatus.PENDING, 2),     # 2个待完成
        ]

        task_id = 2100
        for status, count in tasks_data:
            for _ in range(count):
                task = TaskInstance(
                    id=task_id,
                    patient_id=1002,
                    order_id=1002,
                    scheduled_date=date.today(),
                    status=status
                )
                db_session.add(task)
                task_id += 1
        db_session.commit()

        service = ComplianceService(db_session)
        result = service.calculate_daily_compliance(patient_id=1002, target_date=date.today())

        assert result["total"] == 5
        assert result["completed"] == 2
        assert result["overdue"] == 1
        assert result["pending"] == 2
        assert result["rate"] == 0.4  # 2/5 = 0.4

    def test_calculate_daily_compliance_rate_rounding(self, db_session: Session):
        """测试依从率四舍五入"""
        # 创建测试患者和医嘱
        patient = User(id=1003, phone="13800000003", nickname="测试患者3")
        db_session.add(patient)

        order = MedicalOrder(id=1003, patient_id=1003, title="测试医嘱3", start_date=date.today())
        db_session.add(order)
        db_session.commit()

        # 创建3个任务，完成2个 - 依从率应该是 0.67
        for i in range(2):
            task = TaskInstance(
                id=2200 + i,
                patient_id=1003,
                order_id=1003,
                scheduled_date=date.today(),
                status=TaskStatus.COMPLETED
            )
            db_session.add(task)

        task = TaskInstance(
            id=2202,
            patient_id=1003,
            order_id=1003,
            scheduled_date=date.today(),
            status=TaskStatus.PENDING
        )
        db_session.add(task)
        db_session.commit()

        service = ComplianceService(db_session)
        result = service.calculate_daily_compliance(patient_id=1003, target_date=date.today())

        assert result["rate"] == 0.67  # 2/3 ≈ 0.666... 四舍五入到0.67


class TestCalculateWeeklyCompliance:
    """测试周依从性趋势"""

    def test_calculate_weekly_compliance_no_tasks(self, db_session: Session):
        """测试没有任务时的周依从性"""
        service = ComplianceService(db_session)
        result = service.calculate_weekly_compliance(patient_id=999)

        assert len(result["daily_rates"]) == 7
        assert result["average_rate"] == 0
        assert len(result["dates"]) == 7
        # 所有日期应该都是0
        assert all(rate == 0 for rate in result["daily_rates"])

    def test_calculate_weekly_compliance_with_data(self, db_session: Session):
        """测试有数据的周依从性"""
        # 创建测试患者
        patient = User(id=1004, phone="13800000004", nickname="测试患者4")
        db_session.add(patient)

        order = MedicalOrder(id=1004, patient_id=1004, title="测试医嘱4", start_date=date.today() - timedelta(days=6))
        db_session.add(order)
        db_session.commit()

        # 为今天创建5个完成的任务
        for i in range(5):
            task = TaskInstance(
                id=2300 + i,
                patient_id=1004,
                order_id=1004,
                scheduled_date=date.today(),
                status=TaskStatus.COMPLETED
            )
            db_session.add(task)
        db_session.commit()

        service = ComplianceService(db_session)
        result = service.calculate_weekly_compliance(patient_id=1004)

        assert len(result["daily_rates"]) == 7
        assert len(result["dates"]) == 7
        # 今天的依从率应该是1.0
        assert result["daily_rates"][-1] == 1.0
        # 平均依从率应该大于0
        assert result["average_rate"] > 0

    def test_calculate_weekly_compliance_date_order(self, db_session: Session):
        """测试日期顺序正确（从6天前到今天）"""
        service = ComplianceService(db_session)
        result = service.calculate_weekly_compliance(patient_id=999)

        today = date.today()
        expected_dates = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]

        assert result["dates"] == expected_dates


class TestCalculateOrderCompliance:
    """测试医嘱周期依从性"""

    def test_calculate_order_compliance_no_tasks(self, db_session: Session):
        """测试没有任务的医嘱"""
        service = ComplianceService(db_session)
        result = service.calculate_order_compliance(order_id=999)

        assert result["order_id"] == 999
        assert result["total"] == 0
        assert result["completed"] == 0
        assert result["rate"] == 0
        assert result["start_date"] is None
        assert result["end_date"] is None

    def test_calculate_order_compliance_with_tasks(self, db_session: Session):
        """测试有任务的医嘱"""
        # 创建测试患者和医嘱
        patient = User(id=1005, phone="13800000005", nickname="测试患者5")
        db_session.add(patient)

        start = date.today() - timedelta(days=5)
        order = MedicalOrder(id=1005, patient_id=1005, title="测试医嘱5", start_date=start)
        db_session.add(order)
        db_session.commit()

        # 创建不同日期的任务
        dates = [start, start + timedelta(days=2), start + timedelta(days=5)]
        for i, task_date in enumerate(dates):
            task = TaskInstance(
                id=2400 + i,
                patient_id=1005,
                order_id=1005,
                scheduled_date=task_date,
                status=TaskStatus.COMPLETED if i < 2 else TaskStatus.PENDING
            )
            db_session.add(task)
        db_session.commit()

        service = ComplianceService(db_session)
        result = service.calculate_order_compliance(order_id=1005)

        assert result["order_id"] == 1005
        assert result["total"] == 3
        assert result["completed"] == 2
        assert result["rate"] == 0.67  # 2/3 ≈ 0.67
        assert result["start_date"] == start.isoformat()
        assert result["end_date"] == (start + timedelta(days=5)).isoformat()


class TestGetAbnormalRecords:
    """测试异常记录获取"""

    def test_get_abnormal_records_no_records(self, db_session: Session):
        """测试没有异常记录"""
        service = ComplianceService(db_session)
        result = service.get_abnormal_records(patient_id=999, days=30)

        assert result == []

    def test_get_abnormal_records_with_overdue_tasks(self, db_session: Session):
        """测试有超时任务"""
        # 创建测试患者
        patient = User(id=1006, phone="13800000006", nickname="测试患者6")
        db_session.add(patient)

        order = MedicalOrder(id=1006, patient_id=1006, title="测试医嘱6", start_date=date.today() - timedelta(days=5))
        db_session.add(order)
        db_session.commit()

        # 创建超时任务
        task = TaskInstance(
            id=2500,
            patient_id=1006,
            order_id=1006,
            scheduled_date=date.today() - timedelta(days=1),
            scheduled_time=datetime.now().time(),
            status=TaskStatus.OVERDUE
        )
        db_session.add(task)
        db_session.commit()

        service = ComplianceService(db_session)
        result = service.get_abnormal_records(patient_id=1006, days=30)

        assert len(result) == 1
        assert result[0]["task_id"] == 2500
        assert result[0]["order_title"] == "测试医嘱6"

    def test_get_abnormal_records_date_filter(self, db_session: Session):
        """测试日期范围过滤"""
        # 创建测试患者
        patient = User(id=1007, phone="13800000007", nickname="测试患者7")
        db_session.add(patient)

        order = MedicalOrder(id=1007, patient_id=1007, title="测试医嘱7", start_date=date.today() - timedelta(days=50))
        db_session.add(order)
        db_session.commit()

        # 创建超出范围的超时任务（40天前）
        old_task = TaskInstance(
            id=2600,
            patient_id=1007,
            order_id=1007,
            scheduled_date=date.today() - timedelta(days=40),
            scheduled_time=datetime.now().time(),
            status=TaskStatus.OVERDUE
        )
        db_session.add(old_task)

        # 创建范围内的超时任务（5天前）
        recent_task = TaskInstance(
            id=2601,
            patient_id=1007,
            order_id=1007,
            scheduled_date=date.today() - timedelta(days=5),
            scheduled_time=datetime.now().time(),
            status=TaskStatus.OVERDUE
        )
        db_session.add(recent_task)
        db_session.commit()

        service = ComplianceService(db_session)
        result = service.get_abnormal_records(patient_id=1007, days=30)

        # 只应该返回范围内的任务
        assert len(result) == 1
        assert result[0]["task_id"] == 2601

    def test_get_abnormal_records_sorting(self, db_session: Session):
        """测试记录按日期降序排序"""
        # 创建测试患者
        patient = User(id=1008, phone="13800000008", nickname="测试患者8")
        db_session.add(patient)

        order = MedicalOrder(id=1008, patient_id=1008, title="测试医嘱8", start_date=date.today() - timedelta(days=10))
        db_session.add(order)
        db_session.commit()

        # 创建多个不同日期的超时任务
        dates = [
            date.today() - timedelta(days=5),
            date.today() - timedelta(days=1),
            date.today() - timedelta(days=3),
        ]
        for i, task_date in enumerate(dates):
            task = TaskInstance(
                id=2700 + i,
                patient_id=1008,
                order_id=1008,
                scheduled_date=task_date,
                scheduled_time=datetime.now().time(),
                status=TaskStatus.OVERDUE
            )
            db_session.add(task)
        db_session.commit()

        service = ComplianceService(db_session)
        result = service.get_abnormal_records(patient_id=1008, days=30)

        # 应该按日期降序排序
        assert len(result) == 3
        assert result[0]["date"] >= result[1]["date"]
        assert result[1]["date"] >= result[2]["date"]


class TestEdgeCases:
    """测试边界情况"""

    def test_zero_division_protection_daily(self, db_session: Session):
        """测试日依从性的零除保护"""
        service = ComplianceService(db_session)
        result = service.calculate_daily_compliance(patient_id=999, target_date=date.today())

        # 没有任务时，依从率应该是0而不是除零错误
        assert result["rate"] == 0

    def test_zero_division_protection_weekly(self, db_session: Session):
        """测试周依从性的零除保护"""
        service = ComplianceService(db_session)
        result = service.calculate_weekly_compliance(patient_id=999)

        # 没有任务时，平均依从率应该是0
        assert result["average_rate"] == 0

    def test_zero_division_protection_order(self, db_session: Session):
        """测试医嘱依从性的零除保护"""
        service = ComplianceService(db_session)
        result = service.calculate_order_compliance(order_id=999)

        # 没有任务时，依从率应该是0
        assert result["rate"] == 0
