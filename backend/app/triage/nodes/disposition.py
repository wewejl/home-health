"""Disposition decision node."""
from typing import Dict, Any


DISPOSITION_MAP = {
    "emergency": "er",
    "high": "urgent_clinic",
    "medium": "clinic",
    "low": "home",
}


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("disposition")
    state["node_trace"] = trace

    risk = state.get("risk_level", "low")
    disposition = DISPOSITION_MAP.get(risk, "clinic")

    # Policy hard gate: evidence insufficient + non-low risk -> clinic at least
    if not state.get("evidence_ok") and risk in {"medium", "high"}:
        disposition = "clinic"
        hits = state.get("policy_hits", [])
        hits.append("insufficient_evidence_downgrade")
        state["policy_hits"] = hits

    state["disposition"] = disposition
    state["progress"] = max(state.get("progress", 0), 90)
    return state
