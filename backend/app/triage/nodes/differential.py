"""Differential generation node."""
from typing import Dict, Any, List


def _build_from_evidence(evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for idx, item in enumerate(evidence[:3], start=1):
        content = (item.get("content") or "").strip()
        title = content.split("\n", 1)[0][:40] if content else f"候选诊断{idx}"
        out.append({
            "name": title or f"候选诊断{idx}",
            "confidence": round(max(0.2, 0.85 - idx * 0.15), 2),
            "evidence": content[:180],
        })
    return out


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("differential")
    state["node_trace"] = trace

    evidence = state.get("evidence_selected") or state.get("evidence_candidates", [])
    differentials = _build_from_evidence(evidence)

    if not differentials:
        complaint = state.get("chief_complaint", "")
        differentials = [{
            "name": "信息不足待排查",
            "confidence": 0.25,
            "evidence": complaint[:180],
        }] if complaint else []

    state["differentials"] = differentials
    state["stage"] = "analyzing"
    state["progress"] = max(state.get("progress", 0), 70)
    return state
