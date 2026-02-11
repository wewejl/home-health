"""
Rounding API 单元测试

测试远程查房接口：
- GET /rounding/patients 获取患者列表
- GET /rounding/patients/{patient_id} 获取患者详情
- GET /rounding/patients/abnormal 获取异常患者
- GET /rounding/stats 获取统计数据
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, datetime, time

# 导入必要的模块
try:
    from app.main import app
    from app.models.user import User
    from app.models.session import Session as SessionModel
    from app.models.message import Message, SenderType
    from app.models.medical_order import (
        MedicalOrder, TaskInstance, TaskStatus, OrderType,
        CompletionRecord, Alert
    )
except ImportError:
    from backend.app.main import app
    from backend.app.models.user import User
    from backend.app.models.session import Session as SessionModel
    from backend.app.models.message import Message, SenderType
    from backend.app.models.medical_order import (
        MedicalOrder, TaskInstance, TaskStatus, OrderType,
        CompletionRecord, Alert
    )


class TestCalculateCompletionRate:
    """测试完成率计算"""

    def test_completion_rate_all_completed(self):
        """测试全部完成的完成率"""
        from app.routes.rounding import calculate_completion_rate

        result = calculate_completion_rate(5, 5)
        assert result == 100

    def test_completion_rate_partial(self):
        """测试部分完成的完成率"""
        from app.routes.rounding import calculate_completion_rate

        result = calculate_completion_rate(10, 7)
        assert result == 70

    def test_completion_rate_none_completed(self):
        """测试全部未完成的完成率"""
        from app.routes.rounding import calculate_completion_rate

        result = calculate_completion_rate(5, 0)
        assert result == 0

    def test_completion_rate_no_tasks(self):
        """测试没有任务时的完成率"""
        from app.routes.rounding import calculate_completion_rate

        result = calculate_completion_rate(0, 0)
        assert result == 0

    def test_completion_rate_rounding(self):
        """测试四舍五入"""
        from app.routes.rounding import calculate_completion_rate

        result = calculate_completion_rate(3, 2)
        assert result == 67  # 2/3 ≈ 66.67% 四舍五入到67%


class TestGetPatientStatus:
    """测试患者状态判断"""

    def test_status_danger_low_completion(self):
        """测试完成率低返回danger"""
        from app.routes.rounding import get_patient_status

        result = get_patient_status(completion_rate=40, has_abnormal_value=False, overdue_count=0)
        assert result == "danger"

    def test_status_danger_abnormal_value(self):
        """测试有异常值返回danger"""
        from app.routes.rounding import get_patient_status

        result = get_patient_status(completion_rate=60, has_abnormal_value=True, overdue_count=0)
        assert result == "danger"

    def test_status_danger_overdue(self):
        """测试有超时任务返回danger"""
        from app.routes.rounding import get_patient_status

        result = get_patient_status(completion_rate=70, has_abnormal_value=False, overdue_count=2)
        assert result == "danger"

    def test_status_warning(self):
        """测试警告状态"""
        from app.routes.rounding import get_patient_status

        result = get_patient_status(completion_rate=75, has_abnormal_value=False, overdue_count=0)
        assert result == "warning"

    def test_status_success(self):
        """测试成功状态"""
        from app.routes.rounding import get_patient_status

        result = get_patient_status(completion_rate=90, has_abnormal_value=False, overdue_count=0)
        assert result == "success"


class TestFormatTimeAgo:
    """测试时间格式化"""

    def test_format_minutes_ago(self):
        """测试分钟前格式"""
        from app.routes.rounding import format_time_ago

        dt = datetime.now() - timedelta(minutes=5)
        result = format_time_ago(dt)
        assert "分钟前" in result

    def test_format_hours_ago(self):
        """测试小时前格式"""
        from app.routes.rounding import format_time_ago
        from datetime import timedelta

        dt = datetime.now() - timedelta(hours=3)
        result = format_time_ago(dt)
        assert "小时前" in result

    def test_format_days_ago(self):
        """测试天前格式"""
        from app.routes.rounding import format_time_ago
        from datetime import timedelta

        dt = datetime.now() - timedelta(days=2)
        result = format_time_ago(dt)
        assert "天前" in result

    def test_format_none_time(self):
        """测试None时间"""
        from app.routes.rounding import format_time_ago

        result = format_time_ago(None)
        assert result == "未知"


class TestGetRoundingPatients:
    """测试获取患者列表"""

    def test_get_empty_patient_list(self, test_client: TestClient, db_session: Session):
        """测试空患者列表"""
        user = User(id=6001, phone="13800003001", nickname="医生1")
        db_session.add(user)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.get("/rounding/patients")

            assert response.status_code == 200
            data = response.json()
            assert "patients" in data
            assert "stats" in data

        finally:
            app.dependencies.TEST_MODE = original_test_mode

    def test_get_patients_with_tasks(self, test_client: TestClient, db_session: Session):
        """测试有任务的患者列表"""
        # 创建医生和患者
        doctor = User(id=6002, phone="13800003002", nickname="医生2")
        patient = User(id=6003, phone="13800003003", nickname="患者1")
        db_session.add_all([doctor, patient])

        # 创建医嘱和任务
        order = MedicalOrder(
            id=7001,
            patient_id=6003,
            title="测血糖",
            order_type=OrderType.blood_glucose,
            start_date=date.today()
        )
        db_session.add(order)
        db_session.commit()

        task = TaskInstance(
            id=8001,
            patient_id=6003,
            order_id=7001,
            scheduled_date=date.today(),
            scheduled_time=time(9, 0),
            status=TaskStatus.COMPLETED
        )
        db_session.add(task)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.get("/rounding/patients")

            assert response.status_code == 200
            data = response.json()
            assert len(data["patients"]) >= 1
            assert data["stats"]["total"] >= 1

        finally:
            app.dependencies.TEST_MODE = original_test_mode

    def test_patients_sorted_by_status(self, test_client: TestClient, db_session: Session):
        """测试患者按状态排序"""
        # 创建多个患者
        patient1 = User(id=6004, phone="13800003004", nickname="患者A")
        patient2 = User(id=6005, phone="13800003005", nickname="患者B")
        db_session.add_all([patient1, patient2])

        # 为患者1创建已完成任务（success状态）
        order1 = MedicalOrder(
            id=7002,
            patient_id=6004,
            title="测血压",
            start_date=date.today()
        )
        db_session.add(order1)
        db_session.commit()

        task1 = TaskInstance(
            id=8002,
            patient_id=6004,
            order_id=7002,
            scheduled_date=date.today(),
            status=TaskStatus.COMPLETED
        )
        db_session.add(task1)

        # 为患者2创建超时任务（danger状态）
        order2 = MedicalOrder(
            id=7003,
            patient_id=6005,
            title="测体温",
            start_date=date.today()
        )
        db_session.add(order2)
        db_session.commit()

        task2 = TaskInstance(
            id=8003,
            patient_id=6005,
            order_id=7003,
            scheduled_date=date.today(),
            status=TaskStatus.OVERDUE
        )
        db_session.add(task2)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.get("/rounding/patients")

            assert response.status_code == 200
            data = response.json()
            # danger状态的患者应该排在前面
            if len(data["patients"]) >= 2:
                statuses = [p["status"] for p in data["patients"]]
                # danger应该排在success之前
                if "danger" in statuses and "success" in statuses:
                    danger_idx = statuses.index("danger")
                    success_idx = statuses.index("success")
                    assert danger_idx < success_idx

        finally:
            app.dependencies.TEST_MODE = original_test_mode


class TestGetPatientDetail:
    """测试获取患者详情"""

    def test_get_patient_detail_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取患者详情"""
        # 创建测试数据
        patient = User(id=6006, phone="13800003006", nickname="详情患者")
        db_session.add(patient)
        db_session.commit()

        # 创建会话
        session = SessionModel(id="sess_rounding_001", user_id=6006, department="皮肤科")
        db_session.add(session)
        db_session.commit()

        # 创建任务
        order = MedicalOrder(
            id=7004,
            patient_id=6006,
            title="血糖监测",
            start_date=date.today()
        )
        db_session.add(order)
        db_session.commit()

        task = TaskInstance(
            id=8004,
            patient_id=6006,
            order_id=7004,
            scheduled_date=date.today(),
            scheduled_time=time(8, 0),
            status=TaskStatus.PENDING
        )
        db_session.add(task)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.get(f"/rounding/patients/{6006}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 6006
            assert "total_tasks" in data
            assert "completion_rate" in data
            assert "today_tasks" in data
            assert "daily_compliance" in data

        finally:
            app.dependencies.TEST_MODE = original_test_mode

    def test_get_patient_detail_not_found(self, test_client: TestClient, db_session: Session):
        """测试患者不存在"""
        user = User(id=6007, phone="13800003007", nickname="医生3")
        db_session.add(user)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.get("/rounding/patients/99999")

            assert response.status_code == 404

        finally:
            app.dependencies.TEST_MODE = original_test_mode

    def test_patient_detail_compliance_data(self, test_client: TestClient, db_session: Session):
        """测试患者详情中的依从性数据"""
        patient = User(id=6008, phone="13800003008", nickname="依从性患者")
        db_session.add(patient)
        db_session.commit()

        # 创建过去7天的任务
        order = MedicalOrder(
            id=7005,
            patient_id=6008,
            title="每日任务",
            start_date=date.today() - timedelta(days=7)
        )
        db_session.add(order)
        db_session.commit()

        for i in range(7):
            task_date = date.today() - timedelta(days=i)
            task = TaskInstance(
                id=8010 + i,
                patient_id=6008,
                order_id=7005,
                scheduled_date=task_date,
                status=TaskStatus.COMPLETED if i < 5 else TaskStatus.PENDING
            )
            db_session.add(task)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.get(f"/rounding/patients/{6008}")

            assert response.status_code == 200
            data = response.json()
            assert "daily_compliance" in data
            assert len(data["daily_compliance"]) == 7
            assert "compliance_rate" in data

        finally:
            app.dependencies.TEST_MODE = original_test_mode


class TestGetAbnormalPatients:
    """测试获取异常患者"""

    def test_get_abnormal_patients_empty(self, test_client: TestClient, db_session: Session):
        """测试没有异常患者"""
        user = User(id=6009, phone="13800003009", nickname="医生4")
        db_session.add(user)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.get("/rounding/patients/abnormal")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

        finally:
            app.dependencies.TEST_MODE = original_test_mode

    def test_get_abnormal_patients_with_overdue(self, test_client: TestClient, db_session: Session):
        """测试有超时任务的异常患者"""
        patient = User(id=6010, phone="13800003010", nickname="异常患者")
        db_session.add(patient)

        order = MedicalOrder(
            id=7006,
            patient_id=6010,
            title="任务",
            start_date=date.today()
        )
        db_session.add(order)
        db_session.commit()

        task = TaskInstance(
            id=8020,
            patient_id=6010,
            order_id=7006,
            scheduled_date=date.today(),
            status=TaskStatus.OVERDUE
        )
        db_session.add(task)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.get("/rounding/patients/abnormal")

            assert response.status_code == 200
            data = response.json()
            # 应该返回异常患者
            assert len(data) >= 1
            # 检查返回的患者状态
            if data:
                assert data[0]["status"] == "danger"

        finally:
            app.dependencies.TEST_MODE = original_test_mode


class TestGetRoundingStats:
    """测试获取统计数据"""

    def test_get_stats(self, test_client: TestClient, db_session: Session):
        """测试获取统计数据"""
        user = User(id=6011, phone="13800003011", nickname="医生5")
        db_session.add(user)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.get("/rounding/stats")

            assert response.status_code == 200
            data = response.json()
            assert "total_patients" in data
            assert "abnormal_patients" in data
            assert "high_risk_patients" in data
            assert "date" in data

        finally:
            app.dependencies.TEST_MODE = original_test_mode
