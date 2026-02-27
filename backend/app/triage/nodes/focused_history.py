"""Focused history collection node."""
from typing import Dict, Any
from ..policy import get_required_slots
from ..specialty import get_specialty_pack


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("focused_history")
    state["node_trace"] = trace

    specialty = state.get("specialty", "general")
    pack = get_specialty_pack(specialty)
    required_slots = get_required_slots(specialty)
    symptom_slots = state.get("symptom_slots", {})

    missing = [slot for slot in required_slots if not symptom_slots.get(slot)]
    state["missing_slots"] = missing
    if missing:
        state["quick_options"] = pack.followup_questions[:3]
    state["stage"] = "collecting" if missing else "analyzing"
    state["progress"] = max(state.get("progress", 0), 25)
    return state
