"""Knowledge retrieval subagent (search + dedupe + summarize)."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

import httpx

from ...config import get_settings
from ..types import EvidenceBundle, EvidenceItem, empty_evidence_bundle

logger = logging.getLogger(__name__)


class RetrievalSubagent:
    """Single retrieval subagent for RAG evidence bundle."""

    async def run(
        self,
        conversation_text: str,
        last_user_message: str,
        specialty: str = "general",
        query_hint: str = "",
        top_k: int = 5,
    ) -> EvidenceBundle:
        query = (query_hint or "").strip() or self._build_query(last_user_message, conversation_text)
        if not query:
            return empty_evidence_bundle("")

        result = await self._search(query=query, specialty=specialty, top_k=top_k)

        raw_results = result.get("results", []) or []
        query_used = result.get("query_used", query)

        # fallback to general if specialty-specific retrieval misses
        if not raw_results and specialty != "general":
            fallback = await self._search(query=query, specialty="general", top_k=top_k)
            raw_results = fallback.get("results", []) or []
            query_used = fallback.get("query_used", query)

        items = self._normalize_items(raw_results)
        deduped = self._dedupe_items(items)
        highlights = self._build_highlights(deduped)
        confidence = self._confidence(deduped)
        summary = "；".join(highlights[:3]) if highlights else ""

        return EvidenceBundle(
            query_used=query_used,
            found=bool(deduped),
            count=len(deduped),
            confidence=confidence,
            highlights=highlights,
            summary=summary,
            items=deduped,
        )

    async def _search(self, query: str, specialty: str, top_k: int) -> Dict[str, Any]:
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
                    "specialty": specialty,
                }
        except httpx.TimeoutError as exc:
            logger.warning("Knowledge service timeout: specialty=%s query=%s error=%s", specialty, query[:50], exc)
            return {
                "found": False,
                "results": [],
                "count": 0,
                "query_used": query,
                "specialty": specialty,
            }
        except httpx.HTTPStatusError as exc:
            logger.error("Knowledge service HTTP error: status=%s specialty=%s", exc.response.status_code, specialty)
            return {
                "found": False,
                "results": [],
                "count": 0,
                "query_used": query,
                "specialty": specialty,
            }
        except Exception as exc:
            logger.exception("Knowledge service unexpected error: specialty=%s query=%s", specialty, query[:50])
            return {
                "found": False,
                "results": [],
                "count": 0,
                "query_used": query,
                "specialty": specialty,
            }

    def _build_query(self, last_user_message: str, conversation_text: str) -> str:
        seed = (last_user_message or "").strip()
        if seed:
            return seed
        lines = [line.strip() for line in (conversation_text or "").splitlines() if line.strip()]
        return lines[-1][:200] if lines else ""

    def _normalize_items(self, raw_results: List[Any]) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        for raw in raw_results:
            if isinstance(raw, str):
                content = raw.strip()
                score = 0.0
                metadata: Dict[str, Any] = {}
            else:
                content = (
                    str(raw.get("content") or raw.get("chunk_text") or raw.get("text") or "")
                    .replace("\n", " ")
                    .strip()
                )
                score = self._safe_score(raw.get("score", 0.0))
                metadata = raw.get("metadata", {}) or {}

            if not content:
                continue

            items.append(
                EvidenceItem(
                    content=content,
                    score=score,
                    source="vector_knowledge_base",
                    metadata=metadata if isinstance(metadata, dict) else {},
                )
            )
        return items

    def _dedupe_items(self, items: List[EvidenceItem]) -> List[EvidenceItem]:
        seen = set()
        deduped: List[EvidenceItem] = []

        for item in sorted(items, key=lambda x: x.score, reverse=True):
            key = self._normalize_text(item.content)
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(item)
            if len(deduped) >= 5:
                break

        return deduped

    def _build_highlights(self, items: List[EvidenceItem]) -> List[str]:
        highlights: List[str] = []
        for item in items[:3]:
            sent = self._first_sentence(item.content)
            if sent and sent not in highlights:
                highlights.append(sent)
        return highlights

    def _confidence(self, items: List[EvidenceItem]) -> float:
        if not items:
            return 0.0
        top_scores = [max(0.0, min(1.0, i.score)) for i in items[:3]]
        return round(sum(top_scores) / len(top_scores), 3)

    def _first_sentence(self, text: str) -> str:
        chunks = re.split(r"[。！？!?]", text)
        for chunk in chunks:
            clean = chunk.strip()
            if clean:
                return clean[:80]
        return text[:80].strip()

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", "", text or "").lower()[:220]

    def _safe_score(self, score: Any) -> float:
        try:
            return float(score)
        except (ValueError, TypeError) as exc:
            logger.debug("Invalid score value: %r -> using 0.0", score)
            return 0.0
