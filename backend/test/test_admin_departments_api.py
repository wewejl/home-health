"""
科室管理 API 测试

测试 /admin/departments 端点：
- GET /admin/departments - 获取科室列表
- POST /admin/departments - 创建科室
- GET /admin/departments/{dept_id} - 获取科室详情
- PUT /admin/departments/{dept_id} - 更新科室
- DELETE /admin/departments/{dept_id} - 删除科室
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.department import Department
    from app.models.admin_user import AdminUser
    from app.models.doctor import Doctor
    from app.services.admin_auth_service import AdminAuthService
    from app.main import app
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.department import Department
    from backend.app.models.admin_user import AdminUser
    from backend.app.models.doctor import Doctor
    from backend.app.services.admin_auth_service import AdminAuthService
    from backend.app.main import app


# ============================================================================
# 科室管理 API 测试
# ============================================================================

class TestListDepartmentsAPI:
    """测试获取科室列表 API (GET /admin/departments)"""

    def test_list_departments_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取科室列表"""
        # 创建管理员用户
        admin = AdminUser(
            username="dept_admin",
            email="dept@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建一些科室
        dept1 = Department(name="内科", icon="heart", sort_order=1)
        dept2 = Department(name="外科", icon="scissors", sort_order=2)
        db_session.add_all([dept1, dept2])
        db_session.commit()

        # 登录获取 token
        login_response = test_client.post("/admin/auth/login", json={
            "username": "dept_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/departments",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_departments_includes_doctor_count(self, test_client: TestClient, db_session: Session):
        """测试科室列表包含医生数量"""
        admin = AdminUser(
            username="dept_admin2",
            email="dept2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建科室和医生
        dept = Department(name="心内科", icon="heart", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        doctor = Doctor(
            name="张医生",
            department_id=dept.id,
            is_ai=True,
            is_active=True
        )
        db_session.add(doctor)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "dept_admin2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/departments",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # 找到创建的科室
        dept_data = next((d for d in data if d["name"] == "心内科"), None)
        assert dept_data is not None
        assert dept_data["doctor_count"] >= 1


class TestCreateDepartmentAPI:
    """测试创建科室 API (POST /admin/departments)"""

    def test_create_department_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建科室"""
        admin = AdminUser(
            username="create_dept",
            email="create_dept@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "create_dept",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            "/admin/departments",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "皮肤科",
                "description": "皮肤疾病诊治",
                "icon": "skin",
                "sort_order": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "皮肤科"
        assert data["icon"] == "skin"
        assert data["is_active"] is True

    def test_create_department_without_auth(self, test_client: TestClient):
        """测试未认证创建科室"""
        response = test_client.post(
            "/admin/departments",
            json={
                "name": "测试科室",
                "icon": "test"
            }
        )

        assert response.status_code == 401


class TestGetDepartmentAPI:
    """测试获取科室详情 API (GET /admin/departments/{dept_id})"""

    def test_get_department_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取科室详情"""
        admin = AdminUser(
            username="get_dept",
            email="get_dept@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        dept = Department(name="眼科", icon="eye", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "get_dept",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/admin/departments/{dept.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "眼科"

    def test_get_department_not_found(self, test_client: TestClient, db_session: Session):
        """测试获取不存在的科室"""
        admin = AdminUser(
            username="get_dept2",
            email="get_dept2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "get_dept2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/departments/99999",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert "科室不存在" in response.json()["detail"]


class TestUpdateDepartmentAPI:
    """测试更新科室 API (PUT /admin/departments/{dept_id})"""

    def test_update_department_success(self, test_client: TestClient, db_session: Session):
        """测试成功更新科室"""
        admin = AdminUser(
            username="update_dept",
            email="update_dept@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        dept = Department(name="儿科", icon="baby", sort_order=1, is_active=True)
        db_session.add(dept)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "update_dept",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            f"/admin/departments/{dept.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "小儿科",
                "description": "儿童疾病诊治"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "小儿科"

    def test_update_department_not_found(self, test_client: TestClient, db_session: Session):
        """测试更新不存在的科室"""
        admin = AdminUser(
            username="update_dept2",
            email="update_dept2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "update_dept2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            "/admin/departments/99999",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "新名称"}
        )

        assert response.status_code == 404


class TestDeleteDepartmentAPI:
    """测试删除科室 API (DELETE /admin/departments/{dept_id})"""

    def test_delete_department_success(self, test_client: TestClient, db_session: Session):
        """测试成功删除科室"""
        admin = AdminUser(
            username="delete_dept",
            email="delete_dept@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        dept = Department(name="骨科", icon="bone", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "delete_dept",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.delete(
            f"/admin/departments/{dept.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert "删除成功" in response.json()["message"]

    def test_delete_department_with_doctors_fails(self, test_client: TestClient, db_session: Session):
        """测试删除有医生的科室失败"""
        admin = AdminUser(
            username="delete_dept2",
            email="delete_dept2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建科室和医生
        dept = Department(name="口腔科", icon="tooth", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        doctor = Doctor(
            name="李医生",
            department_id=dept.id,
            is_ai=True,
            is_active=True
        )
        db_session.add(doctor)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "delete_dept2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.delete(
            f"/admin/departments/{dept.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        assert "科室下还有医生" in response.json()["detail"]
