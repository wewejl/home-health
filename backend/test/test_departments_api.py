"""
科室查询 API 测试

测试 /departments 端点：
- GET /departments - 获取科室列表
- GET /departments/{department_id}/doctors - 获取指定科室的医生列表
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.department import Department
    from app.models.doctor import Doctor
    from app.models.user import User
    from app.dependencies import get_current_user
    from app.main import app
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.department import Department
    from backend.app.models.doctor import Doctor
    from backend.app.models.user import User
    from backend.app.dependencies import get_current_user
    from backend.app.main import app


# ============================================================================
# 科室查询 API 测试
# ============================================================================

class TestGetDepartmentsAPI:
    """测试获取科室列表 API (GET /departments)"""

    def test_get_departments_all(self, test_client: TestClient, db_session: Session):
        """测试获取所有科室"""
        # 创建测试用户
        user = User(
            phone="13800888",
            nickname="测试用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取 token
        login_response = test_client.post("/auth/login", json={
            "phone": "13800888"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/departments",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_departments_primary_only(self, test_client: TestClient, db_session: Session):
        """测试只获取主要科室"""
        user = User(
            phone="13800999",
            nickname="测试用户2",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # 创建主要和次要科室
        dept1 = Department(name="心内科", icon="heart", is_primary=True, sort_order=1)
        dept2 = Department(name="皮肤科", icon="skin", is_primary=False, sort_order=2)
        db_session.add_all([dept1, dept2])
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800999"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/departments?primary_only=true",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # 应该只返回主要科室
        assert len(data) == 1
        assert data[0]["name"] == "心内科"


class TestGetDoctorsByDepartmentAPI:
    """测试获取指定科室的医生 API (GET /departments/{department_id}/doctors)"""

    def test_get_doctors_by_department_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取科室医生列表"""
        user = User(
            phone="13800777",
            nickname="测试用户3",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # 创建科室和医生
        dept = Department(name="眼科", icon="eye", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        doctor1 = Doctor(name="张医生", department_id=dept.id, is_ai=True, is_active=True)
        doctor2 = Doctor(name="李医生", department_id=dept.id, is_ai=False, is_active=True)
        db_session.add_all([doctor1, doctor2])
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800777"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/departments/{dept.id}/doctors",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_doctors_by_department_not_found(self, test_client: TestClient, db_session: Session):
        """测试获取不存在科室的医生"""
        user = User(
            phone="13800666",
            nickname="测试用户4",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800666"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/departments/99999/doctors",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # 不存在的科室应该返回空列表
        assert isinstance(data, list)
