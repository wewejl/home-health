"""Evidence quality gate node."""
from typing import Dict, Any
from ..specialty import get_specialty_pack


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("evidence_gate")
    state["node_trace"] = trace

    candidates = state.get("evidence_candidates", [])
    pack = get_specialty_pack(state.get("specialty", "general"))
    if not candidates:
        state["evidence_ok"] = False
        state["evidence_reason"] = "没有检索到可用证据"
        state["progress"] = max(state.get("progress", 0), 55)
        return state

    scores = [float(item.get("score", 0.0)) for item in candidates]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    evidence_ok = len(candidates) >= pack.min_evidence_count and avg_score >= pack.min_avg_score
    state["evidence_ok"] = evidence_ok
    state["evidence_reason"] = (
        f"证据通过(count={len(candidates)}, avg_score={avg_score:.2f}, specialty={pack.code})"
        if evidence_ok
        else f"证据不足(count={len(candidates)}, avg_score={avg_score:.2f}, specialty={pack.code})"
    )
    if evidence_ok:
        ranked = sorted(candidates, key=lambda x: float(x.get("score", 0.0)), reverse=True)[:3]
        selected = []
        for i, item in enumerate(ranked, start=1):
            row = dict(item)
            row["citation_id"] = f"E{i}"
            selected.append(row)
        state["evidence_selected"] = selected
    else:
        state["evidence_selected"] = []
    state["progress"] = max(state.get("progress", 0), 55)
    return state
