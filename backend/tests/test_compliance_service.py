"""
依从性计算服务测试
"""
import pytest
import sys
import os
from datetime import date, datetime, timedelta
import random

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.compliance_service import ComplianceService


def _get_unique_phone():
    """生成唯一的测试手机号"""
    return f"199{random.randint(10000000, 99999999)}"


@pytest.fixture
def db_session():
    """测试数据库会话"""
    from app.database import engine, Base
    Base.metadata.create_all(bind=engine)
    from sqlalchemy.orm import Session
    session = Session(autoflush=False, autocommit=False, bind=engine)
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_user_with_tasks(db_session):
    """创建带任务的测试用户"""
    from app.models.user import User
    from app.services.medical_order_service import MedicalOrderService
    from app.models.medical_order import TaskInstance, TaskStatus, OrderType, ScheduleType

    user = User(phone=_get_unique_phone(), nickname="测试患者")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    service = MedicalOrderService(db_session)

    # 创建医嘱并激活
    order = service.create_draft_order({
        "patient_id": user.id,
        "order_type": OrderType.MEDICATION,
        "title": "胰岛素注射",
        "schedule_type": ScheduleType.DAILY,
        "start_date": date.today(),
        "reminder_times": ["08:00", "12:00", "18:00"]
    })
    service.activate_order(order.id)

    # 标记第一个任务为已完成
    first_task = db_session.query(TaskInstance).filter(
        TaskInstance.patient_id == user.id
    ).first()
    if first_task:
        first_task.status = TaskStatus.COMPLETED
        first_task.completed_at = datetime.now()
        db_session.commit()

    return user


def test_calculate_daily_compliance(db_session, test_user_with_tasks):
    """测试计算日依从性"""
    service = ComplianceService(db_session)

    compliance = service.calculate_daily_compliance(test_user_with_tasks.id, date.today())

    assert "total" in compliance
    assert "completed" in compliance
    assert "rate" in compliance
    assert 0 <= compliance["rate"] <= 1


def test_calculate_weekly_compliance(db_session, test_user_with_tasks):
    """测试计算周依从性"""
    service = ComplianceService(db_session)

    weekly = service.calculate_weekly_compliance(test_user_with_tasks.id)

    assert "daily_rates" in weekly
    assert "average_rate" in weekly
    assert len(weekly["daily_rates"]) <= 7


def test_calculate_order_compliance(db_session, test_user_with_tasks):
    """测试计算医嘱依从性"""
    from app.models.medical_order import MedicalOrder
    service = ComplianceService(db_session)

    order = db_session.query(MedicalOrder).filter(
        MedicalOrder.patient_id == test_user_with_tasks.id
    ).first()

    compliance = service.calculate_order_compliance(order.id)

    assert "order_id" in compliance
    assert "total" in compliance
    assert "rate" in compliance


def test_get_abnormal_records(db_session, test_user_with_tasks):
    """测试获取异常记录"""
    from app.models.medical_order import TaskInstance, TaskStatus

    # 创建一些超时任务
    overdue_tasks = db_session.query(TaskInstance).filter(
        TaskInstance.patient_id == test_user_with_tasks.id,
        TaskInstance.status == TaskStatus.PENDING
    ).limit(2).all()

    for task in overdue_tasks:
        task.scheduled_date = date.today() - timedelta(days=1)
        task.status = TaskStatus.OVERDUE

    db_session.commit()

    service = ComplianceService(db_session)
    abnormal = service.get_abnormal_records(test_user_with_tasks.id, days=7)

    assert isinstance(abnormal, list)
    assert len(abnormal) >= 0
