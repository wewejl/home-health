"""Corrective retrieval node."""
from typing import Dict, Any
from ..knowledge.retriever import corrective_retrieve


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("retrieve_corrective")
    state["node_trace"] = trace

    specialty = state.get("specialty", "general")
    query = state.get("retrieval_query") or state.get("last_user_message", "")

    if not query:
        state["evidence_candidates"] = []
        state["evidence_selected"] = []
        state["evidence_ok"] = False
        state["evidence_reason"] = "纠偏检索缺少查询"
        return state

    result = await corrective_retrieve(query=query, specialty=specialty, top_k=5)

    candidates = []
    for idx, item in enumerate(result.get("results", [])[:5]):
        candidates.append({
            "source": result.get("source", "corrective_retriever"),
            "score": float(item.get("score", max(0.0, 0.8 - idx * 0.1))),
            "content": item.get("content", ""),
            "metadata": item.get("metadata", {}),
        })

    state["evidence_candidates"] = candidates
    selected = []
    for i, item in enumerate(candidates[:3], start=1):
        row = dict(item)
        row["citation_id"] = f"E{i}"
        selected.append(row)
    state["evidence_selected"] = selected
    state["evidence_ok"] = len(candidates) > 0
    state["evidence_reason"] = (
        f"纠偏检索完成，query={result.get('query_used', query)}"
        if candidates else "纠偏检索仍未找到有效证据"
    )
    state["progress"] = max(state.get("progress", 0), 60)
    return state
