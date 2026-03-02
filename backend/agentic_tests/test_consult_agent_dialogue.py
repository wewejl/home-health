import pytest

from backend.app.agentic.consult_agent import AgenticConsultOrchestrator
from backend.app.agentic.types import ComposedReply, TurnPlan


@pytest.mark.asyncio
async def test_consult_agent_keeps_full_session_messages(monkeypatch):
    async def fake_plan(self, specialty, conversation_text, last_user_message):
        _ = specialty
        _ = conversation_text
        _ = last_user_message
        return TurnPlan(
            needs_retrieval=False,
            retrieval_query="",
            next_step="ask",
            brief_rationale="补充关键信息",
            next_question="症状持续多久？",
            quick_options=["今天", "前天", "一周以上"],
            risk_level="low",
        )

    async def fake_compose(self, specialty, conversation_text, plan, evidence):
        _ = specialty
        _ = conversation_text
        _ = plan
        _ = evidence
        return ComposedReply(
            message="先确认一下，您的症状持续多久了？",
            quick_options=["今天", "前天", "一周以上"],
            risk_level="low",
            disposition="home",
            red_flags=[],
        )

    monkeypatch.setattr(AgenticConsultOrchestrator, "_plan_turn", fake_plan)
    monkeypatch.setattr(AgenticConsultOrchestrator, "_compose_turn", fake_compose)

    agent = AgenticConsultOrchestrator()
    state = {
        "session_id": "s1",
        "user_id": 1,
        "agent_type": "general",
        "messages": [{"type": "human", "content": "我喉咙疼"}],
        "turn_index": 1,
    }

    response = await agent.run(state=state, user_input="还伴有鼻塞")

    assert response.stage == "collecting"
    assert response.risk_level == "low"
    assert len(response.next_state["messages"]) == 3
    assert response.next_state["messages"][-1]["type"] == "ai"
    assert "持续多久" in response.message


@pytest.mark.asyncio
async def test_consult_agent_calls_retrieval_subagent_when_needed(monkeypatch):
    called = {"value": False}

    async def fake_plan(self, specialty, conversation_text, last_user_message):
        _ = specialty
        _ = conversation_text
        _ = last_user_message
        return TurnPlan(
            needs_retrieval=True,
            retrieval_query="咽痛与过敏鉴别",
            next_step="advise",
            brief_rationale="需要证据支持",
            next_question="",
            quick_options=["继续观察", "需要就医吗"],
            risk_level="medium",
        )

    async def fake_retrieve(*args, **kwargs):
        _ = args
        _ = kwargs
        called["value"] = True

        class _Bundle:
            count = 1
            confidence = 0.81
            highlights = ["证据要点"]
            summary = "证据要点"
            items = []

            def model_dump(self):
                return {
                    "query_used": "咽痛与过敏鉴别",
                    "found": True,
                    "count": 1,
                    "confidence": 0.81,
                    "highlights": ["证据要点"],
                    "summary": "证据要点",
                    "items": [],
                }

        return _Bundle()

    async def fake_compose(self, specialty, conversation_text, plan, evidence):
        _ = specialty
        _ = conversation_text
        _ = plan
        _ = evidence
        return ComposedReply(
            message="结合目前信息，更倾向环境刺激导致咽喉不适。",
            quick_options=["如何改善环境", "哪些情况要就医"],
            risk_level="medium",
            disposition="clinic",
            red_flags=[],
        )

    monkeypatch.setattr(AgenticConsultOrchestrator, "_plan_turn", fake_plan)
    monkeypatch.setattr(AgenticConsultOrchestrator, "_compose_turn", fake_compose)

    agent = AgenticConsultOrchestrator()
    monkeypatch.setattr(agent._retrieval_subagent, "run", fake_retrieve)

    response = await agent.run(
        state={"session_id": "s2", "user_id": 1, "agent_type": "general", "messages": []},
        user_input="喉咙痛和空气不好有关系吗",
    )

    assert called["value"] is True
    assert response.stage == "diagnosing"
    assert response.risk_level == "medium"
    assert response.specialty_data["agentic"]["needs_retrieval"] is True
