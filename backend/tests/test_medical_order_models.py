"""
医嘱执行监督系统模型测试
"""
import pytest
import sys
import os
from datetime import date, time

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.medical_order import OrderType, ScheduleType, OrderStatus, TaskStatus
from app.models.user import User


def test_order_type_enum():
    assert OrderType.MEDICATION == "medication"
    assert OrderType.MONITORING == "monitoring"
    assert OrderType.BEHAVIOR == "behavior"
    assert OrderType.FOLLOWUP == "followup"


def test_schedule_type_enum():
    assert ScheduleType.ONCE == "once"
    assert ScheduleType.DAILY == "daily"
    assert ScheduleType.WEEKLY == "weekly"
    assert ScheduleType.CUSTOM == "custom"


def test_order_status_enum():
    assert OrderStatus.DRAFT == "draft"
    assert OrderStatus.ACTIVE == "active"
    assert OrderStatus.COMPLETED == "completed"
    assert OrderStatus.STOPPED == "stopped"


def test_task_status_enum():
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.COMPLETED == "completed"
    assert TaskStatus.OVERDUE == "overdue"
    assert TaskStatus.SKIPPED == "skipped"


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


def test_create_medical_order(db_session):
    """测试创建医嘱"""
    from app.models.medical_order import MedicalOrder

    # 创建测试用户
    user = User(phone="13800000001", nickname="测试患者")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 创建医嘱
    order = MedicalOrder(
        patient_id=user.id,
        doctor_id=None,  # AI生成时为空
        order_type=OrderType.MEDICATION,
        title="胰岛素注射",
        description="每日三餐前注射，每次4单位",
        schedule_type=ScheduleType.DAILY,
        start_date=date.today(),
        end_date=date.today().replace(month=date.today().month + 1),
        frequency="每日3次",
        reminder_times=["08:00", "12:00", "18:00"],
        ai_generated=True,
        status=OrderStatus.DRAFT
    )

    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    assert order.id is not None
    assert order.title == "胰岛素注射"
    assert order.ai_generated is True
    assert order.status == OrderStatus.DRAFT
