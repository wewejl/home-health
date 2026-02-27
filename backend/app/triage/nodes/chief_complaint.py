"""Chief complaint node."""
from typing import Dict, Any


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("chief_complaint")
    state["node_trace"] = trace

    latest = (state.get("last_user_message") or "").strip()
    if not state.get("chief_complaint") and latest:
        state["chief_complaint"] = latest[:120]

    state["stage"] = "collecting"
    state["progress"] = max(state.get("progress", 0), 15)
    return state
