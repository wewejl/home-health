"""
疾病管理 API 测试

测试 /admin/diseases 端点：
- GET /admin/diseases - 获取疾病列表
- POST /admin/diseases - 创建疾病
- GET /admin/diseases/{disease_id} - 获取疾病详情
- PUT /admin/diseases/{disease_id} - 更新疾病
- DELETE /admin/diseases/{disease_id} - 删除疾病
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.disease import Disease
    from app.models.admin_user import AdminUser
    from app.models.department import Department
    from app.services.admin_auth_service import AdminAuthService
    from app.main import app
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.disease import Disease
    from backend.app.models.admin_user import AdminUser
    from backend.app.models.department import Department
    from backend.app.services.admin_auth_service import AdminAuthService
    from backend.app.main import app


# ============================================================================
# 疾病管理 API 测试
# ============================================================================

class TestListDiseasesAPI:
    """测试获取疾病列表 API (GET /admin/diseases)"""

    def test_list_diseases_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取疾病列表"""
        admin = AdminUser(
            username="disease_admin",
            email="disease@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建科室
        dept = Department(name="皮肤科", icon="skin", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        # 创建疾病
        disease1 = Disease(
            name="湿疹",
            pinyin="shizhen",
            department_id=dept.id,
            sort_order=1
        )
        disease2 = Disease(
            name="皮炎",
            pinyin="piyan",
            department_id=dept.id,
            sort_order=2
        )
        db_session.add_all([disease1, disease2])
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "disease_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/diseases",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_diseases_filter_by_department(self, test_client: TestClient, db_session: Session):
        """测试按科室筛选疾病"""
        admin = AdminUser(
            username="dept_filter_admin",
            email="dept_filter@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        dept = Department(name="心内科", icon="heart", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        disease = Disease(
            name="高血压",
            pinyin="gaoxueya",
            department_id=dept.id,
            sort_order=1
        )
        db_session.add(disease)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "dept_filter_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/admin/diseases?department_id={dept.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["department_id"] == dept.id

    def test_list_diseases_search(self, test_client: TestClient, db_session: Session):
        """测试搜索疾病"""
        admin = AdminUser(
            username="search_admin",
            email="search@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        disease = Disease(
            name="感冒",
            pinyin="ganmao",
            sort_order=1
        )
        db_session.add(disease)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "search_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/diseases?search=感冒",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestCreateDiseaseAPI:
    """测试创建疾病 API (POST /admin/diseases)"""

    def test_create_disease_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建疾病"""
        admin = AdminUser(
            username="create_disease",
            email="create_disease@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        dept = Department(name="消化科", icon="stomach", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "create_disease",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            "/admin/diseases",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "胃炎",
                "pinyin": "weiyan",
                "department_id": dept.id,
                "overview": "胃部炎症"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "胃炎"
        assert data["pinyin"] == "weiyan"

    def test_create_disease_without_auth(self, test_client: TestClient):
        """测试未认证创建疾病"""
        response = test_client.post(
            "/admin/diseases",
            json={
                "name": "测试疾病",
                "pinyin": "ceshijibing"
            }
        )

        assert response.status_code == 401


class TestGetDiseaseAPI:
    """测试获取疾病详情 API (GET /admin/diseases/{disease_id})"""

    def test_get_disease_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取疾病详情"""
        admin = AdminUser(
            username="get_disease",
            email="get_disease@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        disease = Disease(
            name="糖尿病",
            pinyin="tangniaobing",
            overview="内分泌疾病",
            sort_order=1
        )
        db_session.add(disease)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "get_disease",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/admin/diseases/{disease.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "糖尿病"

    def test_get_disease_not_found(self, test_client: TestClient, db_session: Session):
        """测试获取不存在的疾病"""
        admin = AdminUser(
            username="get_disease2",
            email="get_disease2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "get_disease2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/diseases/99999",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert "疾病不存在" in response.json()["detail"]


class TestUpdateDiseaseAPI:
    """测试更新疾病 API (PUT /admin/diseases/{disease_id})"""

    def test_update_disease_success(self, test_client: TestClient, db_session: Session):
        """测试成功更新疾病"""
        admin = AdminUser(
            username="update_disease",
            email="update_disease@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        disease = Disease(
            name="鼻炎",
            pinyin="biyan",
            overview="鼻部炎症",
            sort_order=1
        )
        db_session.add(disease)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "update_disease",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            f"/admin/diseases/{disease.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "overview": "鼻黏膜炎症"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overview"] == "鼻黏膜炎症"

    def test_update_disease_not_found(self, test_client: TestClient, db_session: Session):
        """测试更新不存在的疾病"""
        admin = AdminUser(
            username="update_disease2",
            email="update_disease2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "update_disease2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            "/admin/diseases/99999",
            headers={"Authorization": f"Bearer {token}"},
            json={"overview": "更新描述"}
        )

        assert response.status_code == 404


class TestDeleteDiseaseAPI:
    """测试删除疾病 API (DELETE /admin/diseases/{disease_id})"""

    def test_delete_disease_success(self, test_client: TestClient, db_session: Session):
        """测试成功删除疾病"""
        admin = AdminUser(
            username="delete_disease",
            email="delete_disease@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        disease = Disease(
            name="扁桃体炎",
            pinyin="biantaotiyan",
            sort_order=1
        )
        db_session.add(disease)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "delete_disease",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.delete(
            f"/admin/diseases/{disease.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        # 验证疾病已被删除
        deleted = db_session.query(Disease).filter(Disease.id == disease.id).first()
        assert deleted is None

    def test_delete_disease_not_found(self, test_client: TestClient, db_session: Session):
        """测试删除不存在的疾病"""
        admin = AdminUser(
            username="delete_disease2",
            email="delete_disease2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "delete_disease2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.delete(
            "/admin/diseases/99999",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
