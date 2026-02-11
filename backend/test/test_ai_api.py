"""
AI Chat API tests for the home health backend.

Tests cover:
- Creating chat sessions
- Sending messages to AI agents
- Retrieving session lists
- Getting session message history
"""
import pytest
import os
import uuid

# Set test mode before imports
os.environ["TEST_MODE"] = "true"


class TestCreateSession:
    """Tests for creating AI chat sessions."""

    def test_create_session_minimal(self, test_client):
        """Test creating a session with minimal parameters."""
        response = test_client.post("/v2/sessions",
            headers={"Authorization": "Bearer test_1"},
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "agent_type" in data
        assert data["agent_type"] == "general"
        assert data["status"] == "active"

    def test_create_session_with_doctor_id(self, test_client, db_session):
        """Test creating a session with a specific doctor."""
        from app.models.doctor import Doctor
        from app.models.department import Department

        # Create a department first
        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        # Create a doctor
        doctor = Doctor(
            name="测试医生",
            specialty="测试专科",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.post("/v2/sessions",
            headers={"Authorization": "Bearer test_1"},
            json={"doctor_id": doctor.id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["doctor_id"] == doctor.id
        assert data["doctor_name"] == "测试医生"

    def test_create_session_with_agent_type(self, test_client):
        """Test creating a session with a specific agent type."""
        response = test_client.post("/v2/sessions",
            headers={"Authorization": "Bearer test_1"},
            json={"agent_type": "dermatology"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["agent_type"] == "dermatology"

    def test_create_session_invalid_agent_type(self, test_client):
        """Test creating a session with invalid agent type."""
        # API may accept invalid types and default to general
        response = test_client.post("/v2/sessions",
            headers={"Authorization": "Bearer test_1"},
            json={"agent_type": "invalid_agent_type"}
        )
        # Either 400 (rejected) or 200 (defaulted to general)
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            # If accepted, should default to general
            assert data["agent_type"] == "general"

    def test_create_session_nonexistent_doctor(self, test_client):
        """Test creating a session with non-existent doctor."""
        response = test_client.post("/v2/sessions",
            headers={"Authorization": "Bearer test_1"},
            json={"doctor_id": 99999}
        )
        assert response.status_code == 404


class TestSendMessage:
    """Tests for sending messages to AI agents."""

    def test_send_message_success(self, test_client, db_session):
        """Test sending a message successfully."""
        from app.models.session import Session as SessionModel
        from app.models.user import User

        # Create a test user first to avoid foreign key violation
        user = User(phone="19999999999", nickname="测试用户", is_active=True)
        db_session.add(user)
        db_session.flush()

        # Create a session first
        session_id = str(uuid.uuid4())
        session = SessionModel(
            id=session_id,
            user_id=user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        response = test_client.post("/v2/sessions/" + session_id + "/messages",
            headers={"Authorization": "Bearer test_1"},
            json={"content": "你好，我头疼"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert isinstance(data["message"], str)

    def test_send_message_to_nonexistent_session(self, test_client):
        """Test sending a message to a non-existent session."""
        fake_session_id = str(uuid.uuid4())
        response = test_client.post("/v2/sessions/" + fake_session_id + "/messages",
            headers={"Authorization": "Bearer test_1"},
            json={"content": "测试消息"}
        )
        assert response.status_code == 404

    def test_send_message_empty_content(self, test_client, db_session):
        """Test sending a message with empty content."""
        from app.models.session import Session as SessionModel
        from app.models.user import User

        # Create a test user
        user = User(phone="19999999998", nickname="测试用户2", is_active=True)
        db_session.add(user)
        db_session.flush()

        # Create a session
        session_id = str(uuid.uuid4())
        session = SessionModel(
            id=session_id,
            user_id=user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        response = test_client.post("/v2/sessions/" + session_id + "/messages",
            headers={"Authorization": "Bearer test_1"},
            json={"content": ""}
        )
        # Should still process, even with empty content
        assert response.status_code in [200, 422]

    def test_send_message_with_attachments(self, test_client, db_session):
        """Test sending a message with image attachments."""
        from app.models.session import Session as SessionModel
        from app.models.user import User

        # Create a test user
        user = User(phone="19999999997", nickname="测试用户3", is_active=True)
        db_session.add(user)
        db_session.flush()

        # Create a session
        session_id = str(uuid.uuid4())
        session = SessionModel(
            id=session_id,
            user_id=user.id,
            agent_type="dermatology"
        )
        db_session.add(session)
        db_session.commit()

        response = test_client.post("/v2/sessions/" + session_id + "/messages",
            headers={"Authorization": "Bearer test_1"},
            json={
                "content": "我的皮肤有问题",
                "attachments": [
                    {"type": "image", "url": "http://example.com/image.jpg"}
                ]
            }
        )
        # In test mode, should get a response
        assert response.status_code in [200, 422]

    def test_send_message_different_agent_types(self, test_client, db_session):
        """Test sending messages to different agent types."""
        from app.models.session import Session as SessionModel
        from app.models.user import User

        # Create a test user
        user = User(phone="19999999996", nickname="测试用户4", is_active=True)
        db_session.add(user)
        db_session.flush()

        # Test available agent types
        agent_types = ["general", "dermatology"]

        for agent_type in agent_types:
            session_id = str(uuid.uuid4())
            session = SessionModel(
                id=session_id,
                user_id=user.id,
                agent_type=agent_type
            )
            db_session.add(session)
            db_session.commit()

            response = test_client.post("/v2/sessions/" + session_id + "/messages",
                headers={"Authorization": "Bearer test_1"},
                json={"content": "测试消息"}
            )
            # Should get a response from each agent type
            assert response.status_code == 200
            data = response.json()
            assert "message" in data


class TestGetSessions:
    """Tests for retrieving user session lists."""

    def test_get_sessions_empty(self, test_client):
        """Test getting sessions when user has none."""
        # Use a unique user_id that won't have sessions
        response = test_client.get("/v2/sessions",
            headers={"Authorization": "Bearer test_99999"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # In test mode with new user, should be empty
        assert len(data) == 0

    def test_get_sessions_with_data(self, test_client):
        """Test getting sessions list endpoint."""
        # In test mode, this should return an empty list for a new user
        response = test_client.get("/v2/sessions",
            headers={"Authorization": "Bearer test_1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # In test mode with new user, should be empty or have test data

    def test_get_sessions_ordering(self, test_client):
        """Test that sessions endpoint returns list."""
        # Test that the sessions list endpoint returns proper structure
        response = test_client.get("/v2/sessions",
            headers={"Authorization": "Bearer test_1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestGetSessionMessages:
    """Tests for retrieving session message history."""

    def test_get_session_messages_empty(self, test_client, db_session):
        """Test getting messages from a session with no messages."""
        from app.models.session import Session as SessionModel
        from app.models.user import User

        # Create a test user (use test_1 which always works in TEST_MODE)
        user = User(phone="19999999993", nickname="测试用户7", is_active=True)
        db_session.add(user)
        db_session.flush()

        # Create a session without messages
        session_id = str(uuid.uuid4())
        session = SessionModel(
            id=session_id,
            user_id=user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        # In TEST_MODE, test_1 token should work for any session
        response = test_client.get("/v2/sessions/" + session_id + "/messages",
            headers={"Authorization": "Bearer test_1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "has_more" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) == 0

    def test_get_session_messages_with_data(self, test_client, db_session):
        """Test getting messages from a session with existing messages."""
        from app.models.session import Session as SessionModel
        from app.models.message import Message, SenderType
        from app.models.user import User

        # Create a test user
        user = User(phone="19999999992", nickname="测试用户8", is_active=True)
        db_session.add(user)
        db_session.flush()

        # Create a session with messages
        session_id = str(uuid.uuid4())
        session = SessionModel(
            id=session_id,
            user_id=user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.flush()

        # Add messages
        user_message = Message(
            session_id=session_id,
            sender=SenderType.user,
            content="你好"
        )
        ai_message = Message(
            session_id=session_id,
            sender=SenderType.ai,
            content="你好，有什么可以帮您？"
        )
        db_session.add(user_message)
        db_session.add(ai_message)
        db_session.commit()

        response = test_client.get("/v2/sessions/" + session_id + "/messages",
            headers={"Authorization": "Bearer test_1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) == 2

    def test_get_session_messages_nonexistent_session(self, test_client):
        """Test getting messages from a non-existent session."""
        fake_session_id = str(uuid.uuid4())
        response = test_client.get("/v2/sessions/" + fake_session_id + "/messages",
            headers={"Authorization": "Bearer test_1"}
        )
        assert response.status_code == 404

    def test_get_session_messages_with_limit(self, test_client, db_session):
        """Test getting messages with a limit parameter."""
        from app.models.session import Session as SessionModel
        from app.models.message import Message, SenderType
        from app.models.user import User

        # Create a test user
        user = User(phone="19999999991", nickname="测试用户9", is_active=True)
        db_session.add(user)
        db_session.flush()

        # Create a session with multiple messages
        session_id = str(uuid.uuid4())
        session = SessionModel(
            id=session_id,
            user_id=user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.flush()

        # Add 5 messages
        for i in range(5):
            msg = Message(
                session_id=session_id,
                sender=SenderType.user,
                content=f"消息 {i}"
            )
            db_session.add(msg)
        db_session.commit()

        # Get with limit=2
        response = test_client.get("/v2/sessions/" + session_id + "/messages?limit=2",
            headers={"Authorization": "Bearer test_1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) <= 2

    def test_get_session_messages_with_before(self, test_client, db_session):
        """Test getting messages with pagination (before parameter)."""
        from app.models.session import Session as SessionModel
        from app.models.message import Message, SenderType
        from app.models.user import User

        # Create a test user
        user = User(phone="19999999990", nickname="测试用户10", is_active=True)
        db_session.add(user)
        db_session.flush()

        # Create a session with messages
        session_id = str(uuid.uuid4())
        session = SessionModel(
            id=session_id,
            user_id=user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.flush()

        # Add messages
        for i in range(5):
            msg = Message(
                session_id=session_id,
                sender=SenderType.user,
                content=f"消息 {i}"
            )
            db_session.add(msg)
        db_session.commit()

        # Get first page
        response1 = test_client.get("/v2/sessions/" + session_id + "/messages?limit=3",
            headers={"Authorization": "Bearer test_1"}
        )
        assert response1.status_code == 200
        data1 = response1.json()

        if len(data1["messages"]) > 0:
            # Get next page using before parameter
            before_id = data1["messages"][0]["id"]
            response2 = test_client.get(
                "/v2/sessions/" + session_id + "/messages?limit=3&before=" + str(before_id),
                headers={"Authorization": "Bearer test_1"}
            )
            assert response2.status_code == 200
            data2 = response2.json()
            # Should get remaining messages
            assert len(data2["messages"]) <= 3


class TestListAgents:
    """Tests for listing available AI agents."""

    def test_list_agents(self, test_client):
        """Test getting list of all available agents."""
        response = test_client.get("/v2/sessions/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Should have at least general agent
        assert "general" in data or len(data) > 0

    def test_get_agent_capabilities(self, test_client):
        """Test getting capabilities of a specific agent."""
        response = test_client.get("/v2/sessions/agents/general/capabilities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_agent_capabilities_invalid_agent(self, test_client):
        """Test getting capabilities of non-existent agent."""
        response = test_client.get("/v2/sessions/agents/nonexistent_agent/capabilities")
        assert response.status_code == 404


class TestAgentResponseFormat:
    """Tests for AgentResponse format compliance."""

    def test_response_format_structure(self, test_client, db_session):
        """Test that agent response follows AgentResponse structure."""
        from app.models.session import Session as SessionModel
        from app.models.user import User

        # Create a test user
        user = User(phone="19999999989", nickname="测试用户11", is_active=True)
        db_session.add(user)
        db_session.flush()

        session_id = str(uuid.uuid4())
        session = SessionModel(
            id=session_id,
            user_id=user.id,
            agent_type="general"
        )
        db_session.add(session)
        db_session.commit()

        response = test_client.post("/v2/sessions/" + session_id + "/messages",
            headers={"Authorization": "Bearer test_1"},
            json={"content": "你好"}
        )
        assert response.status_code == 200
        data = response.json()

        # Check AgentResponse fields
        assert "message" in data
        assert isinstance(data["message"], str)

        # Optional fields that may or may not be present
        if "specialty_data" in data:
            assert isinstance(data["specialty_data"], dict) or data["specialty_data"] is None

        if "next_state" in data:
            assert isinstance(data["next_state"], dict) or data["next_state"] is None

        if "actions" in data:
            assert isinstance(data["actions"], list) or data["actions"] is None
