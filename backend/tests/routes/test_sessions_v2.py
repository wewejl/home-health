"""
V2 Sessions API 单元测试

测试新增的 V2 端点：
- GET /v2/sessions - 获取会话列表
- GET /v2/sessions/{id}/messages - 获取消息列表
- migrate_v1_state_to_v2() - 状态转换函数
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.routes.sessions_v2 import migrate_v1_state_to_v2, router
from app.schemas.session import SessionResponse
from app.schemas.message import MessageListResponse
from app.models.session import Session as SessionModel
from app.models.message import Message, SenderType
from app.models.user import User


class TestMigrateV1StateToV2:
    """测试 V1 到 V2 状态转换函数"""

    def test_empty_state_returns_empty_dict(self):
        """测试：空状态应返回空字典"""
        result = migrate_v1_state_to_v2(None)
        assert result == {}

    def test_json_string_state_parsing(self):
        """测试：JSON 字符串状态应正确解析"""
        import json
        v1_state_str = '{"stage": "collecting", "chief_complaint": "头痛", "symptoms": ["发热"]}'
        result = migrate_v1_state_to_v2(v1_state_str)
        assert result["stage"] == "collecting"
        assert result["chief_complaint"] == "头痛"
        assert result["symptoms"] == ["发热"]

    def test_invalid_json_string_returns_empty(self):
        """测试：无效 JSON 字符串应返回空字典"""
        result = migrate_v1_state_to_v2("invalid json")
        assert result == {}

    def test_v1_state_filters_unwanted_fields(self):
        """测试：V1 状态中的不需要字段应被过滤"""
        v1_state = {
            "questions_asked": 3,
            "session_id": "test-123",
            "user_id": 1,
            "stage": "collecting",
            "chief_complaint": "头痛",
            "symptoms": ["发热"],
            "unwanted_field": "should_be_removed"
        }
        result = migrate_v1_state_to_v2(v1_state)

        # V2 不需要的字段应被过滤
        assert "questions_asked" not in result
        assert "session_id" not in result
        assert "user_id" not in result
        assert "unwanted_field" not in result

        # V2 需要的字段应保留
        assert result["stage"] == "collecting"
        assert result["chief_complaint"] == "头痛"
        assert result["symptoms"] == ["发热"]

    def test_preserves_diagnosis_card(self):
        """测试：诊断卡应被保留"""
        v1_state = {
            "stage": "completed",
            "diagnosis_card": {
                "summary": "疑似感冒",
                "conditions": ["感冒"],
                "risk_level": "low"
            },
            "advice_history": []
        }
        result = migrate_v1_state_to_v2(v1_state)
        assert "diagnosis_card" in result
        assert result["diagnosis_card"]["summary"] == "疑似感冒"

    def test_preserves_advice_history(self):
        """测试：建议历史应被保留"""
        v1_state = {
            "stage": "analyzing",
            "advice_history": [
                {"id": "1", "title": "建议1", "content": "内容1"}
            ]
        }
        result = migrate_v1_state_to_v2(v1_state)
        assert "advice_history" in result
        assert len(result["advice_history"]) == 1

    def test_preserves_knowledge_refs(self):
        """测试：知识引用应被保留"""
        v1_state = {
            "stage": "diagnosing",
            "knowledge_refs": [
                {"id": "ref1", "title": "参考1"}
            ]
        }
        result = migrate_v1_state_to_v2(v1_state)
        assert "knowledge_refs" in result
        assert len(result["knowledge_refs"]) == 1

    def test_preserves_reasoning_steps(self):
        """测试：推理步骤应被保留"""
        v1_state = {
            "stage": "analyzing",
            "reasoning_steps": ["步骤1", "步骤2"]
        }
        result = migrate_v1_state_to_v2(v1_state)
        assert "reasoning_steps" in result
        assert result["reasoning_steps"] == ["步骤1", "步骤2"]

    def test_preserves_latest_analysis(self):
        """测试：最新分析应被保留"""
        v1_state = {
            "latest_analysis": {"result": "分析结果"}
        }
        result = migrate_v1_state_to_v2(v1_state)
        assert "latest_analysis" in result
        assert result["latest_analysis"]["result"] == "分析结果"

    def test_preserves_current_response(self):
        """测试：当前响应应被保留"""
        v1_state = {
            "current_response": "这是回复内容"
        }
        result = migrate_v1_state_to_v2(v1_state)
        assert "current_response" in result
        assert result["current_response"] == "这是回复内容"


class TestGetSessionsV2:
    """测试 GET /v2/sessions 端点"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock()
        return db

    @pytest.fixture
    def mock_current_user(self):
        """模拟当前用户"""
        user = User(id=1, phone="13800138000")
        return user

    @pytest.fixture
    def mock_sessions(self):
        """模拟会话数据"""
        now = datetime.utcnow()
        # 创建带有正确属性类型的 mock 对象
        sess1 = Mock()
        sess1.id = "session-1"
        sess1.user_id = 1
        sess1.doctor_id = 1
        sess1.agent_type = "general"
        sess1.agent_state = {}
        sess1.last_message = "测试消息"
        sess1.status = "active"
        sess1.created_at = now - timedelta(hours=2)
        sess1.updated_at = now - timedelta(hours=1)

        sess2 = Mock()
        sess2.id = "session-2"
        sess2.user_id = 1
        sess2.doctor_id = None
        sess2.agent_type = "dermatology"
        sess2.agent_state = {}
        sess2.last_message = "皮肤问题"
        sess2.status = "active"
        sess2.created_at = now - timedelta(days=1)
        sess2.updated_at = now - timedelta(hours=3)

        return [sess1, sess2]

    @pytest.fixture
    def mock_doctors(self):
        """模拟医生数据"""
        doc1 = Mock()
        doc1.id = 1
        doc1.name = "张医生"

        doc2 = Mock()
        doc2.id = 2
        doc2.name = "李医生"

        return [doc1, doc2]

    def test_get_sessions_v2_empty_list(self, mock_db, mock_current_user):
        """测试：空会话列表应返回空数组"""
        # 创建正确的 mock 链
        mock_query_result = Mock()
        mock_query_result.order_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value = mock_query_result

        from app.routes.sessions_v2 import get_sessions_v2
        result = get_sessions_v2(db=mock_db, current_user=mock_current_user)

        assert result == []

    def test_get_sessions_v2_with_sessions(self, mock_db, mock_current_user, mock_sessions, mock_doctors):
        """测试：返回会话列表"""
        # 创建一个完整的 sessions query mock chain
        mock_filtered = Mock()
        mock_filtered.order_by.return_value.all.return_value = mock_sessions

        mock_sessions_query = Mock()
        mock_sessions_query.filter.return_value = mock_filtered

        # 创建 doctor query mock - 返回一个医生
        mock_doctor_filtered = Mock()
        mock_doctor_filtered.first.return_value = mock_doctors[0]

        mock_doctor_query = Mock()
        mock_doctor_query.filter.return_value = mock_doctor_filtered

        # 根据 query 参数类型返回不同的 mock
        # SessionModel 在 routes/sessions_v2.py 中是 Session 的别名
        from app.models.session import Session as ActualSessionModel
        from app.models.doctor import Doctor as ActualDoctorModel

        def query_side_effect(model):
            # SessionModel 查询（注意：类名是 "Session"）
            if model.__name__ == 'Session':
                return mock_sessions_query
            # Doctor 查询
            else:
                return mock_doctor_query

        mock_db.query.side_effect = query_side_effect

        from app.routes.sessions_v2 import get_sessions_v2
        result = get_sessions_v2(db=mock_db, current_user=mock_current_user)

        assert len(result) == 2
        assert result[0].session_id == "session-1"
        assert result[0].agent_type == "general"
        assert result[1].session_id == "session-2"
        assert result[1].agent_type == "dermatology"

    def test_get_sessions_v2_response_format(self, mock_db, mock_current_user, mock_sessions, mock_doctors):
        """测试：响应格式正确"""
        # 创建一个完整的 sessions query mock chain
        mock_filtered = Mock()
        mock_filtered.order_by.return_value.all.return_value = mock_sessions

        mock_sessions_query = Mock()
        mock_sessions_query.filter.return_value = mock_filtered

        # 创建 doctor query mock
        mock_doctor_filtered = Mock()
        mock_doctor_filtered.first.return_value = mock_doctors[0]

        mock_doctor_query = Mock()
        mock_doctor_query.filter.return_value = mock_doctor_filtered

        # 根据 query 参数类型返回不同的 mock
        def query_side_effect(model):
            if model.__name__ == 'Session':
                return mock_sessions_query
            else:  # Doctor
                return mock_doctor_query

        mock_db.query.side_effect = query_side_effect

        from app.routes.sessions_v2 import get_sessions_v2
        result = get_sessions_v2(db=mock_db, current_user=mock_current_user)

        # 验证 SessionResponse 格式
        for session in result:
            assert hasattr(session, 'session_id')
            assert hasattr(session, 'agent_type')
            assert hasattr(session, 'created_at')
            assert hasattr(session, 'updated_at')


class TestGetSessionMessagesV2:
    """测试 GET /v2/sessions/{session_id}/messages 端点"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock()
        return db

    @pytest.fixture
    def mock_current_user(self):
        """模拟当前用户"""
        user = User(id=1, phone="13800138000")
        return user

    @pytest.fixture
    def mock_session(self):
        """模拟会话数据"""
        sess = Mock()
        sess.id = "session-1"
        sess.user_id = 1
        sess.agent_type = "general"
        sess.agent_state = {}
        sess.status = "active"
        return sess

    @pytest.fixture
    def mock_messages(self):
        """模拟消息数据"""
        now = datetime.utcnow()
        # 创建带有正确属性类型的 mock 对象
        msg1 = Mock()
        msg1.id = 1
        msg1.session_id = "session-1"
        msg1.sender = SenderType.user
        msg1.content = "用户消息"
        msg1.attachment_url = None
        msg1.message_type = "text"
        msg1.attachments = None
        msg1.structured_data = None
        msg1.created_at = now - timedelta(minutes=10)

        msg2 = Mock()
        msg2.id = 2
        msg2.session_id = "session-1"
        msg2.sender = SenderType.ai
        msg2.content = "AI 回复"
        msg2.attachment_url = None
        msg2.message_type = "text"
        msg2.attachments = None
        msg2.structured_data = None
        msg2.created_at = now - timedelta(minutes=5)

        return [msg1, msg2]

    def _setup_test_mode(self, test_mode_value):
        """辅助函数：设置 TEST_MODE"""
        import app.dependencies as deps_module
        original = deps_module.TEST_MODE
        deps_module.TEST_MODE = test_mode_value
        return original

    def _restore_test_mode(self, original_value):
        """辅助函数：恢复 TEST_MODE"""
        import app.dependencies as deps_module
        deps_module.TEST_MODE = original_value

    def test_get_messages_v2_session_not_found(self, mock_db, mock_current_user):
        """测试：会话不存在应返回 404"""
        # 创建 session query mock，返回 None（会话不存在）
        mock_session_filter1 = Mock()
        mock_session_filter1.first.return_value = None

        mock_session_query = Mock()
        mock_session_query.filter.return_value = mock_session_filter1

        # 当查询 SessionModel 时返回 session query mock
        mock_db.query.return_value = mock_session_query

        from app.routes.sessions_v2 import get_session_messages_v2, HTTPException

        original = self._setup_test_mode(False)
        try:
            with pytest.raises(HTTPException) as exc_info:
                get_session_messages_v2(
                    session_id="non-existent",
                    db=mock_db,
                    current_user=mock_current_user
                )
            assert exc_info.value.status_code == 404
        finally:
            self._restore_test_mode(original)

    def test_get_messages_v2_with_messages(self, mock_db, mock_current_user, mock_session, mock_messages):
        """测试：返回消息列表"""
        # 创建 session query mock
        mock_session_filtered = Mock()
        mock_session_filtered.filter.return_value.first.return_value = mock_session

        mock_session_query = Mock()
        mock_session_query.filter.return_value = mock_session_filtered

        # 创建 messages query mock
        mock_messages_ordered = Mock()
        mock_messages_ordered.limit.return_value.all.return_value = mock_messages

        mock_messages_filtered = Mock()
        mock_messages_filtered.order_by.return_value = mock_messages_ordered

        mock_messages_query = Mock()
        mock_messages_query.filter.return_value = mock_messages_filtered

        # 根据 query 参数类型返回不同的 mock
        def query_side_effect(model):
            if model.__name__ == 'Session':
                return mock_session_query
            else:  # Message
                return mock_messages_query

        mock_db.query.side_effect = query_side_effect

        from app.routes.sessions_v2 import get_session_messages_v2, MessageListResponse

        original = self._setup_test_mode(False)
        try:
            result = get_session_messages_v2(
                session_id="session-1",
                limit=20,
                before=None,
                db=mock_db,
                current_user=mock_current_user
            )

            assert isinstance(result, MessageListResponse)
            assert len(result.messages) == 2
            assert result.has_more == False  # 只有2条消息，不超过limit
        finally:
            self._restore_test_mode(original)

    def test_get_messages_v2_with_pagination(self, mock_db, mock_current_user, mock_session):
        """测试：分页功能"""
        # 创建 25 条消息，带有正确的属性类型
        messages = []
        for i in range(1, 26):
            msg = Mock()
            msg.id = i
            msg.session_id = "session-1"
            msg.sender = SenderType.user if i % 2 == 0 else SenderType.ai
            msg.content = f"消息{i}"
            msg.attachment_url = None
            msg.message_type = "text"
            msg.attachments = None
            msg.structured_data = None
            msg.created_at = datetime.utcnow()
            messages.append(msg)

        # 创建 session query mock
        mock_session_filtered = Mock()
        mock_session_filtered.filter.return_value.first.return_value = mock_session

        mock_session_query = Mock()
        mock_session_query.filter.return_value = mock_session_filtered

        # 创建 messages query mock
        mock_messages_ordered = Mock()
        mock_messages_ordered.limit.return_value.all.return_value = messages

        mock_messages_filtered = Mock()
        mock_messages_filtered.order_by.return_value = mock_messages_ordered

        mock_messages_query = Mock()
        mock_messages_query.filter.return_value = mock_messages_filtered

        # 根据 query 参数类型返回不同的 mock
        def query_side_effect(model):
            if model.__name__ == 'Session':
                return mock_session_query
            else:  # Message
                return mock_messages_query

        mock_db.query.side_effect = query_side_effect

        from app.routes.sessions_v2 import get_session_messages_v2

        original = self._setup_test_mode(False)
        try:
            # 请求 limit=20，有25条消息，应该返回20条，has_more=True
            result = get_session_messages_v2(
                session_id="session-1",
                limit=20,
                before=None,
                db=mock_db,
                current_user=mock_current_user
            )

            assert len(result.messages) == 20
            assert result.has_more == True
        finally:
            self._restore_test_mode(original)

    def test_get_messages_v2_with_before_parameter(self, mock_db, mock_current_user, mock_session):
        """测试：before 参数用于分页"""
        # 创建消息，id 1-9（这些会通过 before=10 过滤）
        messages = []
        for i in range(1, 10):
            msg = Mock()
            msg.id = i
            msg.session_id = "session-1"
            msg.sender = SenderType.user
            msg.content = f"消息{i}"
            msg.attachment_url = None
            msg.message_type = "text"
            msg.attachments = None
            msg.structured_data = None
            msg.created_at = datetime.utcnow()
            messages.append(msg)

        # 创建 session query mock
        mock_session_filtered = Mock()
        mock_session_filtered.filter.return_value.first.return_value = mock_session

        mock_session_query = Mock()
        mock_session_query.filter.return_value = mock_session_filtered

        # 创建 messages query mock
        mock_messages_ordered = Mock()
        mock_messages_ordered.limit.return_value.all.return_value = messages

        mock_messages_filtered2 = Mock()
        mock_messages_filtered2.order_by.return_value = mock_messages_ordered

        mock_messages_filtered = Mock()
        # 第一次 filter 用于 session_id，第二次用于 before（模拟过滤结果）
        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            return mock_messages_filtered2

        mock_messages_filtered.filter.side_effect = filter_side_effect

        mock_messages_query = Mock()
        mock_messages_query.filter.return_value = mock_messages_filtered

        # 根据 query 参数类型返回不同的 mock
        def query_side_effect(model):
            if model.__name__ == 'Session':
                return mock_session_query
            else:  # Message
                return mock_messages_query

        mock_db.query.side_effect = query_side_effect

        from app.routes.sessions_v2 import get_session_messages_v2

        original = self._setup_test_mode(False)
        try:
            # 使用 before=10，应该返回 id < 10 的消息
            result = get_session_messages_v2(
                session_id="session-1",
                limit=20,
                before=10,
                db=mock_db,
                current_user=mock_current_user
            )

            # should have messages with id < 10
            message_ids = [m.id for m in result.messages]
            assert all(id < 10 for id in message_ids)
        finally:
            self._restore_test_mode(original)


class TestStateCompatibility:
    """测试 V1/V2 状态兼容性"""

    def test_v1_empty_state_compatibility(self):
        """测试：V1 空 agent_state 兼容"""
        v1_state = None
        result = migrate_v1_state_to_v2(v1_state)
        assert result == {}

    def test_v1_minimal_state_compatibility(self):
        """测试：V1 最小状态兼容"""
        v1_state = {
            "stage": "greeting",
            "chief_complaint": ""
        }
        result = migrate_v1_state_to_v2(v1_state)
        assert result["stage"] == "greeting"
        assert result["chief_complaint"] == ""

    def test_v2_empty_state_still_works(self):
        """测试：V2 空状态仍然可以工作"""
        # V2 使用空状态作为初始状态
        v2_state = {}
        result = migrate_v1_state_to_v2(v2_state)
        assert result == {}

    def test_state_roundtrip(self):
        """测试：状态转换后保留所需字段"""
        original = {
            "stage": "analyzing",
            "chief_complaint": "头痛",
            "symptoms": ["发热", "咳嗽"],
            "skin_location": "头部",
            "diagnosis_card": None,
            "advice_history": [],
            "knowledge_refs": [],
            "reasoning_steps": [],
            "latest_analysis": None,
            "latest_interpretation": None,
            "current_response": None
        }
        result = migrate_v1_state_to_v2(original)

        # 验证所有字段都被保留
        for key in original.keys():
            if original[key] is not None:
                assert result[key] == original[key]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
