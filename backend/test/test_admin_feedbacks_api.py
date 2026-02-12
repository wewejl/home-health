"""
管理员反馈管理 API 测试

测试 /admin/feedbacks 端点：
- GET /admin/feedbacks - 获取反馈列表
- GET /admin/feedbacks/{feedback_id} - 获取反馈详情
- PUT /admin/feedbacks/{feedback_id}/handle - 处理反馈
- GET /admin/feedbacks/stats/summary - 获取反馈统计
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.feedback import SessionFeedback
    from app.models.admin_user import AdminUser
    from app.services.admin_auth_service import AdminAuthService
    from app.main import app
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.feedback import SessionFeedback
    from backend.app.models.admin_user import AdminUser
    from backend.app.services.admin_auth_service import AdminAuthService
    from backend.app.main import app


# ============================================================================
# 管理员反馈 API 测试
# ============================================================================

class TestListFeedbacksAPI:
    """测试获取反馈列表 API (GET /admin/feedbacks)"""

    def test_list_feedbacks_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取反馈列表"""
        admin = AdminUser(
            username="feedback_admin",
            email="feedback@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建一些反馈
        feedback1 = SessionFeedback(
            user_id=1,
            session_id="test_session_1",
            message_id=1,
            feedback_type="helpful",
            rating=5,
            status="pending"
        )
        feedback2 = SessionFeedback(
            user_id=2,
            session_id="test_session_2",
            message_id=2,
            feedback_type="unhelpful",
            rating=2,
            status="reviewed"
        )
        db_session.add_all([feedback1, feedback2])
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "feedback_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/feedbacks",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_feedbacks_filter_by_status(self, test_client: TestClient, db_session: Session):
        """测试按状态筛选反馈"""
        admin = AdminUser(
            username="status_admin",
            email="status@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建不同状态的反馈
        feedback1 = SessionFeedback(
            user_id=1,
            session_id="test_session",
            message_id=1,
            feedback_type="helpful",
            rating=5,
            status="pending"
        )
        feedback2 = SessionFeedback(
            user_id=2,
            session_id="test_session2",
            message_id=2,
            feedback_type="helpful",
            rating=4,
            status="resolved"
        )
        db_session.add_all([feedback1, feedback2])
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "status_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/feedbacks?status=pending",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert all(f["status"] == "pending" for f in data)

    def test_list_feedbacks_filter_by_type(self, test_client: TestClient, db_session: Session):
        """测试按类型筛选反馈"""
        admin = AdminUser(
            username="type_admin",
            email="type@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建不同类型的反馈
        feedback1 = SessionFeedback(
            user_id=1,
            session_id="test_session",
            message_id=1,
            feedback_type="helpful",
            rating=5,
            status="pending"
        )
        feedback2 = SessionFeedback(
            user_id=2,
            session_id="test_session2",
            message_id=2,
            feedback_type="unsafe",
            rating=1,
            status="pending"
        )
        db_session.add_all([feedback1, feedback2])
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "type_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/feedbacks?feedback_type=helpful",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert all(f["feedback_type"] == "helpful" for f in data)


class TestGetFeedbackAPI:
    """测试获取反馈详情 API (GET /admin/feedbacks/{feedback_id})"""

    def test_get_feedback_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取反馈详情"""
        admin = AdminUser(
            username="get_feedback",
            email="get_feedback@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        feedback = SessionFeedback(
            user_id=1,
            session_id="test_session",
            message_id=1,
            feedback_type="helpful",
            rating=5,
            status="pending",
            feedback_text="很有帮助"
        )
        db_session.add(feedback)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "get_feedback",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/admin/feedbacks/{feedback.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["feedback_text"] == "很有帮助"

    def test_get_feedback_not_found(self, test_client: TestClient, db_session: Session):
        """测试获取不存在的反馈"""
        admin = AdminUser(
            username="not_found_fb",
            email="not_found@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "not_found_fb",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/feedbacks/99999",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert "反馈不存在" in response.json()["detail"]


class TestHandleFeedbackAPI:
    """测试处理反馈 API (PUT /admin/feedbacks/{feedback_id}/handle)"""

    def test_handle_feedback_success(self, test_client: TestClient, db_session: Session):
        """测试成功处理反馈"""
        admin = AdminUser(
            username="handle_fb",
            email="handle@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        feedback = SessionFeedback(
            user_id=1,
            session_id="test_session",
            message_id=1,
            feedback_type="helpful",
            rating=5,
            status="pending"
        )
        db_session.add(feedback)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "handle_fb",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            f"/admin/feedbacks/{feedback.id}/handle",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "status": "resolved",
                "resolution_notes": "已处理"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"

    def test_handle_feedback_not_found(self, test_client: TestClient, db_session: Session):
        """测试处理不存在的反馈"""
        admin = AdminUser(
            username="handle_not_found",
            email="handle_not_found@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "handle_not_found",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            "/admin/feedbacks/99999/handle",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "status": "resolved",
                "resolution_notes": "处理"
            }
        )

        assert response.status_code == 404


class TestFeedbackStatsAPI:
    """测试反馈统计 API (GET /admin/feedbacks/stats/summary)"""

    def test_get_feedback_stats_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取反馈统计"""
        admin = AdminUser(
            username="stats_admin",
            email="stats@example.com",
            role="admin",
            is_active=True
        )
        admin.password_hash = AdminAuthService.hash_password("TestPassword123")
        db_session.add(admin)
        db_session.commit()

        # 创建不同状态的反馈
        feedbacks = [
            SessionFeedback(user_id=1, session_id="s1", message_id=1,
                         feedback_type="helpful", rating=5, status="pending"),
            SessionFeedback(user_id=2, session_id="s2", message_id=2,
                         feedback_type="helpful", rating=4, status="reviewed"),
            SessionFeedback(user_id=3, session_id="s3", message_id=3,
                         feedback_type="helpful", rating=5, status="resolved"),
        ]
        db_session.add_all(feedbacks)
        db_session.commit()

        login_response = test_client.post("/admin/auth/login", json={
            "username": "stats_admin",
            "password": "TestPassword123"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/admin/feedbacks/stats/summary",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pending" in data
        assert "reviewed" in data
        assert "resolved" in data
