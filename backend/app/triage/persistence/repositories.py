"""State-level persistence helpers for triage observability.

Phase D keeps persistence inside `session.agent_state` under `_triage_audit`
so we can ship without DB schema migration.
"""
from __future__ import annotations

from typing import Any, Dict, List

MAX_AUDIT_ITEMS = 50


def append_evidence_log(state: Dict[str, Any]) -> None:
    """Append current-turn evidence log into state."""
    audit = _ensure_audit(state)
    item = {
        "turn": int(state.get("turn_index", 0)),
        "query": state.get("retrieval_query", ""),
        "specialty": state.get("specialty", "general"),
        "evidence_ok": bool(state.get("evidence_ok", False)),
        "evidence_reason": state.get("evidence_reason", ""),
        "selected": _compact_evidence(state.get("evidence_selected", [])),
    }
    _append_capped(audit["evidence_log"], item)


def append_decision_log(state: Dict[str, Any]) -> None:
    """Append current-turn triage decision log into state."""
    audit = _ensure_audit(state)
    item = {
        "turn": int(state.get("turn_index", 0)),
        "risk_level": state.get("risk_level", "low"),
        "risk_score": int(state.get("risk_score", 0) or 0),
        "risk_reasoning": state.get("risk_reasoning", ""),
        "disposition": state.get("disposition"),
        "red_flags": list(state.get("red_flags", [])),
        "policy_hits": list(state.get("policy_hits", [])),
    }
    _append_capped(audit["decision_log"], item)


def append_metrics_log(state: Dict[str, Any]) -> None:
    """Append current-turn metrics snapshot into state."""
    audit = _ensure_audit(state)
    selected_count = len(state.get("evidence_selected", []))
    missing_count = len(state.get("missing_slots", []))

    item = {
        "turn": int(state.get("turn_index", 0)),
        "node_count": len(state.get("node_trace", [])),
        "selected_evidence_count": selected_count,
        "missing_slots_count": missing_count,
        "risk_level": state.get("risk_level", "low"),
        "disposition": state.get("disposition"),
    }
    _append_capped(audit["metrics_log"], item)


def latest_audit_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return compact summary for API response/debug."""
    audit = state.get("_triage_audit", {}) or {}
    return {
        "evidence_turns": len(audit.get("evidence_log", [])),
        "decision_turns": len(audit.get("decision_log", [])),
        "metrics_turns": len(audit.get("metrics_log", [])),
        "last_decision": (audit.get("decision_log", []) or [None])[-1],
    }


def _ensure_audit(state: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    audit = state.get("_triage_audit")
    if not isinstance(audit, dict):
        audit = {}
    audit.setdefault("evidence_log", [])
    audit.setdefault("decision_log", [])
    audit.setdefault("metrics_log", [])
    state["_triage_audit"] = audit
    return audit


def _append_capped(rows: List[Dict[str, Any]], item: Dict[str, Any]) -> None:
    rows.append(item)
    if len(rows) > MAX_AUDIT_ITEMS:
        del rows[:-MAX_AUDIT_ITEMS]


def _compact_evidence(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    compact = []
    for row in rows[:5]:
        compact.append(
            {
                "citation_id": row.get("citation_id"),
                "source": row.get("source"),
                "score": float(row.get("score", 0.0)),
                "content": (row.get("content") or "")[:180],
            }
        )
    return compact
