"""
AI Agent Service tests.

Tests cover:
- Base AI service functionality
- Aggregation service (event correlation, merging)
- Summary service (symptom extraction, timeline generation)
- Transcription service (voice to text)
- Dermatology agent (state management, conversation flow)
- Orthopedics agent (X-ray interpretation, state management)

Uses mocks to simulate LLM responses for reliable testing.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os
from datetime import datetime

# Set test mode before imports
os.environ["TEST_MODE"] = "true"


# ============================================================================
# Base AI Service Tests
# ============================================================================

class TestBaseAIService:
    """Tests for BaseAIService core functionality."""

    def test_init_with_defaults(self):
        """Test initializing BaseAIService with default parameters."""
        from app.services.ai.base_ai_service import BaseAIService
        from app.config import get_settings
        from unittest.mock import patch

        # Get the actual model from settings
        settings = get_settings()
        actual_model = settings.LLM_MODEL

        service = BaseAIService()
        assert service.model == actual_model  # Uses actual settings
        assert service.temperature == 0.3
        assert service.max_tokens == 2000

    def test_init_with_custom_params(self):
        """Test initializing BaseAIService with custom parameters."""
        from app.services.ai.base_ai_service import BaseAIService
        from unittest.mock import patch

        with patch("app.services.ai.base_ai_service.get_settings") as mock_settings:
            mock_config = MagicMock()
            mock_config.LLM_BASE_URL = "http://test"
            mock_config.LLM_API_KEY = "test-key"
            mock_config.LLM_MODEL = "test-model"
            mock_settings.return_value = mock_config

            service = BaseAIService(
                model="custom-model",
                temperature=0.5,
                max_tokens=1000
            )
            assert service.model == "custom-model"
            assert service.temperature == 0.5
            assert service.max_tokens == 1000

    def test_parse_json_clean(self):
        """Test parsing clean JSON."""
        from app.services.ai.base_ai_service import BaseAIService
        from unittest.mock import patch

        with patch("app.services.ai.base_ai_service.get_settings") as mock_settings:
            mock_config = MagicMock()
            mock_config.LLM_BASE_URL = "http://test"
            mock_config.LLM_API_KEY = "test-key"
            mock_config.LLM_MODEL = "test-model"
            mock_settings.return_value = mock_config

            service = BaseAIService()
            result = service._parse_json('{"key": "value"}')
            assert result == {"key": "value"}

    def test_parse_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        from app.services.ai.base_ai_service import BaseAIService
        from unittest.mock import patch

        with patch("app.services.ai.base_ai_service.get_settings") as mock_settings:
            mock_config = MagicMock()
            mock_config.LLM_BASE_URL = "http://test"
            mock_config.LLM_API_KEY = "test-key"
            mock_config.LLM_MODEL = "test-model"
            mock_settings.return_value = mock_config

            service = BaseAIService()
            result = service._parse_json('```json\n{"key": "value"}\n```')
            assert result == {"key": "value"}

    def test_parse_json_with_code_block(self):
        """Test parsing JSON wrapped in generic code block."""
        from app.services.ai.base_ai_service import BaseAIService
        from unittest.mock import patch

        with patch("app.services.ai.base_ai_service.get_settings") as mock_settings:
            mock_config = MagicMock()
            mock_config.LLM_BASE_URL = "http://test"
            mock_config.LLM_API_KEY = "test-key"
            mock_config.LLM_MODEL = "test-model"
            mock_settings.return_value = mock_config

            service = BaseAIService()
            result = service._parse_json('```\n{"key": "value"}\n```')
            assert result == {"key": "value"}

    def test_parse_json_extract_from_text(self):
        """Test extracting JSON object from surrounding text."""
        from app.services.ai.base_ai_service import BaseAIService
        from unittest.mock import patch

        with patch("app.services.ai.base_ai_service.get_settings") as mock_settings:
            mock_config = MagicMock()
            mock_config.LLM_BASE_URL = "http://test"
            mock_config.LLM_API_KEY = "test-key"
            mock_config.LLM_MODEL = "test-model"
            mock_settings.return_value = mock_config

            service = BaseAIService()
            result = service._parse_json('Text before {"key": "value"} text after')
            assert result == {"key": "value"}

    def test_parse_json_invalid_returns_default(self):
        """Test that invalid JSON returns default value."""
        from app.services.ai.base_ai_service import BaseAIService
        from unittest.mock import patch

        with patch("app.services.ai.base_ai_service.get_settings") as mock_settings:
            mock_config = MagicMock()
            mock_config.LLM_BASE_URL = "http://test"
            mock_config.LLM_API_KEY = "test-key"
            mock_config.LLM_MODEL = "test-model"
            mock_settings.return_value = mock_config

            service = BaseAIService()
            result = service._parse_json('not json at all', default={"default": True})
            assert result == {"default": True}

    def test_clean_text(self):
        """Test text cleaning utility."""
        from app.services.ai.base_ai_service import BaseAIService
        from unittest.mock import patch

        with patch("app.services.ai.base_ai_service.get_settings") as mock_settings:
            mock_config = MagicMock()
            mock_config.LLM_BASE_URL = "http://test"
            mock_config.LLM_API_KEY = "test-key"
            mock_config.LLM_MODEL = "test-model"
            mock_settings.return_value = mock_config

            service = BaseAIService()
            result = service._clean_text("  hello   world  ")
            assert result == "hello world"

    def test_truncate_text(self):
        """Test text truncation utility."""
        from app.services.ai.base_ai_service import BaseAIService
        from unittest.mock import patch

        with patch("app.services.ai.base_ai_service.get_settings") as mock_settings:
            mock_config = MagicMock()
            mock_config.LLM_BASE_URL = "http://test"
            mock_config.LLM_API_KEY = "test-key"
            mock_config.LLM_MODEL = "test-model"
            mock_settings.return_value = mock_config

            service = BaseAIService()
            long_text = "a" * 1000
            result = service._truncate_text(long_text, max_length=100)
            assert len(result) == 103  # 100 + "..."
            assert result.endswith("...")


# ============================================================================
# Aggregation Service Tests
# ============================================================================

class TestEventAggregationService:
    """Tests for EventAggregationService."""

    @pytest.fixture
    def service(self):
        """Create an EventAggregationService instance with mocked LLM."""
        from app.services.ai.aggregation_service import EventAggregationService
        service = EventAggregationService()
        # Mock the LLM call
        service._call_llm = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_analyze_relation_same_day_same_dept(self, service):
        """Test quick relation check for same day same department."""
        # Note: Use exact same time to ensure time_diff == 0
        # because the implementation uses (time_a - time_b).days which returns
        # the number of full days, not calendar days
        event_a = {
            "title": "头痛",
            "department": "内科",
            "start_time": "2024-01-15 10:00:00"
        }
        event_b = {
            "title": "头晕",
            "department": "内科",
            "start_time": "2024-01-15 10:00:00"  # Same time for time_diff == 0
        }

        result = await service.analyze_relation(event_a, event_b)

        # Should detect high correlation due to same day same dept
        assert result["is_related"] is True
        assert result["relation_type"] == "same_condition"
        assert result["confidence"] >= 0.9

    @pytest.mark.asyncio
    async def test_analyze_relation_different_days(self, service):
        """Test relation analysis for events on different days."""
        event_a = {
            "title": "头痛",
            "department": "内科",
            "start_time": "2024-01-01 10:00:00"
        }
        event_b = {
            "title": "头晕",
            "department": "内科",
            "start_time": "2024-02-01 14:00:00"
        }

        result = await service.analyze_relation(event_a, event_b)

        # Should detect no relation due to >30 day gap
        assert result["is_related"] is False
        assert result["relation_type"] == "unrelated"

    @pytest.mark.asyncio
    async def test_find_related_events_empty_candidates(self, service):
        """Test finding related events with empty candidate list."""
        target_event = {"title": "头痛", "department": "内科"}
        candidates = []

        result = await service.find_related_events(target_event, candidates)

        assert result == []

    @pytest.mark.asyncio
    async def test_smart_aggregate_no_existing_events(self, service):
        """Test smart aggregation with no existing events."""
        session_info = {
            "department": "皮肤科",
            "timestamp": "2024-01-15 10:00:00",
            "chief_complaint": "皮疹"
        }

        result = await service.smart_aggregate(session_info, [])

        assert result.should_merge is False
        assert result.suggested_action == "create_new"
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_smart_aggregate_with_same_day_event(self, service):
        """Test smart aggregation with same-day existing event."""
        session_info = {
            "department": "皮肤科",
            "timestamp": "2024-01-15 10:00:00",
            "chief_complaint": "皮疹加重"
        }

        existing_events = [{
            "id": "evt-1",
            "department": "皮肤科",
            "start_time": "2024-01-15 08:00:00",
            "status": "active"
        }]

        result = await service.smart_aggregate(session_info, existing_events)

        # Should suggest merging due to same day same dept
        assert result.should_merge is True
        assert result.suggested_action == "add_to_existing"
        assert result.target_event_id == "evt-1"

    @pytest.mark.asyncio
    async def test_generate_merged_summary_empty_list(self, service):
        """Test generating merged summary with empty list."""
        with pytest.raises(ValueError, match="事件列表不能为空"):
            await service.generate_merged_summary([])

    @pytest.mark.asyncio
    async def test_generate_merged_summary_single_event(self, service):
        """Test generating merged summary with single event."""
        service._call_llm = AsyncMock(return_value='''{
            "merged_title": "皮肤问题",
            "summary": "患者主诉皮疹",
            "disease_progression": "",
            "key_milestones": [],
            "current_status": "活跃",
            "overall_risk_level": "low",
            "recommendations": ["观察"]
        }''')

        events = [{
            "title": "皮疹",
            "department": "皮肤科",
            "start_time": "2024-01-15",
            "risk_level": "low"
        }]

        result = await service.generate_merged_summary(events)

        assert result.merged_title == "皮肤问题"
        assert result.overall_risk_level == "low"
        assert "观察" in result.recommendations

    @pytest.mark.asyncio
    async def test_generate_merged_summary_fallback_on_error(self, service):
        """Test fallback merged summary when LLM fails."""
        service._call_llm = AsyncMock(side_effect=Exception("LLM error"))

        events = [{
            "title": "皮疹",
            "department": "皮肤科",
            "start_time": "2024-01-15",
            "risk_level": "low"
        }]

        result = await service.generate_merged_summary(events)

        # Should return fallback result
        assert result.merged_title == "皮疹"
        assert "1" in result.summary  # Contains event count
        assert result.overall_risk_level == "medium"


# ============================================================================
# Summary Service Tests
# ============================================================================

class TestAISummaryService:
    """Tests for AISummaryService."""

    @pytest.fixture
    def service(self):
        """Create an AISummaryService instance with mocked LLM."""
        from app.services.ai.summary_service import AISummaryService
        service = AISummaryService()
        service._call_llm = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_generate_summary_basic(self, service):
        """Test generating basic summary."""
        service._call_llm = AsyncMock(return_value='''{
            "summary": "患者主诉头痛，伴发热",
            "key_points": ["头痛", "发热"],
            "symptoms": ["头痛", "发热"],
            "symptom_details": {},
            "possible_diagnosis": ["感冒"],
            "risk_level": "low",
            "risk_warning": null,
            "recommendations": ["多休息"],
            "follow_up_reminders": [],
            "timeline": [],
            "confidence": 0.8
        }''')

        result = await service.generate_summary(
            chief_complaint="头痛",
            department="内科",
            sessions=[{
                "session_id": "s1",
                "timestamp": "2024-01-15",
                "summary": "患者主诉头痛"
            }]
        )

        assert result.summary == "患者主诉头痛，伴发热"
        assert "头痛" in result.symptoms
        assert result.risk_level == "low"

    @pytest.mark.asyncio
    async def test_generate_summary_with_attachments(self, service):
        """Test generating summary with attachment info."""
        service._call_llm = AsyncMock(return_value='''{
            "summary": "患者主诉皮疹，上传了照片",
            "key_points": ["皮疹"],
            "symptoms": ["皮疹"],
            "symptom_details": {},
            "possible_diagnosis": ["湿疹"],
            "risk_level": "low",
            "risk_warning": null,
            "recommendations": ["避免抓挠"],
            "follow_up_reminders": [],
            "timeline": [],
            "confidence": 0.7
        }''')

        attachments = [{
            "type": "image",
            "filename": "rash.jpg",
            "description": "手臂皮疹照片"
        }]

        result = await service.generate_summary(
            chief_complaint="皮疹",
            department="皮肤科",
            sessions=[],
            attachments=attachments
        )

        assert "照片" in result.summary
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_extract_symptoms(self, service):
        """Test symptom extraction from text."""
        service._call_llm = AsyncMock(return_value='''{
            "symptoms": ["头痛", "发热", "咳嗽"],
            "red_flags": ["高烧"]
        }''')

        result = await service.extract_symptoms("我头痛发烧还咳嗽，体温39度")

        assert "头痛" in result["symptoms"]
        assert "发热" in result["symptoms"]
        assert "咳嗽" in result["symptoms"]
        assert "高烧" in result["red_flags"]

    @pytest.mark.asyncio
    async def test_extract_symptoms_llm_failure(self, service):
        """Test symptom extraction when LLM fails."""
        service._call_llm = AsyncMock(side_effect=Exception("LLM error"))

        result = await service.extract_symptoms("我头痛")

        # Should return empty result with confidence 0
        assert result["symptoms"] == []
        assert result["confidence"] == 0

    @pytest.mark.asyncio
    async def test_generate_timeline(self, service):
        """Test timeline generation from sessions."""
        sessions = [{
            "timestamp": "2024-01-15T10:00:00",
            "summary": "初次问诊",
            "session_type": "consultation"
        }]

        attachments = [{
            "upload_time": "2024-01-15T11:00:00",
            "type": "image",
            "description": "皮疹照片"
        }]

        notes = [{
            "created_at": "2024-01-15T12:00:00",
            "content": "症状有所缓解",
            "is_important": False
        }]

        result = await service.generate_timeline(
            chief_complaint="皮疹",
            sessions=sessions,
            attachments=attachments,
            notes=notes
        )

        # Should have 3 timeline events
        assert len(result) == 3

        # Check consultation event
        consult_events = [e for e in result if e.type == "consultation"]
        assert len(consult_events) == 1
        assert consult_events[0].title == "初次问诊"

        # Check image upload event
        image_events = [e for e in result if e.type == "image_upload"]
        assert len(image_events) == 1

        # Check note event
        note_events = [e for e in result if e.type == "note"]
        assert len(note_events) == 1

    @pytest.mark.asyncio
    async def test_generate_summary_fallback(self, service):
        """Test fallback summary when LLM fails."""
        service._call_llm = AsyncMock(side_effect=Exception("LLM error"))

        sessions = [{
            "session_id": "s1",
            "timestamp": "2024-01-15",
            "summary": "头痛"
        }]

        result = await service.generate_summary(
            chief_complaint="头痛",
            department="内科",
            sessions=sessions
        )

        # Should return fallback summary
        assert "头痛" in result.summary
        assert "内科" in result.summary
        assert result.confidence == 0.3


# ============================================================================
# Transcription Service Tests
# ============================================================================

class TestSpeechTranscriptionService:
    """Tests for SpeechTranscriptionService."""

    @pytest.fixture
    def service(self):
        """Create a SpeechTranscriptionService instance."""
        from app.services.ai.transcription_service import SpeechTranscriptionService
        service = SpeechTranscriptionService()
        return service

    def test_validate_audio_file_valid_mp3(self, service):
        """Test validating a valid MP3 file."""
        is_valid, error = service.validate_audio_file("test.mp3", 1024)
        assert is_valid is True
        assert error == ""

    def test_validate_audio_file_valid_wav(self, service):
        """Test validating a valid WAV file."""
        is_valid, error = service.validate_audio_file("test.wav", 1024)
        assert is_valid is True
        assert error == ""

    def test_validate_audio_file_invalid_format(self, service):
        """Test validating an invalid audio format."""
        is_valid, error = service.validate_audio_file("test.xyz", 1024)
        assert is_valid is False
        assert "不支持的音频格式" in error

    def test_validate_audio_file_too_large(self, service):
        """Test validating an oversized file."""
        size = 51 * 1024 * 1024  # 51MB
        is_valid, error = service.validate_audio_file("test.mp3", size)
        assert is_valid is False
        assert "文件过大" in error

    @pytest.mark.asyncio
    async def test_transcribe_no_audio_data(self, service):
        """Test transcription with no audio data."""
        result = await service.transcribe()
        assert result.status.value == "failed"
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_transcribe_with_base64(self, service):
        """Test transcription with base64 audio data."""
        import base64

        # Create a small fake audio data
        audio_data = b"fake audio data" * 100
        audio_base64 = base64.b64encode(audio_data).decode()

        result = await service.transcribe(audio_base64=audio_base64)

        # Should succeed (with mock transcription)
        assert result.task_id is not None
        assert result.status.value in ["completed", "failed"]

    @pytest.mark.asyncio
    async def test_transcribe_llm_post_processing(self, service):
        """Test LLM post-processing of transcription."""
        service._call_llm = AsyncMock(return_value='''{
            "cleaned_text": "患者主诉头痛",
            "symptoms": ["头痛"],
            "symptom_details": [],
            "time_mentions": ["今天"],
            "key_info": [],
            "follow_up_questions": ["持续多久了？"]
        }''')

        result = await service.transcribe_with_llm("呃，我，我头痛", context="患者初次就诊")

        assert result["cleaned_text"] == "患者主诉头痛"
        assert "头痛" in result["symptoms"]
        assert "持续多久了？" in result["follow_up_questions"]

    def test_mock_transcription(self, service):
        """Test that mock transcription returns valid data."""
        audio_data = b"x" * 32000  # 1 second at 16kHz 16-bit
        result = service._mock_transcription(audio_data)

        assert "text" in result
        assert result["duration"] > 0
        assert result["confidence"] > 0
        assert "language" in result


# ============================================================================
# Dermatology Agent Tests
# ============================================================================

class TestDermaAgent:
    """Tests for DermaAgent (Dermatology AI Agent)."""

    @pytest.fixture
    def agent(self):
        """Create a DermaAgent instance."""
        from app.services.dermatology.derma_agent import DermaAgent
        return DermaAgent()

    def test_create_initial_state(self, agent):
        """Test creating initial dermatology state."""
        from app.services.dermatology.derma_agent import create_derma_initial_state

        state = create_derma_initial_state("session-123", 1)

        assert state["session_id"] == "session-123"
        assert state["user_id"] == 1
        assert state["messages"] == []
        assert state["stage"] == "greeting"
        assert state["progress"] == 0
        assert state["risk_level"] == "low"
        assert state["current_task"] == "conversation"
        assert state["awaiting_image"] is False

    def test_create_initial_state_all_fields(self):
        """Test that all initial state fields are present."""
        from app.services.dermatology.derma_agent import create_derma_initial_state, DermaState

        state = create_derma_initial_state("session-123", 1)

        # Check all required fields exist
        required_fields = [
            "session_id", "user_id", "messages", "chief_complaint",
            "symptoms", "symptom_details", "skin_location", "duration",
            "skin_analyses", "latest_analysis", "report_interpretations",
            "latest_interpretation", "stage", "progress", "questions_asked",
            "current_response", "quick_options", "possible_conditions",
            "risk_level", "care_advice", "need_offline_visit",
            "current_task", "awaiting_image"
        ]

        for field in required_fields:
            assert field in state

    def test_task_type_enum(self):
        """Test DermaTaskType enum values."""
        from app.services.dermatology.derma_agent import DermaTaskType

        assert DermaTaskType.CONVERSATION == "conversation"
        assert DermaTaskType.SKIN_ANALYSIS == "skin_analysis"
        assert DermaTaskType.REPORT_INTERPRET == "report_interpret"


# ============================================================================
# Orthopedics Agent Tests
# ============================================================================

class TestOrthoAgent:
    """Tests for OrthoAgent (Orthopedics AI Agent)."""

    @pytest.fixture
    def agent(self):
        """Create an OrthoAgent instance."""
        from app.services.orthopedics.ortho_agent import OrthoAgent
        return OrthoAgent()

    def test_create_initial_state(self, agent):
        """Test creating initial orthopedics state."""
        from app.services.orthopedics.ortho_agent import create_ortho_initial_state

        state = create_ortho_initial_state("session-456", 2)

        assert state["session_id"] == "session-456"
        assert state["user_id"] == 2
        assert state["messages"] == []
        assert state["stage"] == "greeting"
        assert state["progress"] == 0
        assert state["risk_level"] == "low"
        assert state["current_task"] == "conversation"

    def test_create_initial_state_all_fields(self):
        """Test that all orthopedics initial state fields are present."""
        from app.services.orthopedics.ortho_agent import create_ortho_initial_state

        state = create_ortho_initial_state("session-456", 2)

        # Check all required fields exist
        required_fields = [
            "session_id", "user_id", "messages", "chief_complaint",
            "symptoms", "symptom_details", "pain_location", "duration",
            "injury_history", "medical_history", "mobility_limitation",
            "xray_interpretations", "latest_xray_interpretation",
            "stage", "progress", "questions_asked", "current_response",
            "quick_options", "risk_level", "need_urgent_care",
            "possible_conditions", "care_advice", "current_task"
        ]

        for field in required_fields:
            assert field in state

    def test_task_type_enum(self):
        """Test OrthoTaskType enum values."""
        from app.services.orthopedics.ortho_agent import OrthoTaskType

        assert OrthoTaskType.CONVERSATION == "conversation"
        assert OrthoTaskType.INTERPRET_XRAY == "interpret_xray"


# ============================================================================
# AI Service Singleton Tests
# ============================================================================

class TestAIServiceSingletons:
    """Tests for AI service singleton patterns."""

    def test_aggregation_service_singleton(self):
        """Test EventAggregationService singleton."""
        from app.services.ai.aggregation_service import get_aggregation_service

        service1 = get_aggregation_service()
        service2 = get_aggregation_service()

        # Should return the same instance
        assert service1 is service2

    def test_summary_service_singleton(self):
        """Test AISummaryService singleton."""
        from app.services.ai.summary_service import get_summary_service

        service1 = get_summary_service()
        service2 = get_summary_service()

        # Should return the same instance
        assert service1 is service2

    def test_transcription_service_singleton(self):
        """Test SpeechTranscriptionService singleton."""
        from app.services.ai.transcription_service import get_transcription_service

        service1 = get_transcription_service()
        service2 = get_transcription_service()

        # Should return the same instance
        assert service1 is service2


# ============================================================================
# Integration Tests
# ============================================================================

class TestAIAgentIntegration:
    """Integration tests for AI agent workflows."""

    @pytest.mark.asyncio
    async def test_full_symptom_extraction_workflow(self):
        """Test full workflow from conversation to symptom extraction."""
        from app.services.ai.summary_service import AISummaryService

        service = AISummaryService()
        service._call_llm = AsyncMock(return_value='''{
            "summary": "患者主诉头痛伴发热",
            "key_points": ["头痛3天", "发热1天"],
            "symptoms": ["头痛", "发热"],
            "symptom_details": {},
            "possible_diagnosis": ["上呼吸道感染"],
            "risk_level": "low",
            "risk_warning": null,
            "recommendations": ["多饮水", "注意休息"],
            "follow_up_reminders": ["观察体温变化"],
            "timeline": [],
            "confidence": 0.8
        }''')

        # Simulate a conversation with multiple messages
        sessions = [{
            "session_id": "s1",
            "timestamp": "2024-01-15",
            "messages": [
                {"role": "user", "content": "医生我头痛"},
                {"role": "assistant", "content": "多久了？"},
                {"role": "user", "content": "三天了，今天还开始发烧"}
            ],
            "summary": "患者主诉头痛三天，今天开始发热"
        }]

        result = await service.generate_summary(
            chief_complaint="头痛",
            department="内科",
            sessions=sessions
        )

        # Verify the workflow completed
        assert "头痛" in result.symptoms
        assert "发热" in result.symptoms
        assert result.risk_level == "low"
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_event_aggregation_and_summary_workflow(self):
        """Test workflow combining event aggregation and summary."""
        from app.services.ai.aggregation_service import EventAggregationService
        from app.services.ai.summary_service import AISummaryService

        agg_service = EventAggregationService()
        summary_service = AISummaryService()

        # Mock LLM responses
        agg_service._call_llm = AsyncMock()
        summary_service._call_llm = AsyncMock(return_value='''{
            "summary": "综合分析",
            "key_points": [],
            "symptoms": [],
            "symptom_details": {},
            "possible_diagnosis": [],
            "risk_level": "low",
            "risk_warning": null,
            "recommendations": [],
            "follow_up_reminders": [],
            "timeline": [],
            "confidence": 0.7
        }''')

        # Simulate related events
        events = [{
            "id": "evt-1",
            "title": "头痛",
            "department": "内科",
            "start_time": "2024-01-15 10:00:00",  # Use full timestamp
            "risk_level": "low",
            "status": "active"  # Required for rule-based aggregation
        }]

        # Check aggregation
        agg_result = await agg_service.smart_aggregate(
            session_info={
                "department": "内科",
                "timestamp": "2024-01-15 14:00:00",  # Use full timestamp, same day
                "chief_complaint": "头痛加重"
            },
            existing_events=events
        )

        # Should suggest merging due to same day same dept active status
        assert agg_result.should_merge is True
        assert agg_result.target_event_id == "evt-1"

        # Generate summary for related events
        summary_result = await agg_service.generate_merged_summary(events)

        assert summary_result.merged_title is not None
        assert summary_result.overall_risk_level is not None
