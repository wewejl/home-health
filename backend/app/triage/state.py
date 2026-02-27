"""Triage engine state model."""
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class TriageState(TypedDict, total=False):
    # Session
    session_id: str
    user_id: int
    agent_type: str
    specialty: str
    turn_index: int

    # Conversation
    messages: List[Dict[str, str]]
    last_user_message: str

    # Clinical slots
    chief_complaint: str
    symptom_slots: Dict[str, Any]
    history_slots: Dict[str, Any]
    missing_slots: List[str]

    # Evidence
    retrieval_query: str
    evidence_candidates: List[Dict[str, Any]]
    evidence_selected: List[Dict[str, Any]]
    evidence_ok: bool
    evidence_reason: str

    # Reasoning / risk
    differentials: List[Dict[str, Any]]
    risk_level: Optional[str]
    risk_score: int
    risk_reasoning: str
    red_flags: List[str]
    disposition: Optional[str]

    # Output
    current_response: str
    quick_options: List[str]
    stage: str
    progress: int

    # Runtime / trace
    node_trace: List[str]
    policy_hits: List[str]
    errors: List[str]


def create_initial_triage_state(session_id: str, user_id: int, agent_type: str) -> TriageState:
    """Create default triage state."""
    return {
        "session_id": session_id,
        "user_id": user_id,
        "agent_type": agent_type,
        "specialty": "general",
        "turn_index": 0,
        "messages": [],
        "last_user_message": "",
        "chief_complaint": "",
        "symptom_slots": {},
        "history_slots": {},
        "missing_slots": [],
        "retrieval_query": "",
        "evidence_candidates": [],
        "evidence_selected": [],
        "evidence_ok": False,
        "evidence_reason": "",
        "differentials": [],
        "risk_level": "low",
        "risk_score": 0,
        "risk_reasoning": "",
        "red_flags": [],
        "disposition": None,
        "current_response": "",
        "quick_options": [],
        "stage": "collecting",
        "progress": 0,
        "node_trace": [],
        "policy_hits": [],
        "errors": [],
    }
