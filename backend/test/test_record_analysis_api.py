"""
记录分析 API 测试

测试 /admin/doctors/{doctor_id}/analyze-records 端点：
- 上传病历文件
- AI 分析提取诊疗特征
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, AsyncMock

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
# 记录分析 API 测试
# ============================================================================

class TestAnalyzeMedicalRecordsAPI:
    """测试病历分析 API (POST /admin/doctors/{doctor_id}/analyze-records)"""

    def test_analyze_records_success(self, test_client: TestClient, db_session: Session):
        """测试成功分析病历记录"""
        admin = AdminUser(
            username="analyze_admin",
            email="analyze@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建医生
        dept = Department(name="心内科", icon="heart", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        doctor = Doctor(
            name="测试医生",
            department_id=dept.id,
            is_ai=True,
            is_active=True
        )
        db_session.add(doctor)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "analyze_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # Mock 文件读取和分析服务
        mock_file = Mock()
        mock_file.filename = "test.pdf"
        mock_file.read = AsyncMock(return_value=b"test content")

        # Mock RecordAnalysisService
        mock_analysis = {
            "diagnosis": ["高血压"],
            "medications": ["降压药"],
            "follow_up": "1个月后"
        }

        with patch('app.routes.record_analysis.RecordAnalysisService.analyze_records', AsyncMock(return_value=mock_analysis)):
            response = test_client.post(
                f"/admin/doctors/{doctor.id}/analyze-records",
                headers={"Authorization": f"Bearer {token}"},
                files={"files": (mock_file,)}
            )

        assert response.status_code == 200
        data = response.json()
        assert "diagnosis" in data

    def test_analyze_records_doctor_not_found(self, test_client: TestClient, db_session: Session):
        """测试医生不存在"""
        admin = AdminUser(
            username="not_found_doc",
            email="not_found@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "not_found_doc",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        mock_file = Mock()
        mock_file.filename = "test.pdf"
        mock_file.read = AsyncMock(return_value=b"test content")

        response = test_client.post(
            "/admin/doctors/99999/analyze-records",
            headers={"Authorization": f"Bearer {token}"},
            files={"files": (mock_file,)}
        )

        assert response.status_code == 404
        assert "医生不存在" in response.json()["detail"]

    def test_analyze_records_too_many_files(self, test_client: TestClient, db_session: Session):
        """测试上传文件过多"""
        admin = AdminUser(
            username="too_many_admin",
            email="too_many@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        dept = Department(name="眼科", icon="eye", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        doctor = Doctor(
            name="测试医生2",
            department_id=dept.id,
            is_ai=True,
            is_active=True
        )
        db_session.add(doctor)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "too_many_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # 创建6个文件（超过限制）
        files = []
        for i in range(6):
            mock_file = Mock()
            mock_file.filename = f"test{i}.pdf"
            mock_file.read = AsyncMock(return_value=b"test content")
            files.append(mock_file)

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/analyze-records",
            headers={"Authorization": f"Bearer {token}"},
            files={"files": files}
        )

        assert response.status_code == 400
        assert "最多支持上传" in response.json()["detail"]

    def test_analyze_records_file_too_large(self, test_client: TestClient, db_session: Session):
        """测试单个文件过大"""
        admin = AdminUser(
            username="large_file_admin",
            email="large@example.com",
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
            name="测试医生3",
            department_id=dept.id,
            is_ai=True,
            is_active=True
        )
        db_session.add(doctor)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "large_file_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        # Mock 文件（超过10MB）
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        mock_file = Mock()
        mock_file.filename = "large.pdf"
        mock_file.read = AsyncMock(return_value=large_content)

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/analyze-records",
            headers={"Authorization": f"Bearer {token}"},
            files={"files": (mock_file,)}
        )

        assert response.status_code == 400
        assert "超过" in response.json()["detail"] or "MB" in response.json()["detail"]

    def test_analyze_records_unauthorized(self, test_client: TestClient):
        """测试未授权访问"""
        # 不登录，直接访问
        response = test_client.post("/admin/doctors/1/analyze-records")

        assert response.status_code == 401

    def test_analyze_records_without_files(self, test_client: TestClient, db_session: Session):
        """测试没有上传文件"""
        admin = AdminUser(
            username="no_files_admin",
            email="no_files@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        dept = Department(name="儿科", icon="baby", sort_order=1)
        db_session.add(dept)
        db_session.commit()

        doctor = Doctor(
            name="测试医生4",
            department_id=dept.id,
            is_ai=True,
            is_active=True
        )
        db_session.add(doctor)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "no_files_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/analyze-records",
            headers={"Authorization": f"Bearer {token}"},
            json={}
        )

        # 应该返回错误（缺少文件）
        assert response.status_code in [400, 422]
