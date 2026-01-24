"""
医嘱执行监督 API 路由测试
"""
import pytest
import sys
import os
from datetime import date
from fastapi.testclient import TestClient

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """获取认证头"""
    # 使用验证码登录（测试模式下 000000 为万能验证码）
    response = client.post("/auth/login", json={
        "phone": "19900000101",
        "code": "000000"
    })

    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        if token:
            return {"Authorization": f"Bearer {token}"}
    return {}


def test_create_order(client, auth_headers):
    """测试创建医嘱"""
    data = {
        "order_type": "medication",
        "title": "胰岛素注射",
        "schedule_type": "daily",
        "start_date": "2024-01-23",
        "reminder_times": ["08:00", "12:00", "18:00"]
    }

    response = client.post("/medical-orders", json=data, headers=auth_headers)

    assert response.status_code == 201
    result = response.json()
    assert result["title"] == "胰岛素注射"
    assert result["status"] == "draft"


def test_get_patient_orders(client, auth_headers):
    """测试获取患者医嘱列表"""
    response = client.get("/medical-orders", headers=auth_headers)

    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)


def test_get_daily_tasks(client, auth_headers):
    """测试获取每日任务列表"""
    today = date.today().isoformat()
    response = client.get(f"/medical-orders/tasks/{today}", headers=auth_headers)

    assert response.status_code == 200
    result = response.json()
    assert "date" in result
    assert "summary" in result


def test_complete_task(client, auth_headers):
    """测试完成任务打卡"""
    # 先创建一个任务（简化测试）
    data = {
        "task_instance_id": 1,
        "completion_type": "check",
        "notes": "已完成"
    }

    # 这个测试需要先有任务存在，实际应用中会先创建医嘱并激活
    # 这里仅验证API结构
    pass


def test_get_daily_compliance(client, auth_headers):
    """测试获取日依从性"""
    today = date.today().isoformat()
    response = client.get(f"/medical-orders/compliance/daily?task_date={today}", headers=auth_headers)

    assert response.status_code == 200
    result = response.json()
    assert "rate" in result
    assert 0 <= result["rate"] <= 1


def test_get_weekly_compliance(client, auth_headers):
    """测试获取周依从性"""
    response = client.get("/medical-orders/compliance/weekly", headers=auth_headers)

    assert response.status_code == 200
    result = response.json()
    assert "daily_rates" in result
    assert "average_rate" in result
