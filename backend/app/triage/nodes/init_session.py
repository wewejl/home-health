"""Init session node."""
from typing import Dict, Any
from ..policy import infer_specialty


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("init_session")
    state["node_trace"] = trace

    if not state.get("specialty"):
        state["specialty"] = infer_specialty(state.get("agent_type", "general"))

    state["stage"] = state.get("stage", "collecting")
    state["progress"] = max(state.get("progress", 0), 5)
    return state
