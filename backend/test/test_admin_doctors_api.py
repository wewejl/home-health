"""
医生管理 API 测试

测试 /admin/doctors 端点：
- GET /admin/doctors - 获取医生列表
- POST /admin/doctors - 创建医生
- GET /admin/doctors/{doctor_id} - 获取医生详情
- PUT /admin/doctors/{doctor_id} - 更新医生
- DELETE /admin/doctors/{doctor_id} - 删除医生
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.doctor import Doctor
    from app.models.admin_user import AdminUser
    from app.models.department import Department
    from app.services.admin_auth_service import AdminAuthService
    from app.main import app
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.doctor import Doctor
    from backend.app.models.admin_user import AdminUser
    from backend.app.models.department import Department
    from backend.app.services.admin_auth_service import AdminAuthService
    from backend.app.main import app


# ============================================================================
# 医生管理 API 测试
# ============================================================================

class TestListDoctorsAPI:
    """测试获取医生列表 API (GET /admin/doctors)"""

    def test_list_doctors_all(self, test_client: TestClient, db_session: Session):
        """测试获取所有医生"""
        admin = AdminUser(
            username="doc_list",
            email="doc_list@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "doc_list",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/doctors",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_doctors_filter_by_department(self, test_client: TestClient, db_session: Session):
        """测试按科室筛选医生"""
        admin = AdminUser(
            username="dept_filter",
            email="dept_filter@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建科室
        dept1 = Department(name="内科", icon="heart", sort_order=1)
        dept2 = Department(name="外科", icon="scissors", sort_order=2)
        db_session.add_all([dept1, dept2])
        db_session.commit()

        # 创建不同科室的医生
        doc1 = Doctor(name="张医生", department_id=dept1.id, is_ai=True, is_active=True)
        doc2 = Doctor(name="李医生", department_id=dept2.id, is_ai=True, is_active=True)
        db_session.add_all([doc1, doc2])
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "dept_filter",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/admin/doctors?department_id={dept1.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "张医生"

    def test_list_doctors_filter_ai_only(self, test_client: TestClient, db_session: Session):
        """测试筛选AI医生"""
        admin = AdminUser(
            username="ai_filter",
            email="ai_filter@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        doc1 = Doctor(name="AI医生1", is_ai=True, is_active=True)
        doc2 = Doctor(name="真人医生", is_ai=False, is_active=True)
        db_session.add_all([doc1, doc2])
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "ai_filter",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/doctors?is_ai=true",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_ai"] is True


class TestCreateDoctorAPI:
    """测试创建医生 API (POST /admin/doctors)"""

    def test_create_doctor_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建医生"""
        admin = AdminUser(
            username="create_doc",
            email="create_doc@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建科室
        dept = Department(name="眼科", icon="eye", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "create_doc",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            "/admin/doctors",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "王医生",
                "title": "主任医师",
                "department_id": dept.id,
                "is_ai": True,
                "is_active": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "王医生"

    def test_create_doctor_invalid_department(self, test_client: TestClient, db_session: Session):
        """测试创建医生时科室不存在"""
        admin = AdminUser(
            username="create_doc2",
            email="create_doc2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "create_doc2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            "/admin/doctors",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "测试医生",
                "department_id": 99999,  # 不存在的科室
                "is_ai": True,
                "is_active": True
            }
        )

        assert response.status_code == 400
        assert "科室不存在" in response.json()["detail"]


class TestGetDoctorAPI:
    """测试获取医生详情 API (GET /admin/doctors/{doctor_id})"""

    def test_get_doctor_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取医生详情"""
        admin = AdminUser(
            username="get_doc",
            email="get_doc@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        dept = Department(name="耳鼻喉", icon="ear", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        doctor = Doctor(
            name="赵医生",
            title="副主任医师",
            department_id=dept.id,
            is_ai=False,
            is_active=True
        )
        db_session.add(doctor)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "get_doc",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/admin/doctors/{doctor.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "赵医生"

    def test_get_doctor_not_found(self, test_client: TestClient, db_session: Session):
        """测试获取不存在的医生"""
        admin = AdminUser(
            username="get_doc2",
            email="get_doc2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "get_doc2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/doctors/99999",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert "医生不存在" in response.json()["detail"]


class TestUpdateDoctorAPI:
    """测试更新医生 API (PUT /admin/doctors/{doctor_id})"""

    def test_update_doctor_success(self, test_client: TestClient, db_session: Session):
        """测试成功更新医生"""
        admin = AdminUser(
            username="update_doc",
            email="update_doc@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        dept = Department(name="神经内科", icon="brain", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        doctor = Doctor(
            name="孙医生",
            title="主治医师",
            department_id=dept.id,
            is_ai=False,
            is_active=True
        )
        db_session.add(doctor)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "update_doc",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            f"/admin/doctors/{doctor.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "主任医师",
                "is_active": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "主任医师"
        assert data["is_active"] is False

    def test_update_doctor_not_found(self, test_client: TestClient, db_session: Session):
        """测试更新不存在的医生"""
        admin = AdminUser(
            username="update_doc2",
            email="update_doc2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "update_doc2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            "/admin/doctors/99999",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "主治医师"}
        )

        assert response.status_code == 404


class TestDeleteDoctorAPI:
    """测试删除医生 API (DELETE /admin/doctors/{doctor_id})"""

    def test_delete_doctor_success(self, test_client: TestClient, db_session: Session):
        """测试成功删除医生"""
        admin = AdminUser(
            username="delete_doc",
            email="delete_doc@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        dept = Department(name="康复科", icon=" Rehab", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        doctor = Doctor(
            name="周医生",
            title="康复师",
            department_id=dept.id,
            is_ai=False,
            is_active=True
        )
        db_session.add(doctor)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "delete_doc",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.delete(
            f"/admin/doctors/{doctor.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        # 验证医生已被删除
        deleted = db_session.query(Doctor).filter(Doctor.id == doctor.id).first()
        assert deleted is None

    def test_delete_doctor_not_found(self, test_client: TestClient, db_session: Session):
        """测试删除不存在的医生"""
        admin = AdminUser(
            username="delete_doc2",
            email="delete_doc2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "delete_doc2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.delete(
            "/admin/doctors/99999",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
