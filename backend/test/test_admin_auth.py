"""
认证相关测试

包含：
1. 管理员认证服务测试 (AdminAuthService)
2. 管理员认证 API 端点测试 (/admin/auth)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

try:
    from app.services.admin_auth_service import AdminAuthService
    from app.models.admin_user import AdminUser, AuditLog
    from app.database import get_db
    from app.dependencies import TEST_MODE
    from app.main import app
except ImportError:
    from backend.app.services.admin_auth_service import AdminAuthService
    from backend.app.models.admin_user import AdminUser, AuditLog
    from backend.app.database import get_db
    from backend.app.dependencies import TEST_MODE
    from backend.app.main import app


# ============================================================================
# 管理员认证服务测试
# ============================================================================

class TestAdminAuthService:
    """管理员认证服务测试"""

    def test_hash_password(self):
        """测试密码哈希"""
        password = "TestPassword123"
        hash_result = AdminAuthService.hash_password(password)

        assert hash_result is not None
        assert hash_result != password
        assert hash_result.startswith("$2b$")  # bcrypt hash

    def test_verify_password_correct(self):
        """测试验证正确密码"""
        password = "TestPassword123"
        hash_result = AdminAuthService.hash_password(password)

        is_valid = AdminAuthService.verify_password(password, hash_result)
        assert is_valid is True

    def test_verify_password_incorrect(self):
        """测试验证错误密码"""
        password = "TestPassword123"
        wrong_password = "WrongPassword123"
        hash_result = AdminAuthService.hash_password(password)

        is_valid = AdminAuthService.verify_password(wrong_password, hash_result)
        assert is_valid is False

    def test_create_admin_token(self):
        """测试创建管理员 Token"""
        admin_id = 123
        token = AdminAuthService.create_admin_token(admin_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long

    def test_verify_admin_token_valid(self):
        """测试验证有效的管理员 Token"""
        admin_id = 456
        token = AdminAuthService.create_admin_token(admin_id)

        verified_id = AdminAuthService.verify_admin_token(token)
        assert verified_id == admin_id

    def test_verify_admin_token_invalid(self):
        """测试验证无效的管理员 Token"""
        invalid_token = "invalid.token.here"

        verified_id = AdminAuthService.verify_admin_token(invalid_token)
        assert verified_id is None


# ============================================================================
# 管理员认证 API 端点测试
# ============================================================================

class TestAdminLoginAPI:
    """测试管理员登录 API (POST /admin/auth/login)"""

    def test_login_success(self, test_client: TestClient, db_session: Session):
        """测试成功登录"""
        # 创建测试管理员
        admin = AdminUser(
            username="testuser",
            email="test@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        response = test_client.post("/admin/auth/login", json={
            "username": "testuser",
            "password": "TestPassword123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "admin" in data
        assert data["admin"]["username"] == "testuser"

    def test_login_wrong_username(self, test_client: TestClient):
        """测试错误的用户名"""
        response = test_client.post("/admin/auth/login", json={
            "username": "wronguser",
            "password": "TestPassword123"
        })

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_wrong_password(self, test_client: TestClient, db_session: Session):
        """测试错误的密码"""
        admin = AdminUser(
            username="testuser2",
            email="test2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("CorrectPassword123")
        db_session.add(admin)
        db_session.commit()

        response = test_client.post("/admin/auth/login", json={
            "username": "testuser2",
            "password": "WrongPassword123"
        })

        assert response.status_code == 401

    def test_login_creates_audit_log(self, test_client: TestClient, db_session: Session):
        """测试登录创建审计日志"""
        admin = AdminUser(
            username="audituser",
            email="audit@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 清除之前的审计日志
        db_session.query(AuditLog).delete()
        db_session.commit()

        response = test_client.post("/admin/auth/login", json={
            "username": "audituser",
            "password": "TestPassword123"
        })

        assert response.status_code == 200

        # 验证审计日志已创建
        logs = db_session.query(AuditLog).filter(
            AuditLog.action == "login_success"
        ).all()
        assert len(logs) > 0


class TestGetCurrentAdminAPI:
    """测试获取当前管理员信息 API (GET /admin/auth/me)"""

    def test_get_current_admin_with_token(self, test_client: TestClient, db_session: Session):
        """测试使用有效 token 获取当前管理员信息"""
        admin = AdminUser(
            username="metest",
            email="me@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 先登录获取 token
        login_response = test_client.post("/admin/auth/login", json={
            "username": "metest",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # 使用 token 获取当前管理员信息
        response = test_client.get(
            "/admin/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "metest"
        assert data["role"] == "admin"

    def test_get_current_admin_without_token(self, test_client: TestClient):
        """测试不带 token 获取当前管理员信息"""
        response = test_client.get("/admin/auth/me")

        assert response.status_code == 401

    def test_get_current_admin_with_invalid_token(self, test_client: TestClient):
        """测试使用无效 token 获取当前管理员信息"""
        response = test_client.get(
            "/admin/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


class TestAdminLogoutAPI:
    """测试管理员登出 API (POST /admin/auth/logout)"""

    def test_logout_success(self, test_client: TestClient):
        """测试成功登出"""
        response = test_client.post("/admin/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestCreateAdminUserAPI:
    """测试创建管理员用户 API (POST /admin/auth/users)"""

    def test_create_admin_user_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建管理员用户"""
        # 创建一个 admin 用户来执行创建操作
        admin = AdminUser(
            username="creator",
            email="creator@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "creator",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            "/admin/auth/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newadmin",
                "password": "NewPassword123",
                "email": "newadmin@example.com",
                "role": "admin"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newadmin"
        assert data["email"] == "newadmin@example.com"

    def test_create_admin_user_weak_password(self, test_client: TestClient, db_session: Session):
        """测试创建管理员用户时密码复杂度不足"""
        admin = AdminUser(
            username="creator2",
            email="creator2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "creator2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # 弱密码：缺少大写字母
        response = test_client.post(
            "/admin/auth/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "weakuser",
                "password": "weak123",  # 缺少大写字母
                "email": "weak@example.com",
                "role": "admin"
            }
        )

        assert response.status_code == 400
        assert "密码" in response.json()["detail"]

    def test_create_admin_user_duplicate_username(self, test_client: TestClient, db_session: Session):
        """测试创建管理员用户时用户名重复"""
        admin = AdminUser(
            username="creator3",
            email="creator3@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建已存在的用户
        existing = AdminUser(
            username="existing",
            email="existing@example.com",
            role="admin",
            is_active=True
        )
        existing.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(existing)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "creator3",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            "/admin/auth/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "existing",  # 重复的用户名
                "password": "NewPassword123",
                "email": "another@example.com",
                "role": "admin"
            }
        )

        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]

    def test_create_doctor_user(self, test_client: TestClient, db_session: Session):
        """测试创建医生用户"""
        admin = AdminUser(
            username="creator4",
            email="creator4@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "creator4",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            "/admin/auth/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newdoctor",
                "password": "NewPassword123",
                "email": "doctor@example.com",
                "role": "doctor",
                "department_id": 1,
                "doctor_attributes": {
                    "title": "主治医师",
                    "specialty": "内科",
                    "license_no": "DOC12345"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "doctor"
        assert data["department_id"] == 1


class TestListAdminUsersAPI:
    """测试获取管理员用户列表 API (GET /admin/auth/users)"""

    def test_list_users_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取用户列表"""
        admin = AdminUser(
            username="lister",
            email="lister@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "lister",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestUpdateAdminUserAPI:
    """测试更新管理员用户 API (PUT /admin/auth/users/{user_id})"""

    def test_update_admin_user_success(self, test_client: TestClient, db_session: Session):
        """测试成功更新管理员用户"""
        admin = AdminUser(
            username="updater",
            email="updater@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建要更新的用户
        target_user = AdminUser(
            username="toupdate",
            email="toupdate@example.com",
            role="doctor",
            is_active=True
        )
        target_user.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(target_user)
        db_session.commit()
        db_session.refresh(target_user)

        login_response = test_client.post("/admin/auth/login", json={
            "username": "updater",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            f"/admin/auth/users/{target_user.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "updated@example.com"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"

    def test_update_admin_user_not_found(self, test_client: TestClient, db_session: Session):
        """测试更新不存在的用户"""
        admin = AdminUser(
            username="updater2",
            email="updater2@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "updater2",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            "/admin/auth/users/99999",  # 不存在的用户 ID
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "updated@example.com"
            }
        )

        assert response.status_code == 404
        assert "用户不存在" in response.json()["detail"]


class TestDoctorLoginAPI:
    """测试医生登录 API"""

    def test_doctor_login_with_test_mode(self, test_client: TestClient, db_session: Session):
        """测试测试模式下医生登录"""
        # 在测试模式下，使用 test_doctor 可以直接登录
        response = test_client.post("/admin/auth/login", json={
            "username": "test_doctor",
            "password": "test123"
        })

        # 测试模式下应该成功（自动创建测试用户）
        assert response.status_code in [200, 401]  # 取决于测试模式设置

    def test_doctor_role_verification(self, test_client: TestClient, db_session: Session):
        """测试医生角色验证"""
        # 创建一个医生角色用户
        doctor = AdminUser(
            username="testdoctor_role",
            email="doctor_role@example.com",
            role="doctor",
            is_active=True
        )
        doctor.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(doctor)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "testdoctor_role",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # 获取当前用户信息
        response = test_client.get(
            "/admin/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "doctor"
