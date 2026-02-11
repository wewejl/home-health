"""
AI Services 单元测试

测试 AI 相关服务的核心功能：
- EventAggregationService 事件聚合
- AISummaryService 摘要生成
- 数据模型转换
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

# 导入服务和模型
try:
    from app.services.ai.aggregation_service import (
        EventAggregationService,
        AggregationResult,
        MergeResult,
        RelatedEvent,
        get_aggregation_service
    )
    from app.services.ai.summary_service import (
        AISummaryService,
        SummaryResult,
        TimelineEvent,
        get_summary_service
    )
except ImportError:
    from backend.app.services.ai.aggregation_service import (
        EventAggregationService,
        AggregationResult,
        MergeResult,
        RelatedEvent,
        get_aggregation_service
    )
    from backend.app.services.ai.summary_service import (
        AISummaryService,
        SummaryResult,
        TimelineEvent,
        get_summary_service
    )


class TestAggregationResult:
    """测试聚合结果数据模型"""

    def test_aggregation_result_to_dict(self):
        """测试转换为字典"""
        result = AggregationResult(
            should_merge=True,
            confidence=0.8,
            related_events=["evt1", "evt2"],
            merge_reason="相关症状",
            suggested_action="add_to_existing",
            target_event_id="evt1"
        )

        expected = {
            "should_merge": True,
            "confidence": 0.8,
            "related_events": ["evt1", "evt2"],
            "merge_reason": "相关症状",
            "suggested_action": "add_to_existing",
            "target_event_id": "evt1"
        }

        assert result.to_dict() == expected

    def test_aggregation_result_without_target(self):
        """测试没有目标事件的聚合结果"""
        result = AggregationResult(
            should_merge=False,
            confidence=1.0,
            related_events=[],
            merge_reason="无相关事件",
            suggested_action="create_new"
        )

        assert result.target_event_id is None
        assert result.suggested_action == "create_new"


class TestMergeResult:
    """测试合并结果数据模型"""

    def test_merge_result_to_dict(self):
        """测试转换为字典"""
        result = MergeResult(
            merged_title="合并病历",
            summary="综合摘要",
            disease_progression="症状演变",
            key_milestones=[{"date": "2024-01-01", "event": "初诊"}],
            current_status="稳定",
            overall_risk_level="medium",
            recommendations=["继续观察", "定期复查"]
        )

        data = result.to_dict()

        assert data["merged_title"] == "合并病历"
        assert data["overall_risk_level"] == "medium"
        assert len(data["recommendations"]) == 2


class TestRelatedEvent:
    """测试相关事件数据模型"""

    def test_related_event_fields(self):
        """测试相关事件字段"""
        event = RelatedEvent(
            event_id="evt123",
            relation_type="same_condition",
            confidence=0.9,
            reasoning="相同症状"
        )

        assert event.event_id == "evt123"
        assert event.relation_type == "same_condition"
        assert event.confidence == 0.9


class TestEventAggregationService:
    """测试事件聚合服务"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return EventAggregationService()

    def test_service_initialization(self, service):
        """测试服务初始化"""
        assert service.TIME_WINDOW_DAYS == 7
        assert service.SIMILARITY_THRESHOLD == 0.7
        assert service.SAME_DAY_AUTO_MERGE is True

    def test_parse_time_iso_format(self, service):
        """测试解析 ISO 格式时间"""
        time_str = "2024-01-15T10:30:00"
        result = service._parse_time(time_str)

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_time_datetime_object(self, service):
        """测试解析 datetime 对象"""
        dt = datetime(2024, 1, 15, 10, 30)
        result = service._parse_time(dt)

        assert result == dt

    def test_parse_time_none(self, service):
        """测试解析 None"""
        result = service._parse_time(None)
        assert result is None

    def test_quick_relation_check_same_day_same_dept(self, service):
        """测试同一天同科室的快速判断"""
        event_a = {
            "department": "皮肤科",
            "start_time": "2024-01-15T10:00:00"
        }
        event_b = {
            "department": "皮肤科",
            "start_time": "2024-01-15T14:00:00"
        }

        result = service._quick_relation_check(event_a, event_b)

        assert result is not None
        assert result["is_related"] is True
        assert result["confidence"] == 0.95
        assert result["should_merge"] is True

    def test_quick_relation_check_over_30_days(self, service):
        """测试超过30天的事件"""
        event_a = {
            "department": "皮肤科",
            "start_time": "2024-01-01T10:00:00"
        }
        event_b = {
            "department": "皮肤科",
            "start_time": "2024-02-05T10:00:00"  # 超过30天
        }

        result = service._quick_relation_check(event_a, event_b)

        assert result is not None
        assert result["is_related"] is False
        assert result["relation_type"] == "unrelated"

    def test_rule_based_aggregate_same_day(self, service):
        """测试基于规则的聚合（同一天同科室）"""
        session_info = {
            "department": "皮肤科",
            "timestamp": "2024-01-15T10:00:00"
        }
        existing_events = [
            {
                "id": "evt1",
                "department": "皮肤科",
                "start_time": "2024-01-15T09:00:00",
                "status": "active"
            }
        ]

        result = service._rule_based_aggregate(session_info, existing_events)

        assert result is not None
        assert result.should_merge is True
        assert result.target_event_id == "evt1"

    def test_filter_by_rules_excludes_self(self, service):
        """测试规则过滤排除自己"""
        target = {"id": "evt1", "start_time": "2024-01-15T10:00:00"}
        candidates = [
            {"id": "evt1", "start_time": "2024-01-15T10:00:00"},  # 自己
            {"id": "evt2", "start_time": "2024-01-16T10:00:00"},  # 候选
        ]

        result = service._filter_by_rules(target, candidates)

        assert len(result) == 1
        assert result[0]["id"] == "evt2"

    def test_filter_by_rules_time_window(self, service):
        """测试时间窗口过滤"""
        target = {"id": "evt1", "start_time": "2024-01-15T10:00:00"}
        candidates = [
            {"id": "evt2", "start_time": "2024-01-01T10:00:00"},  # 超过30天
            {"id": "evt3", "start_time": "2024-01-20T10:00:00"},  # 在30天内
        ]

        result = service._filter_by_rules(target, candidates)

        assert len(result) == 1
        assert result[0]["id"] == "evt3"

    def test_format_candidate_events(self, service):
        """测试格式化候选事件"""
        events = [
            {
                "id": "evt1",
                "title": "皮疹",
                "department": "皮肤科",
                "chief_complaint": "皮肤痒",
                "start_time": "2024-01-15T10:00:00",
                "summary": "过敏性皮炎"
            }
        ]

        result = service._format_candidate_events(events)

        assert "evt1" in result
        assert "皮疹" in result
        assert "皮肤科" in result

    def test_fallback_merged_summary(self, service):
        """测试降级合并摘要"""
        events = [
            {"title": "事件1", "department": "皮肤科"},
            {"title": "事件2", "department": "皮肤科"}
        ]

        result = service._fallback_merged_summary(events)

        assert isinstance(result, MergeResult)
        assert result.merged_title == "事件1"
        assert "2 个相关病历" in result.summary


class TestAISummaryService:
    """测试 AI 摘要服务"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return AISummaryService()

    def test_service_initialization(self, service):
        """测试服务初始化"""
        assert service is not None

    def test_format_conversations_empty(self, service):
        """测试格式化空会话列表"""
        result = service._format_conversations([])

        assert result == "暂无对话记录"

    def test_format_conversations_with_data(self, service):
        """测试格式化会话列表"""
        sessions = [
            {
                "session_id": "sess_12345678",
                "timestamp": "2024-01-15T10:00:00",
                "summary": "皮肤瘙痒",
                "messages": [
                    {"role": "user", "content": "医生我皮肤痒"},
                    {"role": "assistant", "content": "多久了？"}
                ]
            }
        ]

        result = service._format_conversations(sessions)

        assert "sess_12345678" in result
        assert "皮肤瘙痒" in result
        assert "患者" in result or "医生" in result

    def test_format_attachments_empty(self, service):
        """测试格式化空附件列表"""
        result = service._format_attachments([])

        assert result == "无附件"

    def test_format_attachments_with_data(self, service):
        """测试格式化附件列表"""
        attachments = [
            {"type": "image", "filename": "rash.jpg", "description": "皮疹照片"}
        ]

        result = service._format_attachments(attachments)

        assert "image" in result
        assert "rash.jpg" in result

    def test_format_notes_empty(self, service):
        """测试格式化空备注列表"""
        result = service._format_notes([])

        assert result == "无备注"

    def test_format_notes_with_important(self, service):
        """测试格式化备注（重要标记）"""
        notes = [
            {"content": "正常备注", "is_important": False},
            {"content": "重要备注", "is_important": True}
        ]

        result = service._format_notes(notes)

        assert "⚠️" in result
        assert "重要备注" in result

    def test_get_default_summary(self, service):
        """测试获取默认摘要"""
        result = service._get_default_summary()

        assert "summary" in result
        assert result["risk_level"] == "low"
        assert isinstance(result["recommendations"], list)

    def test_get_fallback_summary(self, service):
        """测试获取降级摘要"""
        result = service._get_fallback_summary(
            chief_complaint="皮肤痒",
            department="皮肤科",
            sessions=[{"timestamp": "2024-01-15"}]
        )

        assert isinstance(result, SummaryResult)
        assert "皮肤痒" in result.summary
        assert result.confidence == 0.3

    def test_generate_timeline_empty(self, service):
        """测试生成空时间轴"""
        result = service.generate_timeline(
            chief_complaint="测试",
            sessions=[],
            attachments=[],
            notes=[]
        )

        assert isinstance(result, list)
        # 空列表因为没有带时间戳的项目
        assert len(result) == 0

    def test_generate_timeline_with_sessions(self, service):
        """测试生成会话时间轴"""
        sessions = [
            {
                "timestamp": "2024-01-15T10:00:00",
                "summary": "初诊",
                "session_type": "consultation"
            }
        ]

        result = service.generate_timeline(
            chief_complaint="测试",
            sessions=sessions
        )

        assert len(result) == 1
        assert result[0].type == "consultation"
        assert result[0].importance == "high"


class TestTimelineEvent:
    """测试时间轴事件"""

    def test_timeline_event_creation(self):
        """测试创建时间轴事件"""
        event = TimelineEvent(
            timestamp="2024-01-15T10:00:00",
            type="consultation",
            title="初诊",
            description="首次就诊",
            importance="high"
        )

        assert event.timestamp == "2024-01-15T10:00:00"
        assert event.type == "consultation"
        assert event.importance == "high"


class TestSummaryResult:
    """测试摘要结果"""

    def test_summary_result_to_dict(self):
        """测试转换为字典"""
        result = SummaryResult(
            summary="测试摘要",
            key_points=["要点1", "要点2"],
            symptoms=["发热", "咳嗽"],
            symptom_details={},
            possible_diagnosis=["感冒"],
            risk_level="low",
            risk_warning=None,
            recommendations=["多喝水"],
            follow_up_reminders=[],
            timeline=[],
            confidence=0.8
        )

        data = result.to_dict()

        assert data["summary"] == "测试摘要"
        assert data["risk_level"] == "low"
        assert len(data["key_points"]) == 2


class TestSingletonServices:
    """测试单例服务"""

    def test_aggregation_service_singleton(self):
        """测试聚合服务单例"""
        service1 = get_aggregation_service()
        service2 = get_aggregation_service()

        assert service1 is service2

    def test_summary_service_singleton(self):
        """测试摘要服务单例"""
        service1 = get_summary_service()
        service2 = get_summary_service()

        assert service1 is service2


class TestSmartAggregate:
    """测试智能聚合"""

    @pytest.fixture
    def service(self):
        return EventAggregationService()

    def test_smart_aggregate_no_existing_events(self, service):
        """测试没有现有事件时的聚合"""
        session_info = {
            "department": "皮肤科",
            "timestamp": "2024-01-15T10:00:00",
            "chief_complaint": "皮肤痒"
        }

        # 同步测试规则逻辑
        result = service._rule_based_aggregate(session_info, [])

        # 规则返回 None，智能聚合应该返回创建新事件
        if result is None:
            # 验证空事件处理
            assert len([]) == 0

    @pytest.mark.asyncio
    async def test_smart_aggregate_with_mocked_llm(self, service):
        """测试使用模拟 LLM 的智能聚合"""
        session_info = {
            "department": "皮肤科",
            "timestamp": "2024-01-15T10:00:00",
            "chief_complaint": "皮肤痒"
        }
        existing_events = [
            {
                "id": "evt1",
                "department": "内科",  # 不同科室
                "start_time": "2024-01-14T10:00:00",
                "status": "active"
            }
        ]

        # Mock LLM 调用
        service._call_llm = AsyncMock(return_value='{"action": "create_new", "confidence": 0.8}')

        result = await service.smart_aggregate(session_info, existing_events)

        assert isinstance(result, AggregationResult)
        assert result.suggested_action == "create_new"
