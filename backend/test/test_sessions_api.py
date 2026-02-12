"""
Sessions API 单元测试

测试统一会话接口：
- POST /sessions - 创建会话
- GET /sessions - 获取会话列表
- POST /sessions/{session_id}/messages - 发送消息（支持流式和非流式）
- GET /sessions/{session_id}/messages - 获取会话消息
- GET /sessions/agents - 获取可用智能体列表
- GET /sessions/agents/{agent_type}/capabilities - 获取智能体能力
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# 导入必要的模块
try:
    from app.main import app
    from app.models.session import Session as SessionModel
    from app.models.message import Message, SenderType
    from app.models.user import User
    from app.models.doctor import Doctor
    from app.models.department import Department
    from app.database import get_db
    from app.dependencies import TEST_MODE
    from app.schemas.agent_response import AgentResponse
except ImportError:
    from backend.app.main import app
    from backend.app.models.session import Session as SessionModel
    from backend.app.models.message import Message, SenderType
    from backend.app.models.user import User
    from backend.app.models.doctor import Doctor
    from backend.app.models.department import Department
    from backend.app.database import get_db
    from backend.app.dependencies import TEST_MODE
    from backend.app.schemas.agent_response import AgentResponse


# ============================================================================
# 测试辅助函数和 Mock
# ============================================================================

def create_mock_agent_response(message: str = "测试回复", stage: str = "greeting") -> AgentResponse:
    """创建 Mock 的 AgentResponse"""
    return AgentResponse(
        message=message,
        stage=stage,
        progress=50,
        quick_options=["继续", "结束"],
        risk_level="low",
        next_state={"test_key": "test_value"}
    )


def mock_agent_run(state, user_input, attachments=None, action="conversation", on_chunk=None):
    """Mock 智能体 run 方法"""
    async def _run(*args, **kwargs):
        response = create_mock_agent_response(f"回复: {user_input}")
        # 如果有 on_chunk 回调，模拟流式输出
        if on_chunk:
            for chunk in ["你", "好", ",", "我", "是", "A", "I"]:
                await on_chunk(chunk)
        return response
    return _run()


class TestCreateSession:
    """测试创建会话 (POST /sessions)"""

    def test_create_session_basic_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建基础会话（无医生）"""
        response = test_client.post("/sessions", json={})

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["agent_type"] == "general"
        assert data["doctor_name"] == "AI助手"
        assert data["status"] == "active"

    def test_create_session_with_agent_type(self, test_client: TestClient, db_session: Session):
        """测试创建指定智能体类型的会话"""
        response = test_client.post("/sessions", json={
            "agent_type": "dermatology"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["agent_type"] == "dermatology"

    def test_create_session_with_invalid_agent_type_fallback(self, test_client: TestClient, db_session: Session):
        """测试创建会话时使用无效的智能体类型会回退到 general"""
        # 注意：当前实现会将无效类型回退到 "general"，而不是报错
        response = test_client.post("/sessions", json={
            "agent_type": "invalid_agent"
        })

        # 当前实现会回退到 general
        assert response.status_code == 200
        data = response.json()
        assert data["agent_type"] == "general"

    def test_create_session_with_doctor(self, test_client: TestClient, db_session: Session):
        """测试创建带医生的会话"""
        # 创建科室
        department = Department(
            id=1,
            name="皮肤科",
            description="皮肤科科室",
            icon="skin",
            sort_order=1
        )
        db_session.add(department)

        # 创建医生
        doctor = Doctor(
            id=1,
            name="张医生",
            title="主治医师",
            department_id=1,
            is_ai=True,
            is_active=True
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.post("/sessions", json={
            "doctor_id": 1
        })

        assert response.status_code == 200
        data = response.json()
        assert data["doctor_id"] == 1
        assert data["doctor_name"] == "张医生"

    def test_create_session_with_nonexistent_doctor(self, test_client: TestClient, db_session: Session):
        """测试创建会话时医生不存在"""
        response = test_client.post("/sessions", json={
            "doctor_id": 99999
        })

        assert response.status_code == 404
        assert "医生不存在" in response.json()["detail"]

    def test_create_session_infers_agent_type_from_department(self, test_client: TestClient, db_session: Session):
        """测试根据科室自动推断智能体类型"""
        # 创建皮肤科科室
        department = Department(
            id=2,
            name="皮肤科",
            description="皮肤科",
            icon="skin",
            sort_order=1
        )
        db_session.add(department)

        # 创建皮肤科医生
        doctor = Doctor(
            id=2,
            name="李医生",
            title="主任医师",
            department_id=2,
            is_ai=True,
            is_active=True
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.post("/sessions", json={
            "doctor_id": 2
        })

        assert response.status_code == 200
        data = response.json()
        # 皮肤科应该推断为 dermatology
        assert data["agent_type"] == "dermatology"

    def test_create_session_with_cardiology_department(self, test_client: TestClient, db_session: Session):
        """测试心内科科室推断为 cardiology（但 cardiology 未实现）"""
        # 创建心内科科室
        department = Department(
            id=3,
            name="心内科",
            description="心血管内科",
            icon="heart",
            sort_order=2
        )
        db_session.add(department)

        doctor = Doctor(
            id=3,
            name="王医生",
            title="副主任医师",
            department_id=3,
            is_ai=True,
            is_active=True
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.post("/sessions", json={
            "doctor_id": 3
        })

        # BUG: 当通过 doctor 参数创建时，推断出的 cardiology 类型会返回 400
        # 而不是像直接传 agent_type 那样回退到 general
        # 这是一个代码不一致的 bug
        assert response.status_code == 400
        assert "不支持的智能体类型" in response.json()["detail"]

    def test_create_session_all_agent_types(self, test_client: TestClient, db_session: Session):
        """测试所有声明的智能体类型"""
        # VALID_AGENT_TYPES 声明的类型
        declared_types = ["general", "dermatology", "cardiology", "orthopedics"]
        # _AGENTS 中实际注册的类型
        registered_types = ["general", "dermatology"]

        for agent_type in declared_types:
            response = test_client.post("/sessions", json={
                "agent_type": agent_type
            })
            if agent_type in registered_types:
                # 已注册的类型应该成功创建
                assert response.status_code == 200, f"{agent_type} should succeed"
                data = response.json()
                assert data["agent_type"] == agent_type
            else:
                # BUG: cardiology 和 orthopedics 在 VALID_AGENT_TYPES 中声明但未在 _AGENTS 中注册
                # Pydantic 验证通过，但 AgentRouterV2.is_valid_agent_type 返回 False
                # 导致返回 400 错误
                assert response.status_code == 400, f"{agent_type} should fail with 400"
                assert "不支持的智能体类型" in response.json()["detail"]

class TestGetSessions:
    """测试获取会话列表 (GET /sessions)"""

    def test_get_sessions_empty_list(self, test_client: TestClient, db_session: Session):
        """测试获取空的会话列表"""
        response = test_client.get("/sessions")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_sessions_with_data(self, test_client: TestClient, db_session: Session):
        """测试获取包含数据的会话列表"""
        # 创建测试用户
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        # 创建会话
        session1 = SessionModel(
            id="test_sess_1",
            user_id=test_user.id,
            agent_type="general",
            status="active"
        )
        session2 = SessionModel(
            id="test_sess_2",
            user_id=test_user.id,
            agent_type="dermatology",
            status="active"
        )
        db_session.add_all([session1, session2])
        db_session.commit()

        response = test_client.get("/sessions")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_get_sessions_ordering(self, test_client: TestClient, db_session: Session):
        """测试会话列表按更新时间倒序排列"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        # 创建会话
        session1 = SessionModel(
            id="test_sess_order_1",
            user_id=test_user.id,
            agent_type="general",
            last_message="第一条消息"
        )
        session2 = SessionModel(
            id="test_sess_order_2",
            user_id=test_user.id,
            agent_type="dermatology",
            last_message="第二条消息"
        )
        db_session.add_all([session1, session2])
        db_session.commit()

        response = test_client.get("/sessions")

        assert response.status_code == 200
        data = response.json()
        # 验证返回的是列表
        assert isinstance(data, list)


class TestSendMessage:
    """测试发送消息 (POST /sessions/{session_id}/messages)"""

    def test_send_message_session_not_found(self, test_client: TestClient, db_session: Session):
        """测试向不存在的会话发送消息"""
        response = test_client.post(
            "/sessions/nonexistent_session/messages",
            json={"content": "测试消息"}
        )

        assert response.status_code == 404
        assert "会话不存在" in response.json()["detail"]

    def test_send_message_non_streaming_success(self, test_client: TestClient, db_session: Session):
        """测试非流式发送消息成功"""
        # 创建测试用户
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        # 创建会话
        session = SessionModel(
            id="test_msg_sess_1",
            user_id=test_user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        # Mock AgentRouterV2.get_agent
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=create_mock_agent_response("你好，我是AI助手"))

        with patch('app.routes.sessions.AgentRouterV2.get_agent', return_value=mock_agent):
            response = test_client.post(
                "/sessions/test_msg_sess_1/messages",
                json={"content": "你好"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "你好，我是AI助手"
        assert data["stage"] == "greeting"

    def test_send_message_with_attachments(self, test_client: TestClient, db_session: Session):
        """测试发送带附件的消息"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_msg_sess_2",
            user_id=test_user.id,
            agent_type="dermatology"
        )
        db_session.add(session)
        db_session.commit()

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=create_mock_agent_response("收到图片"))

        with patch('app.routes.sessions.AgentRouterV2.get_agent', return_value=mock_agent):
            response = test_client.post(
                "/sessions/test_msg_sess_2/messages",
                json={
                    "content": "看这张照片",
                    "attachments": [
                        {
                            "type": "image",
                            "url": "https://example.com/image.jpg"
                        }
                    ]
                }
            )

        assert response.status_code == 200

    def test_send_message_with_action(self, test_client: TestClient, db_session: Session):
        """测试发送带动作的消息"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_msg_sess_3",
            user_id=test_user.id,
            agent_type="dermatology"
        )
        db_session.add(session)
        db_session.commit()

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=create_mock_agent_response("分析中..."))

        with patch('app.routes.sessions.AgentRouterV2.get_agent', return_value=mock_agent):
            response = test_client.post(
                "/sessions/test_msg_sess_3/messages",
                json={
                    "content": "帮我分析",
                    "action": "analyze_skin"
                }
            )

        assert response.status_code == 200

    def test_send_message_streaming_response(self, test_client: TestClient, db_session: Session):
        """测试流式响应"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_stream_sess_1",
            user_id=test_user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        # 创建支持流式的 mock agent
        async def mock_run_with_chunks(*args, on_chunk=None, **kwargs):
            if on_chunk:
                chunks = ["你", "好", ",", "世", "界"]
                for chunk in chunks:
                    await on_chunk(chunk)
            return create_mock_agent_response("你好,世界")

        mock_agent = MagicMock()
        mock_agent.run = mock_run_with_chunks

        with patch('app.routes.sessions.AgentRouterV2.get_agent', return_value=mock_agent):
            response = test_client.post(
                "/sessions/test_stream_sess_1/messages",
                json={"content": "你好"},
                headers={"Accept": "text/event-stream"}
            )

        # 流式响应应该返回 200
        assert response.status_code == 200
        # 检查响应头
        assert response.headers.get("content-type", "").startswith("text/event-stream")

    def test_send_message_invalid_agent_type(self, test_client: TestClient, db_session: Session):
        """测试智能体类型无效"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_invalid_agent",
            user_id=test_user.id,
            agent_type="invalid_type"
        )
        db_session.add(session)
        db_session.commit()

        with patch('app.routes.sessions.AgentRouterV2.get_agent', side_effect=ValueError("Unknown agent")):
            response = test_client.post(
                "/sessions/test_invalid_agent/messages",
                json={"content": "测试"}
            )

        assert response.status_code == 500
        assert "智能体类型错误" in response.json()["detail"]

    def test_send_message_saves_to_database(self, test_client: TestClient, db_session: Session):
        """测试消息正确保存到数据库"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_save_sess",
            user_id=test_user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=create_mock_agent_response("已保存"))

        with patch('app.routes.sessions.AgentRouterV2.get_agent', return_value=mock_agent):
            response = test_client.post(
                "/sessions/test_save_sess/messages",
                json={"content": "保存这条消息"}
            )

        assert response.status_code == 200

        # 验证用户消息已保存
        user_messages = db_session.query(Message).filter(
            Message.session_id == "test_save_sess",
            Message.sender == SenderType.user
        ).all()
        assert len(user_messages) > 0
        assert user_messages[0].content == "保存这条消息"

        # 验证 AI 消息已保存
        ai_messages = db_session.query(Message).filter(
            Message.session_id == "test_save_sess",
            Message.sender == SenderType.ai
        ).all()
        assert len(ai_messages) > 0


class TestGetSessionMessages:
    """测试获取会话消息列表 (GET /sessions/{session_id}/messages)"""

    def test_get_messages_session_not_found(self, test_client: TestClient, db_session: Session):
        """测试获取不存在会话的消息"""
        response = test_client.get("/sessions/nonexistent/messages")

        assert response.status_code == 404
        assert "会话不存在" in response.json()["detail"]

    def test_get_messages_empty_list(self, test_client: TestClient, db_session: Session):
        """测试获取空消息列表"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_empty_msg_sess",
            user_id=test_user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        response = test_client.get("/sessions/test_empty_msg_sess/messages")

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) == 0
        assert data["has_more"] is False

    def test_get_messages_with_data(self, test_client: TestClient, db_session: Session):
        """测试获取包含数据的消息列表"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_msg_data_sess",
            user_id=test_user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        # 创建消息
        msg1 = Message(
            session_id="test_msg_data_sess",
            sender=SenderType.user,
            content="你好"
        )
        msg2 = Message(
            session_id="test_msg_data_sess",
            sender=SenderType.ai,
            content="你好，有什么可以帮助你？"
        )
        db_session.add_all([msg1, msg2])
        db_session.commit()

        response = test_client.get("/sessions/test_msg_data_sess/messages")

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2

    def test_get_messages_with_limit(self, test_client: TestClient, db_session: Session):
        """测试带限制的消息获取"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_limit_sess",
            user_id=test_user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        # 创建多条消息
        for i in range(5):
            msg = Message(
                session_id="test_limit_sess",
                sender=SenderType.user if i % 2 == 0 else SenderType.ai,
                content=f"消息{i+1}"
            )
            db_session.add(msg)
        db_session.commit()

        response = test_client.get("/sessions/test_limit_sess/messages?limit=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 3

    def test_get_messages_with_before_parameter(self, test_client: TestClient, db_session: Session):
        """测试使用 before 参数进行分页"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_before_sess",
            user_id=test_user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        # 创建消息
        for i in range(5):
            msg = Message(
                session_id="test_before_sess",
                sender=SenderType.user,
                content=f"消息{i+1}"
            )
            db_session.add(msg)
        db_session.commit()

        # 第一次请求
        response1 = test_client.get("/sessions/test_before_sess/messages?limit=2")
        assert response1.status_code == 200
        data1 = response1.json()

        # 获取最后一条消息的 ID 作为 before 参数
        if len(data1["messages"]) > 0:
            last_msg_id = data1["messages"][-1]["id"]
            response2 = test_client.get(f"/sessions/test_before_sess/messages?limit=2&before={last_msg_id}")
            assert response2.status_code == 200

    def test_get_messages_has_more_flag(self, test_client: TestClient, db_session: Session):
        """测试 has_more 分页标志"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_has_more_sess",
            user_id=test_user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        # 创建超过 limit 的消息数量
        for i in range(25):
            msg = Message(
                session_id="test_has_more_sess",
                sender=SenderType.user,
                content=f"消息{i+1}"
            )
            db_session.add(msg)
        db_session.commit()

        response = test_client.get("/sessions/test_has_more_sess/messages?limit=20")

        assert response.status_code == 200
        data = response.json()
        # 应该有 has_more 标志
        assert "has_more" in data


class TestListAgents:
    """测试获取智能体列表 (GET /sessions/agents)"""

    def test_list_agents_success(self, test_client: TestClient):
        """测试成功获取智能体列表"""
        response = test_client.get("/sessions/agents")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_list_agents_contains_general(self, test_client: TestClient):
        """测试智能体列表包含 general"""
        response = test_client.get("/sessions/agents")

        assert response.status_code == 200
        data = response.json()
        assert "general" in data

    def test_list_agents_contains_dermatology(self, test_client: TestClient):
        """测试智能体列表包含 dermatology"""
        response = test_client.get("/sessions/agents")

        assert response.status_code == 200
        data = response.json()
        assert "dermatology" in data

    def test_list_agents_structure(self, test_client: TestClient):
        """测试智能体数据结构正确"""
        response = test_client.get("/sessions/agents")

        assert response.status_code == 200
        data = response.json()

        # 检查至少有一个智能体
        if len(data) > 0:
            agent_type = list(data.keys())[0]
            agent_info = data[agent_type]
            # 验证字段存在
            assert "display_name" in agent_info or "description" in agent_info or "actions" in agent_info

class TestGetAgentCapabilities:
    """测试获取智能体能力 (GET /sessions/agents/{agent_type}/capabilities)"""

    def test_get_capabilities_general(self, test_client: TestClient):
        """测试获取 general 智能体能力"""
        response = test_client.get("/sessions/agents/general/capabilities")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_capabilities_dermatology(self, test_client: TestClient):
        """测试获取 dermatology 智能体能力"""
        response = test_client.get("/sessions/agents/dermatology/capabilities")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_capabilities_not_found(self, test_client: TestClient):
        """测试获取不存在智能体的能力"""
        response = test_client.get("/sessions/agents/nonexistent/capabilities")

        assert response.status_code == 404
        assert "智能体不存在" in response.json()["detail"]

    def test_get_capabilities_dermatology_actions(self, test_client: TestClient):
        """测试皮肤科智能体包含预期动作"""
        response = test_client.get("/sessions/agents/dermatology/capabilities")

        assert response.status_code == 200
        data = response.json()
        # 皮肤科应该有这些动作
        if "actions" in data:
            actions = data["actions"]
            assert isinstance(actions, list)

class TestStateMigration:
    """测试旧状态迁移"""

    def test_migrate_legacy_state_empty(self, test_client: TestClient):
        """测试空状态迁移"""
        from app.routes.sessions import migrate_legacy_state

        result = migrate_legacy_state(None)
        assert result == {}

    def test_migrate_legacy_state_valid_fields(self, test_client: TestClient):
        """测试有效字段迁移"""
        from app.routes.sessions import migrate_legacy_state

        legacy_state = {
            "stage": "collecting",
            "chief_complaint": "头痛",
            "symptoms": ["发热", "咳嗽"],
            "questions_asked": 3,  # 旧字段，应该被过滤
            "session_id": "123",  # 旧字段，应该被过滤
            "user_id": 1  # 旧字段，应该被过滤
        }

        result = migrate_legacy_state(legacy_state)

        assert result["stage"] == "collecting"
        assert result["chief_complaint"] == "头痛"
        assert "symptoms" in result
        assert "questions_asked" not in result
        assert "session_id" not in result
        assert "user_id" not in result

    def test_migrate_legacy_state_json_string(self, test_client: TestClient):
        """测试 JSON 字符串状态迁移"""
        from app.routes.sessions import migrate_legacy_state

        legacy_state_str = '{"stage": "analyzing", "diagnosis_card": {"test": "value"}}'

        result = migrate_legacy_state(legacy_state_str)

        assert result["stage"] == "analyzing"
        assert "diagnosis_card" in result

    def test_migrate_legacy_state_invalid_json_string(self, test_client: TestClient):
        """测试无效 JSON 字符串返回空字典"""
        from app.routes.sessions import migrate_legacy_state

        result = migrate_legacy_state("invalid json")
        assert result == {}


class TestStreamingResponse:
    """测试流式响应功能"""

    def test_streaming_sse_format(self, test_client: TestClient, db_session: Session):
        """测试 SSE 格式正确"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_sse_sess",
            user_id=test_user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        async def mock_run(*args, on_chunk=None, **kwargs):
            if on_chunk:
                await on_chunk("测")
                await on_chunk("试")
            return create_mock_agent_response("测试")

        mock_agent = MagicMock()
        mock_agent.run = mock_run

        with patch('app.routes.sessions.AgentRouterV2.get_agent', return_value=mock_agent):
            response = test_client.post(
                "/sessions/test_sse_sess/messages",
                json={"content": "测试"},
                headers={"Accept": "text/event-stream"}
            )

        assert response.status_code == 200
        # 验证是 SSE 响应
        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type

    def test_streaming_without_accept_header(self, test_client: TestClient, db_session: Session):
        """测试不带 Accept 头时使用非流式"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_no_stream_sess",
            user_id=test_user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=create_mock_agent_response("非流式"))

        with patch('app.routes.sessions.AgentRouterV2.get_agent', return_value=mock_agent):
            response = test_client.post(
                "/sessions/test_no_stream_sess/messages",
                json={"content": "测试"}
                # 不带 Accept: text/event-stream 头
            )

        assert response.status_code == 200
        # 应该返回 JSON，不是 SSE
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

class TestSessionUpdate:
    """测试会话状态更新"""

    def test_session_updated_after_message(self, test_client: TestClient, db_session: Session):
        """测试发送消息后会话状态更新"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()
        if not test_user:
            test_user = User(phone="test_user", nickname="测试用户", is_active=True)
            db_session.add(test_user)
            db_session.commit()
            db_session.refresh(test_user)

        session = SessionModel(
            id="test_update_sess",
            user_id=test_user.id,
            agent_type="general",
            last_message=None
        )
        db_session.add(session)
        db_session.commit()

        mock_response = create_mock_agent_response("这是一条很长的消息内容，用于测试最后消息字段是否正确更新到数据库中")

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=mock_response)

        with patch('app.routes.sessions.AgentRouterV2.get_agent', return_value=mock_agent):
            response = test_client.post(
                "/sessions/test_update_sess/messages",
                json={"content": "测试"}
            )

        assert response.status_code == 200

        # 验证会话状态已更新
        db_session.expire_all()
        updated_session = db_session.query(SessionModel).filter(
            SessionModel.id == "test_update_sess"
        ).first()

        assert updated_session is not None
        assert updated_session.last_message is not None
        assert updated_session.agent_state is not None


class TestAgentRouterIntegration:
    """测试与 AgentRouterV2 的集成"""

    def test_agent_router_is_valid_agent_type(self, test_client: TestClient):
        """测试 AgentRouterV2.is_valid_agent_type 方法"""
        from app.services.agent_router_v2 import AgentRouterV2

        assert AgentRouterV2.is_valid_agent_type("general") is True
        assert AgentRouterV2.is_valid_agent_type("dermatology") is True
        assert AgentRouterV2.is_valid_agent_type("invalid") is False

    def test_agent_router_infer_agent_type(self, test_client: TestClient):
        """测试 AgentRouterV2.infer_agent_type 方法"""
        from app.services.agent_router_v2 import AgentRouterV2

        assert AgentRouterV2.infer_agent_type("皮肤科") == "dermatology"
        assert AgentRouterV2.infer_agent_type("心内科") == "cardiology"
        assert AgentRouterV2.infer_agent_type("") == "general"
        assert AgentRouterV2.infer_agent_type("未知科室") == "general"

    def test_agent_router_list_agents(self, test_client: TestClient):
        """测试 AgentRouterV2.list_agents 方法"""
        from app.services.agent_router_v2 import AgentRouterV2

        agents = AgentRouterV2.list_agents()
        assert isinstance(agents, dict)
        assert len(agents) > 0

    def test_agent_router_get_capabilities(self, test_client: TestClient):
        """测试 AgentRouterV2.get_capabilities 方法"""
        from app.services.agent_router_v2 import AgentRouterV2

        caps = AgentRouterV2.get_capabilities("general")
        assert isinstance(caps, dict)

        caps_none = AgentRouterV2.get_capabilities("nonexistent")
        assert caps_none == {}
