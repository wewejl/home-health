"""Metrics hooks for triage pipeline (phase B lightweight)."""
from typing import Dict, Any


def record_turn_metrics(state: Dict[str, Any]) -> None:
    """Attach lightweight in-state metrics summary for debugging."""
    state["turn_metrics"] = {
        "turn_index": state.get("turn_index", 0),
        "evidence_count": len(state.get("evidence_selected", [])),
        "risk_level": state.get("risk_level", "low"),
        "disposition": state.get("disposition"),
    }
