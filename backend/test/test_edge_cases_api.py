"""
边界条件和错误路径测试

补充测试以下场景：
- 参数验证（空值、超长值、非法格式）
- 并发场景
- 边界条件（分页、排序）
- 异常数据处理
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.user import User
    from app.models.admin_user import AdminUser
    from app.models.department import Department
    from app.models.doctor import Doctor
    from app.models.medical_folder import MedicalFolder
    from app.models.medical_record import MedicalRecord
    from app.services.auth_service import AuthService
    from app.services.admin_auth_service import AdminAuthService
    from app.main import app
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.user import User
    from backend.app.models.admin_user import AdminUser
    from backend.app.models.department import Department
    from backend.app.models.doctor import Doctor
    from backend.app.models.medical_folder import MedicalFolder
    from backend.app.models.medical_record import MedicalRecord
    from backend.app.services.auth_service import AuthService
    from backend.app.services.admin_auth_service import AdminAuthService
    from backend.app.main import app


# ============================================================================
# 参数验证测试
# ============================================================================

class TestParameterValidation:
    """测试 API 参数验证"""

    def test_empty_string_params(self, test_client: TestClient, db_session: Session):
        """测试空字符串参数"""
        user = User(
            phone="13800901",
            nickname="参数测试用户1",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()

        record = MedicalRecord(
            id=str(uuid.uuid4()),
            user_id=user.id,
            folder_id=folder.id,
            title="测试记录"
        )
        db_session.add(record)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800901"
        })
        token = login_response.json()["access_token"]

        # 测试空标题
        response = test_client.put(
            f"/medical-records/{record.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": ""}
        )

        # 应该拒绝空标题
        assert response.status_code in [400, 422]

    def test_extremely_long_string(self, test_client: TestClient, db_session: Session):
        """测试超长字符串"""
        user = User(
            phone="13800902",
            nickname="参数测试用户2",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800902"
        })
        token = login_response.json()["access_token"]

        # 测试超长文件夹名（1000字符）
        long_name = "a" * 1000
        response = test_client.post(
            "/medical-folders",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": long_name}
        )

        # 可能成功或截断，不应崩溃
        assert response.status_code in [200, 201, 400, 422]

    def test_invalid_uuid_format(self, test_client: TestClient, db_session: Session):
        """测试无效的 UUID 格式"""
        user = User(
            phone="13800903",
            nickname="UUID测试用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800903"
        })
        token = login_response.json()["access_token"]

        invalid_uuids = [
            "not-a-uuid",
            "12345",
            "00000000-0000-0000-0000-000000000000",
            "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        ]

        for invalid_uuid in invalid_uuids:
            response = test_client.get(
                f"/medical-records/{invalid_uuid}",
                headers={"Authorization": f"Bearer {token}"}
            )
            # 应该拒绝无效UUID
            assert response.status_code in [400, 404]

    def test_negative_pagination(self, test_client: TestClient, db_session: Session):
        """测试负数分页参数"""
        admin = AdminUser(
            username="pagination_admin",
            email="pagination@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "pagination_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # 测试负数页码
        response = test_client.get(
            "/admin/users?page=-1",
            headers={"Authorization": f"Bearer {token}"}
        )

        # 应该处理负数或返回错误
        assert response.status_code in [200, 400]

    def test_zero_page_size(self, test_client: TestClient, db_session: Session):
        """测试零页大小"""
        admin = AdminUser(
            username="pagesize_admin",
            email="pagesize@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "pagesize_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # 测试零页大小
        response = test_client.get(
            "/admin/users?page_size=0",
            headers={"Authorization": f"Bearer {token}"}
        )

        # 应该处理或返回错误
        assert response.status_code in [200, 400]

    def test_extremely_large_page_size(self, test_client: TestClient, db_session: Session):
        """测试超大页大小"""
        admin = AdminUser(
            username="largepage_admin",
            email="largepage@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "largepage_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # 测试超大页大小（可能导致性能问题）
        response = test_client.get(
            "/admin/users?page_size=1000000",
            headers={"Authorization": f"Bearer {token}"}
        )

        # 应该限制页大小或返回错误
        assert response.status_code in [200, 400]


# ============================================================================
# 授权和权限测试
# ============================================================================

class TestAuthorizationEdgeCases:
    """测试授权边界情况"""

    def test_expired_token(self, test_client: TestClient):
        """测试过期 token"""
        # 使用格式正确但可能无效的 token
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6ImFkbWluIiwiaWF0IjoxNjE2MjAwMDAwfQ.fake"

        response = test_client.get(
            "/medical-records",
            headers={"Authorization": f"Bearer {fake_token}"}
        )

        assert response.status_code == 401

    def test_malformed_token(self, test_client: TestClient):
        """测试格式错误的 token"""
        malformed_tokens = [
            "Bearer invalid-token",
            "invalid",
            "",
            "null",
            "Bearer "
        ]

        for token in malformed_tokens:
            response = test_client.get(
                "/medical-records",
                headers={"Authorization": token}
            )
            assert response.status_code == 401

    def test_missing_auth_header(self, test_client: TestClient):
        """测试缺少认证头"""
        response = test_client.get("/medical-records")

        assert response.status_code == 401

    def test_invalid_auth_scheme(self, test_client: TestClient):
        """测试无效的认证方案"""
        response = test_client.get(
            "/medical-records",
            headers={"Authorization": "Basic token123"}
        )

        assert response.status_code == 401


# ============================================================================
# 数据类型验证测试
# ============================================================================

class TestDataTypeValidation:
    """测试数据类型验证"""

    def test_numeric_string_for_number_field(self, test_client: TestClient, db_session: Session):
        """测试数字字段使用字符串"""
        admin = AdminUser(
            username="datatype_admin",
            email="datatype@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "datatype_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # 创建科室
        dept = Department(name="测试科室", icon="heart", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        # 测试用字符串创建医生（is_active 应该是布尔）
        response = test_client.post(
            "/admin/doctors",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "测试医生",
                "department_id": str(dept.id),
                "is_active": "true",  # 字符串而非布尔
                "is_ai": "false"     # 字符串而非布尔
            }
        )

        # 应该接受字符串布尔值或返回验证错误
        assert response.status_code in [200, 201, 400, 422]

    def test_invalid_enum_value(self, test_client: TestClient, db_session: Session):
        """测试无效的枚举值"""
        admin = AdminUser(
            username="enum_admin",
            email="enum@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "enum_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # 测试无效的角色
        response = test_client.post(
            "/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "testuser",
                "email": "test@example.com",
                "role": "invalid_role"  # 无效角色
            }
        )

        # 应该拒绝无效枚举值
        assert response.status_code in [400, 422]

    def test_invalid_date_format(self, test_client: TestClient, db_session: Session):
        """测试无效的日期格式"""
        user = User(
            phone="13800904",
            nickname="日期测试用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800904"
        })
        token = login_response.json()["access_token"]

        invalid_dates = [
            "not-a-date",
            "2024-13-01",  # 无效月份
            "2024-02-30",  # 无效日期
            "01-01-2024",  # 错误顺序
        ]

        for invalid_date in invalid_dates:
            response = test_client.post(
                "/medical-records",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "folder_id": str(folder.id),
                    "title": "测试记录",
                    "record_date": invalid_date
                }
            )
            # 应该拒绝无效日期
            assert response.status_code in [400, 422]


# ============================================================================
# 并发和数据一致性测试
# ============================================================================

class TestConcurrencyAndConsistency:
    """测试并发场景和数据一致性"""

    def test_create_duplicate_resource(self, test_client: TestClient, db_session: Session):
        """测试创建重复资源"""
        admin = AdminUser(
            username="duplicate_admin",
            email="duplicate@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "duplicate_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # 创建第一个科室
        dept1 = test_client.post(
            "/admin/departments",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "心内科", "icon": "heart", "sort_order": 1}
        )

        assert dept1.status_code in [200, 201]

        # 尝试创建同名科室
        dept2 = test_client.post(
            "/admin/departments",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "心内科", "icon": "heart", "sort_order": 1}
        )

        # 可能拒绝重复或允许（取决于业务逻辑）
        assert dept2.status_code in [200, 201, 400, 409]

    def test_delete_non_existent_resource(self, test_client: TestClient, db_session: Session):
        """测试删除不存在的资源"""
        admin = AdminUser(
            username="deletenone_admin",
            email="deletenone@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "deletenone_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # 删除不存在的科室
        response = test_client.delete(
            f"/admin/departments/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # 应该返回 404
        assert response.status_code == 404

    def test_update_with_no_changes(self, test_client: TestClient, db_session: Session):
        """测试无变更的更新"""
        user = User(
            phone="13800905",
            nickname="无变更更新用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="原始文件夹名"
        )
        db_session.add(folder)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800905"
        })
        token = login_response.json()["access_token"]

        # 更新为相同值
        response = test_client.put(
            f"/medical-folders/{folder.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "原始文件夹名"}
        )

        # 应该成功（即使无变更）
        assert response.status_code == 200
