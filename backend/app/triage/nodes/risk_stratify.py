"""Risk stratification node."""
from typing import Dict, Any
from ..safety.risk import assess_risk


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("risk_stratify")
    state["node_trace"] = trace

    if state.get("red_flags"):
        state["risk_level"] = "emergency"
        state["risk_score"] = 95
        state["risk_reasoning"] = f"命中危险信号: {', '.join(state.get('red_flags', []))}"
        state["progress"] = max(state.get("progress", 0), 80)
        return state

    slots = state.get("symptom_slots", {})
    symptoms = slots.get("symptoms", [])
    specialty = state.get("specialty", "general")

    result = assess_risk(symptoms=symptoms, free_text=state.get("last_user_message", ""), specialty=specialty)
    state["risk_level"] = result.get("risk_level", "low")
    state["risk_score"] = int(result.get("score", 0))
    state["risk_reasoning"] = result.get("reasoning", "")
    state["progress"] = max(state.get("progress", 0), 80)
    return state
