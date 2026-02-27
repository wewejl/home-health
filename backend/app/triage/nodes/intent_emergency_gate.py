"""Intent and emergency gate node."""
from typing import Dict, Any
from ..policy import detect_red_flags


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("intent_emergency_gate")
    state["node_trace"] = trace

    text = state.get("last_user_message", "")
    red_flags = detect_red_flags(text)
    state["red_flags"] = red_flags
    if red_flags:
        hits = state.get("policy_hits", [])
        hits.append("emergency_red_flag")
        state["policy_hits"] = hits
        state["risk_level"] = "emergency"
        state["risk_reasoning"] = f"命中危险信号: {', '.join(red_flags)}"
        state["disposition"] = "er"

    return state
