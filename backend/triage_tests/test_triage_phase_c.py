import pytest

from backend.app.triage.nodes.evidence_gate import run as evidence_gate_run
from backend.app.triage.nodes.compose_response import run as compose_response_run
from backend.app.triage.nodes.differential import run as differential_run
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
    assert updated["next_question"]
    assert "持续" in updated["next_question"] or "多久" in updated["next_question"]


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
    assert "可能原因（按优先级）" in text
    assert "现在可以做什么" in text


@pytest.mark.asyncio
async def test_compose_response_collecting_branch_uses_dynamic_question():
    state = {
        "specialty": "general",
        "risk_level": "low",
        "disposition": "home",
        "differentials": [],
        "missing_slots": ["duration", "severity"],
        "next_question": "这个不适持续了多久？",
        "quick_options": ["前天开始", "今天突然", "已经一周"],
        "evidence_selected": [],
        "node_trace": [],
    }

    updated = await compose_response_run(state)
    text = updated["current_response"]
    assert "下一步请先回答" in text
    assert "可直接选" in text
    assert "这个不适持续了多久" in text


@pytest.mark.asyncio
async def test_differential_builds_heuristics_when_no_evidence():
    state = {
        "specialty": "general",
        "evidence_selected": [],
        "evidence_candidates": [],
        "symptom_slots": {
            "symptoms": ["咽痛", "咳嗽", "鼻塞", "流涕"],
            "triggers": ["装修", "不通风"],
            "scene": ["晚上", "卧室"],
        },
        "last_user_message": "喉咙刀割样疼，晚上卧室更严重。",
        "chief_complaint": "喉咙疼痛",
        "node_trace": [],
    }
    updated = await differential_run(state)
    names = [d["name"] for d in updated["differentials"]]
    assert any("环境刺激" in n for n in names)


@pytest.mark.asyncio
async def test_orchestrator_emergency_path_sets_er_disposition():
    orchestrator = TriageOrchestrator()
    state = {"session_id": "s-1", "user_id": 1, "agent_type": "cardiology"}

    result = await orchestrator.run(state=state, user_input="突然剧烈胸痛并呼吸困难", action="conversation")

    assert result.risk_level == "emergency"
    assert result.specialty_data["triage"]["disposition"] == "er"
    assert "立即前往急诊" in result.message or "拨打120" in result.message
