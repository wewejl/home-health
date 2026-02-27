"""Quick evidence retrieval node."""
from typing import Dict, Any
from ..knowledge.retriever import quick_retrieve


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("retrieve_quick")
    state["node_trace"] = trace

    specialty = state.get("specialty", "general")
    query = state.get("chief_complaint") or state.get("last_user_message", "")
    state["retrieval_query"] = query

    if not query:
        state["evidence_candidates"] = []
        return state

    result = await quick_retrieve(query=query, specialty=specialty, top_k=5)
    candidates = []
    for idx, item in enumerate(result.get("results", [])[:5]):
        candidates.append({
            "source": result.get("source", "vector_knowledge_base"),
            "score": float(item.get("score", max(0.0, 1 - idx * 0.1))),
            "content": item.get("content", ""),
            "metadata": item.get("metadata", {}),
        })

    state["evidence_candidates"] = candidates
    state["progress"] = max(state.get("progress", 0), 45)
    return state
