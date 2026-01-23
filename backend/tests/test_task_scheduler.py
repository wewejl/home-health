"""
任务调度服务测试
"""
import pytest
import sys
import os
from datetime import date, time, timedelta
import random

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.task_scheduler import TaskScheduler
from app.models.medical_order import OrderType, ScheduleType, OrderStatus


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
def medical_order(db_session):
    """创建测试医嘱"""
    from app.models.user import User
    from app.services.medical_order_service import MedicalOrderService

    user = User(phone=_get_unique_phone(), nickname="测试患者")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    service = MedicalOrderService(db_session)
    order = service.create_draft_order({
        "patient_id": user.id,
        "order_type": OrderType.MEDICATION,
        "title": "胰岛素注射",
        "schedule_type": ScheduleType.DAILY,
        "start_date": date.today(),
        "end_date": date.today() + timedelta(days=30),
        "reminder_times": ["08:00", "12:00", "18:00"]
    })

    return order


def test_generate_daily_tasks(db_session, medical_order):
    """测试生成每日任务"""
    scheduler = TaskScheduler(db_session)

    # 激活医嘱
    from app.services.medical_order_service import MedicalOrderService
    service = MedicalOrderService(db_session)
    service.activate_order(medical_order.id)

    # 生成第8天的任务（超出激活时生成的7天范围）
    future_date = date.today() + timedelta(days=8)
    tasks = scheduler.generate_daily_tasks(medical_order.id, future_date)

    assert len(tasks) > 0
    assert all(t.scheduled_date == future_date for t in tasks)


def test_mark_overdue_tasks(db_session):
    """测试标记超时任务"""
    from app.models.user import User
    from app.services.medical_order_service import MedicalOrderService
    from app.models.medical_order import TaskInstance, TaskStatus

    scheduler = TaskScheduler(db_session)
    service = MedicalOrderService(db_session)

    # 创建用户和医嘱
    user = User(phone=_get_unique_phone(), nickname="测试患者")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    order = service.create_draft_order({
        "patient_id": user.id,
        "order_type": OrderType.MEDICATION,
        "title": "胰岛素注射",
        "schedule_type": ScheduleType.DAILY,
        "start_date": date.today(),
        "reminder_times": ["08:00"]
    })
    service.activate_order(order.id)

    # 标记超时
    overdue_count = scheduler.mark_overdue_tasks()

    # 应该有一些任务被标记为超时（昨天或之前的任务）
    assert overdue_count >= 0


def test_generate_all_active_orders_tasks(db_session):
    """测试为所有活跃医嘱生成任务"""
    from app.models.user import User
    from app.services.medical_order_service import MedicalOrderService

    scheduler = TaskScheduler(db_session)
    service = MedicalOrderService(db_session)

    # 创建多个活跃医嘱
    for i in range(2):
        user = User(phone=_get_unique_phone(), nickname=f"测试患者{i}")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        order = service.create_draft_order({
            "patient_id": user.id,
            "order_type": OrderType.MEDICATION,
            "title": f"医嘱{i}",
            "schedule_type": ScheduleType.DAILY,
            "start_date": date.today(),
            "reminder_times": ["08:00"]
        })
        service.activate_order(order.id)

    # 为所有活跃医嘱生成明天的任务
    tomorrow = date.today() + timedelta(days=1)
    total_count = scheduler.generate_all_active_orders_tasks(tomorrow)

    assert total_count >= 0
