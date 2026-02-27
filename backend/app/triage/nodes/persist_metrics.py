"""Persist and metrics node (phase D state-level persistence)."""
from typing import Dict, Any
from ..metrics import record_turn_metrics
from ..persistence import (
    append_evidence_log,
    append_decision_log,
    append_metrics_log,
)


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("persist_metrics")
    state["node_trace"] = trace
    record_turn_metrics(state)
    append_evidence_log(state)
    append_decision_log(state)
    append_metrics_log(state)
    return state
