"""Knowledge retrievers for triage engine."""
from typing import Any, Dict, List
import httpx

from ...config import get_settings
from ..specialty import get_specialty_pack


async def quick_retrieve(query: str, specialty: str, top_k: int = 5) -> Dict[str, Any]:
    """Call external knowledge service search endpoint directly."""
    if not query:
        return {"found": False, "results": [], "query_used": query, "source": "quick_retriever"}

    settings = get_settings()
    base_url = settings.KNOWLEDGE_SERVICE_URL.rstrip("/")
    headers = {"Content-Type": "application/json"}
    if settings.KNOWLEDGE_SERVICE_API_KEY:
        headers["X-API-Key"] = settings.KNOWLEDGE_SERVICE_API_KEY

    payload = {
        "query": query,
        "specialty": specialty,
        "top_k": top_k,
        "score_threshold": 0.0,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.KNOWLEDGE_SERVICE_TIMEOUT) as client:
            resp = await client.post(f"{base_url}/api/v1/search", json=payload, headers=headers)
            resp.raise_for_status()
            body = resp.json()
            data = body.get("data", {})
            return {
                "found": data.get("count", 0) > 0,
                "results": data.get("results", []),
                "count": data.get("count", 0),
                "query_used": data.get("query", query),
                "source": "quick_retriever",
            }
    except Exception as exc:
        return {
            "found": False,
            "results": [],
            "count": 0,
            "query_used": query,
            "source": "quick_retriever",
            "error": str(exc),
        }


async def corrective_retrieve(query: str, specialty: str, top_k: int = 5) -> Dict[str, Any]:
    """Heuristic corrective retrieval: rewrite query and retry once."""
    first = await quick_retrieve(query, specialty, top_k=top_k)
    if first.get("found"):
        first["source"] = "corrective_retriever"
        first["correction_applied"] = False
        return first

    rewritten = _rewrite_query(query, specialty)
    second = await quick_retrieve(rewritten, specialty, top_k=top_k)
    second["source"] = "corrective_retriever"
    second["correction_applied"] = rewritten != query
    second["original_query"] = query
    return second


def _rewrite_query(query: str, specialty: str) -> str:
    """Simple medical-oriented rewrite without LLM dependency."""
    q = query.strip()
    if not q:
        return q

    pack = get_specialty_pack(specialty)
    expansions: List[str] = []

    # generic heuristics
    if "疼" in q or "痛" in q:
        expansions.extend(["症状", "持续时间", "诱因"])
    if "发烧" in q or "发热" in q:
        expansions.extend(["体温", "伴随症状", "感染"])
    if "咳" in q:
        expansions.extend(["痰", "呼吸困难", "病程"])
    if "皮疹" in q or "瘙痒" in q:
        expansions.extend(["分布", "过敏", "诱因"])

    # specialty-tailored terms
    expansions.extend(pack.rewrite_terms)

    uniq = []
    for t in expansions:
        if t and t not in uniq:
            uniq.append(t)

    if not uniq:
        uniq = ["症状", "鉴别", "处理建议"]

    return f"{q} {' '.join(uniq[:4])}"
