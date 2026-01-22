"""
医嘱执行监督系统模型测试
"""
import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.medical_order import OrderType, ScheduleType, OrderStatus, TaskStatus


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
