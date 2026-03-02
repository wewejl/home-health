import pytest

from backend.app.triage.knowledge.retriever import _rewrite_query
from backend.app.triage.nodes.compose_response import run as compose_response_run
from backend.app.triage.nodes.extract_normalize import run as extract_normalize_run
from backend.app.triage.safety.risk import assess_risk
from backend.app.triage.specialty import get_specialty_pack


def test_cardiology_pack_is_production_grade_configured():
    pack = get_specialty_pack("cardiology")
    assert pack.min_evidence_count >= 2
    assert "chest_pain_character" in pack.required_slots
    assert len(pack.emergency_signs) >= 4
    assert "er" in pack.disposition_advice


def test_respiratory_pack_is_production_grade_configured():
    pack = get_specialty_pack("respiratory")
    assert pack.min_avg_score >= 0.15
    assert "temperature" in pack.required_slots
    assert any("呼吸" in s or "紫绀" in s for s in pack.emergency_signs)


def test_general_pack_is_production_grade_configured():
    pack = get_specialty_pack("general")
    assert "symptoms" in pack.required_slots
    assert len(pack.warning_signals) >= 3


def test_specialty_rewrite_query_uses_pack_terms():
    q = "胸痛两天"
    rewritten = _rewrite_query(q, "cardiology")
    assert "心肌缺血" in rewritten or "胸痛性质" in rewritten


def test_cardiology_risk_hits_emergency_signal():
    result = assess_risk(symptoms=["胸痛", "呼吸困难"], free_text="持续胸痛伴大汗", specialty="cardiology")
    assert result["risk_level"] == "emergency"


@pytest.mark.asyncio
async def test_compose_response_uses_specialty_warning_and_disposition_advice():
    state = {
        "specialty": "respiratory",
        "risk_level": "medium",
        "disposition": "clinic",
        "differentials": [{"name": "呼吸道感染", "confidence": 0.66}],
        "missing_slots": [],
        "evidence_selected": [{"citation_id": "E1", "content": "持续咳嗽伴低热建议门诊评估"}],
        "node_trace": [],
    }

    updated = await compose_response_run(state)
    text = updated["current_response"]
    assert "呼吸导诊" in text
    assert "建议呼吸科门诊评估" in text
    assert "静息气促" in text or "持续高热" in text or "痰中带血" in text


@pytest.mark.asyncio
async def test_extract_normalize_captures_environment_and_throat_synonyms():
    state = {
        "last_user_message": "喉咙非常疼，前天开始逐渐加重，晚上卧室更明显，家里不通风还刚装修过。",
        "symptom_slots": {},
        "node_trace": [],
    }

    updated = await extract_normalize_run(state)
    slots = updated["symptom_slots"]
    assert "咽痛" in slots.get("symptoms", [])
    assert slots.get("duration") in {"前天", "最近", "今天", "昨天"} or slots.get("duration")
    assert slots.get("severity") in {"high", "medium", "low"}
    assert "装修" in slots.get("triggers", [])
    assert "卧室" in slots.get("scene", [])
