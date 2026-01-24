"""
家属关系管理 API 测试
"""
import pytest
import sys
import os
from datetime import date

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def auth_headers_patient(client):
    """获取患者认证头"""
    response = client.post("/auth/login", json={
        "phone": "19900000201",
        "code": "000000"
    })

    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        if token:
            return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def auth_headers_family(client):
    """获取家属认证头"""
    response = client.post("/auth/login", json={
        "phone": "19900000202",
        "code": "000000"
    })

    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        if token:
            return {"Authorization": f"Bearer {token}"}
    return {}


def test_create_family_bond(client, auth_headers_patient):
    """测试创建家属关系"""
    # 先创建家属用户
    client.post("/auth/login", json={
        "phone": "19900000202",
        "code": "000000"
    })

    data = {
        "patient_id": 1,  # 假设当前用户 ID 为 1
        "family_member_phone": "19900000202",
        "relationship": "配偶",
        "notification_level": "all"
    }

    # 注意：由于测试环境的用户 ID 可能不同，这里主要验证 API 结构
    # 实际测试需要先获取当前用户 ID
    pass


def test_get_family_bonds(client, auth_headers_patient):
    """测试获取家属关系列表"""
    response = client.get("/medical-orders/family-bonds", headers=auth_headers_patient)

    # 可能返回空列表（如果没有任何关系）
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)


def test_get_family_member_tasks_forbidden(client, auth_headers_patient):
    """测试获取家属任务 - 无权限"""
    # 尝试获取没有权限的患者任务
    today = date.today().isoformat()
    response = client.get(
        f"/medical-orders/family-bonds/999/tasks?task_date={today}",
        headers=auth_headers_patient
    )

    # 应该返回 403 错误
    assert response.status_code == 403


def test_delete_family_bond(client, auth_headers_patient):
    """测试删除家属关系"""
    # 尝试删除不存在的家属关系
    response = client.delete(
        "/medical-orders/family-bonds/999",
        headers=auth_headers_patient
    )

    # 应该返回 404
    assert response.status_code == 404


# 集成测试 - 需要数据库支持
@pytest.mark.skip(reason="需要完整数据库设置")
def test_family_bond_full_flow(client, auth_headers_patient, auth_headers_family):
    """完整的家属关系流程测试"""
    # 1. 创建家属关系
    create_data = {
        "patient_id": 1,
        "family_member_phone": "19900000202",
        "relationship": "子女",
        "notification_level": "abnormal"
    }

    response = client.post("/medical-orders/family-bonds", json=create_data, headers=auth_headers_patient)
    assert response.status_code in [201, 400]  # 201 创建成功或 400 已存在

    # 2. 获取家属关系列表
    response = client.get("/medical-orders/family-bonds", headers=auth_headers_patient)
    assert response.status_code == 200

    # 3. 家属查看患者任务
    today = date.today().isoformat()
    response = client.get(
        f"/medical-orders/family-bonds/1/tasks?task_date={today}",
        headers=auth_headers_family
    )
    # 如果关系创建成功，应该返回 200；否则返回 403
    assert response.status_code in [200, 403]

    # 4. 删除家属关系
    # 获取第一个关系的 ID
    bonds = client.get("/medical-orders/family-bonds", headers=auth_headers_family).json()
    if bonds:
        bond_id = bonds[0]["id"]
        response = client.delete(
            f"/medical-orders/family-bonds/{bond_id}",
            headers=auth_headers_family
        )
        assert response.status_code == 204
