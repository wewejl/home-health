"""
用户反馈 API 测试

测试 /sessions 端点下的反馈功能：
- POST /sessions/{session_id}/feedback - 创建会话反馈
- POST /sessions/messages/{message_id}/feedback - 创建消息反馈
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.user import User
    from app.models.session import Session as SessionModel
    from app.models.message import Message
    from app.models.feedback import SessionFeedback
    from app.dependencies import get_current_user, TEST_MODE
    from app.schemas.feedback import FeedbackCreate
    from app.main import app
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.user import User
    from backend.app.models.session import Session as SessionModel
    from backend.app.models.message import Message
    from backend.app.models.feedback import SessionFeedback
    from backend.app.dependencies import get_current_user, TEST_MODE
    from backend.app.schemas.feedback import FeedbackCreate
    from backend.app.main import app


# ============================================================================
# 用户反馈 API 测试
# ============================================================================

class TestSessionFeedbackAPI:
    """测试会话反馈 API (POST /sessions/{session_id}/feedback)"""

    def test_create_session_feedback_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建会话反馈"""
        user = User(
            phone="13800001",
            nickname="反馈用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # 创建会话
        session = SessionModel(
            id=str(uuid.uuid4()),
            user_id=user.id,
            agent_type="general",
            status="active"
        )
        db_session.add(session)
        db_session.commit()

        # 创建消息
        message = Message(
            session_id=session.id,
            sender="ai",
            content="AI 回复内容"
        )
        db_session.add(message)
        db_session.commit()

        # 登录获取 token
        login_response = test_client.post("/auth/login", json={
            "phone": "13800001"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            f"/sessions/{session.id}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message_id": message.id,
                "rating": 5,
                "feedback_type": "helpful",
                "feedback_text": "非常有帮助"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5

    def test_create_session_feedback_invalid_session(self, test_client: TestClient, db_session: Session):
        """测试会话不存在时创建反馈"""
        user = User(
            phone="13800002",
            nickname="反馈用户2",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800002"
        })
        token = login_response.json()["access_token"]

        # 使用不存在的会话ID
        fake_session_id = str(uuid.uuid4())
        response = test_client.post(
            f"/sessions/{fake_session_id}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message_id": 1,
                "rating": 5,
                "feedback_type": "helpful"
            }
        )

        assert response.status_code == 404
        assert "会话不存在" in response.json()["detail"]


class TestMessageFeedbackAPI:
    """测试消息反馈 API (POST /sessions/messages/{message_id}/feedback)"""

    def test_create_message_feedback_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建消息反馈"""
        user = User(
            phone="13800003",
            nickname="消息反馈用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # 创建会话和消息
        session = SessionModel(
            id=str(uuid.uuid4()),
            user_id=user.id,
            agent_type="general",
            status="active"
        )
        db_session.add(session)
        db_session.commit()

        message = Message(
            session_id=session.id,
            sender="ai",
            content="这是AI消息"
        )
        db_session.add(message)
        db_session.commit()

        # 登录获取 token
        login_response = test_client.post("/auth/login", json={
            "phone": "13800003"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            f"/sessions/messages/{message.id}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "rating": 4,
                "feedback_type": "unhelpful",
                "feedback_text": "不够清楚"
            }
        )

        assert response.status_code == 200

    def test_create_message_feedback_invalid_message(self, test_client: TestClient, db_session: Session):
        """测试消息不存在时创建反馈"""
        user = User(
            phone="13800004",
            nickname="消息反馈用户2",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800004"
        })
        token = login_response.json()["access_token"]

        # 使用不存在的消息ID
        response = test_client.post(
            "/sessions/messages/99999/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "rating": 5,
                "feedback_type": "helpful"
            }
        )

        assert response.status_code == 404
        assert "消息不存在" in response.json()["detail"]

    def test_create_feedback_invalid_rating(self, test_client: TestClient, db_session: Session):
        """测试无效评分"""
        user = User(
            phone="13800005",
            nickname="评分测试用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        session = SessionModel(
            id=str(uuid.uuid4()),
            user_id=user.id,
            agent_type="general",
            status="active"
        )
        db_session.add(session)
        db_session.commit()

        message = Message(
            session_id=session.id,
            sender="ai",
            content="AI消息"
        )
        db_session.add(message)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800005"
        })
        token = login_response.json()["access_token"]

        # 评分超出范围（1-5）
        response = test_client.post(
            f"/sessions/messages/{message.id}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "rating": 6,  # 无效评分
                "feedback_type": "helpful"
            }
        )

        # 应该返回验证错误
        assert response.status_code in [400, 422]

    def test_create_feedback_missing_fields(self, test_client: TestClient, db_session: Session):
        """测试缺少必填字段"""
        user = User(
            phone="13800006",
            nickname="字段测试用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        session = SessionModel(
            id=str(uuid.uuid4()),
            user_id=user.id,
            agent_type="general",
            status="active"
        )
        db_session.add(session)
        db_session.commit()

        message = Message(
            session_id=session.id,
            sender="ai",
            content="AI消息"
        )
        db_session.add(message)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800006"
        })
        token = login_response.json()["access_token"]

        # 缺少 rating
        response = test_client.post(
            f"/sessions/messages/{message.id}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "feedback_type": "helpful"
                # 缺少 rating
            }
        )

        # 应该返回验证错误
        assert response.status_code in [400, 422]
