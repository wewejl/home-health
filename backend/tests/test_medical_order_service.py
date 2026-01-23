"""
医嘱管理服务测试
"""
import pytest
import sys
import os
from datetime import date
import random

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.medical_order_service import MedicalOrderService
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
def test_user(db_session):
    """创建测试用户"""
    from app.models.user import User
    user = User(phone=_get_unique_phone(), nickname="测试患者")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_create_draft_order(db_session, test_user):
    """测试创建草稿医嘱"""
    service = MedicalOrderService(db_session)

    order_data = {
        "patient_id": test_user.id,
        "order_type": OrderType.MEDICATION,
        "title": "胰岛素注射",
        "description": "每日三餐前注射，每次4单位",
        "schedule_type": ScheduleType.DAILY,
        "start_date": date.today(),
        "end_date": date.today().replace(month=date.today().month + 1),
        "frequency": "每日3次",
        "reminder_times": ["08:00", "12:00", "18:00"],
        "ai_generated": True
    }

    order = service.create_draft_order(order_data)

    assert order.id is not None
    assert order.title == "胰岛素注射"
    assert order.status == OrderStatus.DRAFT
    assert order.ai_generated is True


def test_activate_order(db_session, test_user):
    """测试激活医嘱"""
    service = MedicalOrderService(db_session)

    # 先创建草稿医嘱
    order_data = {
        "patient_id": test_user.id,
        "order_type": OrderType.MEDICATION,
        "title": "胰岛素注射",
        "schedule_type": ScheduleType.DAILY,
        "start_date": date.today(),
        "reminder_times": ["08:00", "12:00", "18:00"]
    }

    order = service.create_draft_order(order_data)
    assert order.status == OrderStatus.DRAFT

    # 激活医嘱
    activated = service.activate_order(order.id)

    assert activated.status == OrderStatus.ACTIVE
    assert len(activated.task_instances) > 0


def test_get_patient_orders(db_session, test_user):
    """测试获取患者医嘱列表"""
    service = MedicalOrderService(db_session)

    # 创建多个医嘱
    for i in range(3):
        service.create_draft_order({
            "patient_id": test_user.id,
            "order_type": OrderType.MEDICATION,
            "title": f"医嘱{i+1}",
            "schedule_type": ScheduleType.DAILY,
            "start_date": date.today()
        })

    # 获取医嘱列表
    orders = service.get_patient_orders(test_user.id)

    assert len(orders) >= 3
    assert all(o.patient_id == test_user.id for o in orders)
