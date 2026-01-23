"""
医嘱执行监督系统 Pydantic Schemas 测试
"""
import pytest
from datetime import date, time

# 添加项目路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.schemas.medical_order import (
    MedicalOrderCreateRequest, MedicalOrderResponse,
    TaskInstanceResponse, CompletionRecordRequest
)


def test_medical_order_create_schema():
    """测试医嘱创建请求 schema"""
    data = {
        "order_type": "medication",
        "title": "胰岛素注射",
        "description": "每日三餐前注射",
        "schedule_type": "daily",
        "start_date": "2024-01-23",
        "end_date": "2024-02-23",
        "frequency": "每日3次",
        "reminder_times": ["08:00", "12:00", "18:00"]
    }

    schema = MedicalOrderCreateRequest(**data)

    assert schema.order_type == "medication"
    assert schema.title == "胰岛素注射"
    assert len(schema.reminder_times) == 3


def test_completion_record_value_schema():
    """测试打卡记录数值 schema"""
    data = {
        "task_instance_id": 1,
        "completion_type": "value",
        "value": {"value": 7.8, "unit": "mmol/L"},
        "notes": "早餐后血糖正常"
    }

    schema = CompletionRecordRequest(**data)

    assert schema.completion_type == "value"
    assert schema.value["value"] == 7.8


def test_medical_order_response_schema():
    """测试医嘱响应 schema"""
    from datetime import datetime

    data = {
        "id": 1,
        "patient_id": 100,
        "doctor_id": None,
        "order_type": "medication",
        "title": "胰岛素注射",
        "description": "每日三餐前注射",
        "schedule_type": "daily",
        "start_date": "2024-01-23",
        "end_date": "2024-02-23",
        "frequency": "每日3次",
        "reminder_times": ["08:00", "12:00", "18:00"],
        "ai_generated": True,
        "status": "draft",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    schema = MedicalOrderResponse(**data)

    assert schema.id == 1
    assert schema.title == "胰岛素注射"
    assert schema.ai_generated is True


def test_task_instance_response_schema():
    """测试任务实例响应 schema"""
    data = {
        "id": 1,
        "order_id": 10,
        "patient_id": 100,
        "scheduled_date": "2024-01-23",
        "scheduled_time": "08:00",
        "status": "pending",
        "completed_at": None,
        "completion_notes": None,
        "order_title": "胰岛素注射",
        "order_type": "medication"
    }

    schema = TaskInstanceResponse(**data)

    assert schema.id == 1
    assert schema.status == "pending"
    assert schema.order_title == "胰岛素注射"
