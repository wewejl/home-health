"""
药品管理 API 测试

测试 /admin/drugs 端点：
- GET /admin/drugs - 获取药品列表（分页）
- POST /admin/drugs - 创建药品
- GET /admin/drugs/{drug_id} - 获取药品详情
- PUT /admin/drugs/{drug_id} - 更新药品
- DELETE /admin/drugs/{drug_id} - 删除药品

测试 /admin/drug-categories 端点：
- GET /admin/drug-categories - 获取药品分类列表
- POST /admin/drug-categories - 创建药品分类
- PUT /admin/drug-categories/{category_id} - 更新药品分类
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.drug import Drug, DrugCategory
    from app.models.admin_user import AdminUser
    from app.services.admin_auth_service import AdminAuthService
    from app.main import app
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.drug import Drug, DrugCategory
    from backend.app.models.admin_user import AdminUser
    from backend.app.services.admin_auth_service import AdminAuthService
    from backend.app.main import app


# ============================================================================
# 药品管理 API 测试
# ============================================================================

class TestListDrugsAPI:
    """测试获取药品列表 API (GET /admin/drugs)"""

    def test_list_drugs_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取药品列表"""
        admin = AdminUser(
            username="drug_admin",
            email="drug@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "drug_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/drugs",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_drugs_pagination(self, test_client: TestClient, db_session: Session):
        """测试药品列表分页"""
        admin = AdminUser(
            username="page_admin",
            email="page@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "page_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/drugs?skip=0&limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10

    def test_list_drugs_search(self, test_client: TestClient, db_session: Session):
        """测试搜索药品"""
        admin = AdminUser(
            username="search_admin",
            email="search@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建药品分类
        category = DrugCategory(name="感冒药", icon="pill", sort_order=1)
        db_session.add(category)
        db_session.commit()

        # 创建药品
        drug = Drug(
            name="感冒灵",
            pinyin="ganmaoling",
            category_id=category.id,
            common_brands="999感冒灵",
            is_active=True
        )
        db_session.add(drug)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "search_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/drugs?search=感冒",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1


class TestCreateDrugAPI:
    """测试创建药品 API (POST /admin/drugs)"""

    def test_create_drug_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建药品"""
        admin = AdminUser(
            username="create_drug",
            email="create_drug@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建药品分类
        category = DrugCategory(name="止痛药", icon="capsule", sort_order=1)
        db_session.add(category)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "create_drug",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            "/admin/drugs",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "布洛芬",
                "pinyin": "buluofen",
                "common_brands": "芬必得",
                "category_ids": [category.id],
                "dosage": "0.3g",
                "indications": "止痛"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "布洛芬"

    def test_create_drug_without_auth(self, test_client: TestClient):
        """测试未认证创建药品"""
        response = test_client.post(
            "/admin/drugs",
            json={
                "name": "阿司匹林",
                "pinyin": "asipilin"
            }
        )

        assert response.status_code == 401


class TestGetDrugAPI:
    """测试获取药品详情 API (GET /admin/drugs/{drug_id})"""

    def test_get_drug_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取药品详情"""
        admin = AdminUser(
            username="get_drug",
            email="get_drug@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        category = DrugCategory(name="抗生素", icon="pill", sort_order=1)
        db_session.add(category)
        db_session.commit()

        drug = Drug(
            name="阿莫西林",
            pinyin="amoxilin",
            category_id=category.id,
            is_active=True
        )
        db_session.add(drug)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "get_drug",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/admin/drugs/{drug.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "阿莫西林"

    def test_get_drug_not_found(self, test_client: TestClient, db_session: Session):
        """测试获取不存在的药品"""
        admin = AdminUser(
            username="not_found",
            email="not_found@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "not_found",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/drugs/99999",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert "药品不存在" in response.json()["detail"]


class TestUpdateDrugAPI:
    """测试更新药品 API (PUT /admin/drugs/{drug_id})"""

    def test_update_drug_success(self, test_client: TestClient, db_session: Session):
        """测试成功更新药品"""
        admin = AdminUser(
            username="update_drug",
            email="update_drug@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        category = DrugCategory(name="维生素", icon="vitamin", sort_order=1)
        db_session.add(category)
        db_session.commit()

        drug = Drug(
            name="维生素C",
            pinyin="weishengsuC",
            category_id=category.id,
            is_active=True
        )
        db_session.add(drug)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "update_drug",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            f"/admin/drugs/{drug.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "indications": "补充维生素C"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "补充维生素C" in data["indications"]


class TestDeleteDrugAPI:
    """测试删除药品 API (DELETE /admin/drugs/{drug_id})"""

    def test_delete_drug_success(self, test_client: TestClient, db_session: Session):
        """测试成功删除药品"""
        admin = AdminUser(
            username="delete_drug",
            email="delete_drug@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        category = DrugCategory(name="中成药", icon="herb", sort_order=1)
        db_session.add(category)
        db_session.commit()

        drug = Drug(
            name="板蓝根",
            pinyin="banlangen",
            category_id=category.id,
            is_active=True
        )
        db_session.add(drug)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "delete_drug",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.delete(
            f"/admin/drugs/{drug.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        # 验证药品已删除
        deleted = db_session.query(Drug).filter(Drug.id == drug.id).first()
        assert deleted is None


class TestDrugCategoriesAPI:
    """测试药品分类 API"""

    def test_list_drug_categories_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取药品分类列表"""
        admin = AdminUser(
            username="cat_admin",
            email="cat@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "cat_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/drug-categories",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_drug_category_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建药品分类"""
        admin = AdminUser(
            username="create_cat",
            email="create_cat@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "create_cat",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            "/admin/drug-categories",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "外用药品",
                "icon": "external",
                "display_type": "grid"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "外用药品"
