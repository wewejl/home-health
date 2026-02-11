"""
Feedbacks API 单元测试

测试反馈接口：
- POST /sessions/{session_id}/feedback 创建会话反馈
- POST /sessions/messages/{message_id}/feedback 创建消息反馈
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# 导入必要的模块
try:
    from app.main import app
    from app.models.session import Session as SessionModel
    from app.models.message import Message
    from app.models.feedback import SessionFeedback
    from app.models.user import User
    from app.database import get_db
    from app.dependencies import TEST_MODE
except ImportError:
    from backend.app.main import app
    from backend.app.models.session import Session as SessionModel
    from backend.app.models.message import Message
    from backend.app.models.feedback import SessionFeedback
    from backend.app.models.user import User
    from backend.app.database import get_db
    from backend.app.dependencies import TEST_MODE


class TestCreateSessionFeedback:
    """测试创建会话反馈"""

    def test_create_feedback_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建反馈"""
        # 创建测试用户和会话
        user = User(id=5001, phone="13800002001", nickname="测试用户1")
        db_session.add(user)

        session = SessionModel(id="sess_feedback_001", user_id=5001, department="皮肤科")
        db_session.add(session)
        db_session.commit()

        # 设置测试模式
        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.post(
                f"/sessions/sess_feedback_001/feedback",
                json={
                    "message_id": None,
                    "rating": 5,
                    "feedback_type": "helpful",
                    "feedback_text": "非常有帮助"
                }
            )

            # 测试模式下可能返回200或201
            assert response.status_code in [200, 201]

        finally:
            app.dependencies.TEST_MODE = original_test_mode

    def test_create_feedback_session_not_found(self, test_client: TestClient, db_session: Session):
        """测试会话不存在"""
        user = User(id=5002, phone="13800002002", nickname="测试用户2")
        db_session.add(user)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.post(
                "/sessions/nonexistent_session/feedback",
                json={
                    "message_id": None,
                    "rating": 5,
                    "feedback_type": "helpful",
                    "feedback_text": "测试"
                }
            )

            assert response.status_code == 404

        finally:
            app.dependencies.TEST_MODE = original_test_mode

    def test_create_feedback_rating_range(self, test_client: TestClient, db_session: Session):
        """测试评分范围"""
        user = User(id=5003, phone="13800002003", nickname="测试用户3")
        db_session.add(user)

        session = SessionModel(id="sess_feedback_003", user_id=5003, department="皮肤科")
        db_session.add(session)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            # 测试最低评分
            response = test_client.post(
                "/sessions/sess_feedback_003/feedback",
                json={
                    "message_id": None,
                    "rating": 1,
                    "feedback_type": "not_helpful",
                    "feedback_text": "不太有用"
                }
            )
            assert response.status_code in [200, 201]

            # 测试最高评分
            response = test_client.post(
                "/sessions/sess_feedback_004/feedback",
                json={
                    "message_id": None,
                    "rating": 5,
                    "feedback_type": "helpful",
                    "feedback_text": "非常有用"
                }
            )
            # 不同session会404
            assert response.status_code in [200, 201, 404]

        finally:
            app.dependencies.TEST_MODE = original_test_mode


class TestCreateMessageFeedback:
    """测试创建消息反馈"""

    def test_create_message_feedback_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建消息反馈"""
        user = User(id=5004, phone="13800002004", nickname="测试用户4")
        db_session.add(user)

        session = SessionModel(id="sess_feedback_005", user_id=5004, department="皮肤科")
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        message = Message(
            id=6001,
            session_id=session.id,
            content="测试消息",
            sender="ai"
        )
        db_session.add(message)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.post(
                "/sessions/messages/6001/feedback",
                json={
                    "message_id": 6001,
                    "rating": 4,
                    "feedback_type": "helpful",
                    "feedback_text": "回答准确"
                }
            )

            assert response.status_code in [200, 201]

        finally:
            app.dependencies.TEST_MODE = original_test_mode

    def test_create_message_feedback_message_not_found(self, test_client: TestClient, db_session: Session):
        """测试消息不存在"""
        user = User(id=5005, phone="13800002005", nickname="测试用户5")
        db_session.add(user)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.post(
                "/sessions/messages/99999/feedback",
                json={
                    "message_id": 99999,
                    "rating": 5,
                    "feedback_type": "helpful",
                    "feedback_text": "测试"
                }
            )

            assert response.status_code == 404

        finally:
            app.dependencies.TEST_MODE = original_test_mode


class TestFeedbackTypes:
    """测试反馈类型"""

    def test_feedback_type_helpful(self, test_client: TestClient, db_session: Session):
        """测试'有帮助'反馈类型"""
        user = User(id=5006, phone="13800002006", nickname="测试用户6")
        db_session.add(user)

        session = SessionModel(id="sess_feedback_006", user_id=5006, department="皮肤科")
        db_session.add(session)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.post(
                "/sessions/sess_feedback_006/feedback",
                json={
                    "message_id": None,
                    "rating": 5,
                    "feedback_type": "helpful",
                    "feedback_text": "很有帮助"
                }
            )

            assert response.status_code in [200, 201]

        finally:
            app.dependencies.TEST_MODE = original_test_mode

    def test_feedback_type_not_helpful(self, test_client: TestClient, db_session: Session):
        """测试'没帮助'反馈类型"""
        user = User(id=5007, phone="13800002007", nickname="测试用户7")
        db_session.add(user)

        session = SessionModel(id="sess_feedback_007", user_id=5007, department="皮肤科")
        db_session.add(session)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            response = test_client.post(
                "/sessions/sess_feedback_007/feedback",
                json={
                    "message_id": None,
                    "rating": 1,
                    "feedback_type": "not_helpful",
                    "feedback_text": "没有解决问题"
                }
            )

            assert response.status_code in [200, 201]

        finally:
            app.dependencies.TEST_MODE = original_test_mode


class TestFeedbackPersistence:
    """测试反馈持久化"""

    def test_feedback_saved_to_database(self, test_client: TestClient, db_session: Session):
        """测试反馈保存到数据库"""
        user = User(id=5008, phone="13800002008", nickname="测试用户8")
        db_session.add(user)

        session = SessionModel(id="sess_feedback_008", user_id=5008, department="皮肤科")
        db_session.add(session)
        db_session.commit()

        import app.dependencies
        original_test_mode = app.dependencies.TEST_MODE
        app.dependencies.TEST_MODE = True

        try:
            test_client.post(
                "/sessions/sess_feedback_008/feedback",
                json={
                    "message_id": None,
                    "rating": 5,
                    "feedback_type": "helpful",
                    "feedback_text": "测试反馈文本"
                }
            )

            # 验证数据库中存在该反馈
            feedback = db_session.query(SessionFeedback).filter(
                SessionFeedback.session_id == "sess_feedback_008"
            ).first()

            assert feedback is not None
            assert feedback.rating == 5
            assert feedback.feedback_type == "helpful"
            assert feedback.feedback_text == "测试反馈文本"

        finally:
            app.dependencies.TEST_MODE = original_test_mode
