import pytest

from backend.app.triage.nodes.evidence_gate import run as evidence_gate_run
from backend.app.triage.nodes.compose_response import run as compose_response_run
from backend.app.triage.nodes.focused_history import run as focused_history_run
from backend.app.triage.orchestrator import TriageOrchestrator


@pytest.mark.asyncio
async def test_evidence_gate_uses_specialty_thresholds_for_cardiology():
    # cardiology requires >=2 evidences in phase C pack
    state = {
        "specialty": "cardiology",
        "evidence_candidates": [
            {"score": 0.9, "content": "证据A", "source": "x"}
        ],
        "node_trace": [],
    }

    updated = await evidence_gate_run(state)
    assert updated["evidence_ok"] is False
    assert updated["evidence_selected"] == []

    state["evidence_candidates"].append({"score": 0.8, "content": "证据B", "source": "y"})
    updated = await evidence_gate_run(state)
    assert updated["evidence_ok"] is True
    assert len(updated["evidence_selected"]) == 2
    assert updated["evidence_selected"][0]["citation_id"].startswith("E")


@pytest.mark.asyncio
async def test_focused_history_injects_pack_followup_questions():
    state = {
        "specialty": "dermatology",
        "symptom_slots": {"symptoms": ["皮疹"]},
        "node_trace": [],
    }

    updated = await focused_history_run(state)
    assert updated["missing_slots"]
    assert len(updated["quick_options"]) > 0


@pytest.mark.asyncio
async def test_compose_response_contains_citations_and_stable_template():
    state = {
        "specialty": "general",
        "risk_level": "medium",
        "disposition": "clinic",
        "differentials": [{"name": "上呼吸道感染", "confidence": 0.72}],
        "missing_slots": [],
        "evidence_selected": [
            {"citation_id": "E1", "content": "发热与咳嗽持续超过3天建议评估肺部感染"},
            {"citation_id": "E2", "content": "胸闷需结合呼吸困难与氧饱和度判断"},
        ],
        "node_trace": [],
    }

    updated = await compose_response_run(state)
    text = updated["current_response"]
    assert "初步导诊判断" in text
    assert "风险等级" in text
    assert "依据要点" in text
    assert "[E1]" in text


@pytest.mark.asyncio
async def test_orchestrator_emergency_path_sets_er_disposition():
    orchestrator = TriageOrchestrator()
    state = {"session_id": "s-1", "user_id": 1, "agent_type": "cardiology"}

    result = await orchestrator.run(state=state, user_input="突然剧烈胸痛并呼吸困难", action="conversation")

    assert result.risk_level == "emergency"
    assert result.specialty_data["triage"]["disposition"] == "er"
    assert "立即前往急诊" in result.message or "拨打120" in result.message
