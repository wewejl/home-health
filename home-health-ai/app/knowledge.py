"""Knowledge retrieval subagent."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict, List, Set, Tuple

import httpx

from .config import get_settings
from .models import EvidenceBundle, EvidenceItem


SPECIALTY_ALIASES: Dict[str, str] = {
    "ent": "otorhinolaryngology",
    "otolaryngology": "otorhinolaryngology",
    "ear_nose_throat": "otorhinolaryngology",
}

NON_GENERAL_SPECIALTIES: Tuple[str, ...] = (
    "otorhinolaryngology",
    "respiratory",
    "cardiology",
    "gastroenterology",
    "dermatology",
    "neurology",
    "orthopedics",
    "endocrinology",
    "pediatrics",
    "obstetrics_gynecology",
    "ophthalmology",
)

SUPPORTED_SPECIALTIES: Set[str] = set(NON_GENERAL_SPECIALTIES) | {"general"}


class RetrievalSubagent:
    """Retrieve evidence from medical knowledge service."""

    async def run(
        self,
        *,
        user_message: str,
        history_lines: List[str],
        specialty: str,
        top_k: int | None = None,
    ) -> EvidenceBundle:
        settings = get_settings()
        query = self._build_query(user_message=user_message, history_lines=history_lines)
        if not query:
            return EvidenceBundle(query_used="", items=[], error="empty query")

        limit = max(1, int(top_k or settings.KNOWLEDGE_TOP_K))
        requested_specialty = self._normalize_specialty(specialty)
        selected_specialties = await self._llm_select_specialties(
            query=query,
            requested_specialty=requested_specialty,
        )
        probe_scores: Dict[str, float] = {}

        async with httpx.AsyncClient(timeout=settings.KNOWLEDGE_SERVICE_TIMEOUT) as client:
            if not selected_specialties:
                probe_specialties = (
                    [requested_specialty]
                    if requested_specialty != "general"
                    else list(NON_GENERAL_SPECIALTIES)
                )
                probe_scores = await self._probe_scores(
                    client=client,
                    query=query,
                    specialties=probe_specialties,
                )
                selected_specialties = self._select_specialties(
                    requested_specialty=requested_specialty,
                    probe_scores=probe_scores,
                )
            if not selected_specialties:
                selected_specialties = ["general"]

            search_tasks = [
                self._search(
                    client=client,
                    query=query,
                    specialty=spec,
                    top_k=max(limit + 3, settings.KNOWLEDGE_TOP_K),
                )
                for spec in selected_specialties
            ]
            search_results = await asyncio.gather(*search_tasks)

            # Data-driven补查：首轮为空时，按工具分数再补查候选专科与general。
            if not any((row.get("results") or []) for row in search_results):
                backup_specialties = self._select_specialties(
                    requested_specialty=requested_specialty,
                    probe_scores=probe_scores,
                )
                if "general" not in backup_specialties:
                    backup_specialties.append("general")
                backup_specialties = [sp for sp in backup_specialties if sp not in selected_specialties][:3]
                if backup_specialties:
                    backup_tasks = [
                        self._search(
                            client=client,
                            query=query,
                            specialty=spec,
                            top_k=max(limit + 3, settings.KNOWLEDGE_TOP_K),
                        )
                        for spec in backup_specialties
                    ]
                    backup_results = await asyncio.gather(*backup_tasks)
                    selected_specialties.extend(backup_specialties)
                    search_results.extend(backup_results)

        merged_items: List[EvidenceItem] = []
        errors: List[str] = []
        specialty_strength: Dict[str, float] = {}
        query_used = query
        for spec, data in zip(selected_specialties, search_results):
            if data.get("error"):
                errors.append(str(data["error"]))
                continue

            query_used = str(data.get("query") or query)
            raw_results = data.get("results", []) or []
            if not raw_results:
                continue

            # preserve strongest score per searched specialty
            best = 0.0
            for row in raw_results[:3]:
                if isinstance(row, dict):
                    best = max(best, self._safe_float(row.get("score", 0.0)))
            specialty_strength[spec] = max(specialty_strength.get(spec, 0.0), best)
            merged_items.extend(self._normalize_items(raw_results, default_specialty=spec))

        if not merged_items:
            return EvidenceBundle(
                query_used=query_used,
                items=[],
                error=(errors[0][:180] if errors else None),
            )

        query_terms = self._extract_query_terms(query)
        ranked_items = self._rerank(
            items=merged_items,
            query_terms=query_terms,
            specialty_strength=specialty_strength or probe_scores,
            selected_specialties=selected_specialties,
        )
        if not ranked_items:
            ranked_items = merged_items
        return EvidenceBundle(query_used=query_used, items=ranked_items[:limit], error=None)

    async def _llm_select_specialties(
        self,
        *,
        query: str,
        requested_specialty: str,
    ) -> List[str]:
        if requested_specialty != "general":
            return [requested_specialty]

        settings = get_settings()
        if not settings.LLM_API_KEY:
            return []

        endpoint = f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json",
        }

        specialty_list = ", ".join(NON_GENERAL_SPECIALTIES)
        prompt = (
            "你是检索路由子智能体。根据用户问题选择最相关的 1-2 个专科。\n"
            f"可选专科: {specialty_list}\n"
            "只输出 JSON: {\"specialties\": [\"...\"]}\n"
            f"用户问题: {query}"
        )
        body = {
            "model": settings.LLM_MODEL,
            "temperature": 0,
            "max_tokens": 120,
            "messages": [
                {"role": "system", "content": "只返回严格 JSON，不要解释。"},
                {"role": "user", "content": prompt},
            ],
        }

        try:
            timeout_s = max(5, min(int(settings.LLM_TIMEOUT), 12))
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                resp = await client.post(endpoint, headers=headers, json=body)
                resp.raise_for_status()
                payload = resp.json() or {}
            text = self._extract_llm_text(payload)
            data = self._parse_json_object(text)
            specs = data.get("specialties") or []
            if not isinstance(specs, list):
                return []
            selected: List[str] = []
            for raw in specs:
                spec = self._normalize_specialty(str(raw))
                if spec == "general":
                    continue
                if spec in NON_GENERAL_SPECIALTIES and spec not in selected:
                    selected.append(spec)
                if len(selected) >= 2:
                    break
            return selected
        except Exception:
            return []

    async def _probe_scores(
        self,
        *,
        client: httpx.AsyncClient,
        query: str,
        specialties: List[str],
    ) -> Dict[str, float]:
        tasks = [
            self._search(client=client, query=query, specialty=spec, top_k=1)
            for spec in specialties
        ]
        rows = await asyncio.gather(*tasks)

        scores: Dict[str, float] = {}
        for spec, data in zip(specialties, rows):
            if data.get("error"):
                continue
            raw_results = data.get("results", []) or []
            if not raw_results:
                continue

            best = 0.0
            for raw in raw_results[:2]:
                if isinstance(raw, dict):
                    best = max(best, self._safe_float(raw.get("score", 0.0)))
            if best > 0:
                scores[spec] = best
        return scores

    def _select_specialties(
        self,
        *,
        requested_specialty: str,
        probe_scores: Dict[str, float],
    ) -> List[str]:
        if requested_specialty != "general":
            return [requested_specialty]

        ranked = sorted(probe_scores.items(), key=lambda row: row[1], reverse=True)
        if not ranked:
            return ["general"]

        top_score = ranked[0][1]
        if top_score <= 0:
            return ["general"]

        selected: List[str] = []
        dynamic_cutoff = max(0.02, top_score * 0.65)
        for spec, score in ranked:
            if score < dynamic_cutoff:
                continue
            selected.append(spec)
            if len(selected) >= 3:
                break

        if not selected:
            for spec, score in ranked[:2]:
                if score > 0:
                    selected.append(spec)

        if not selected:
            return ["general"]

        if top_score < 0.1 and "general" not in selected:
            selected.append("general")
        return selected

    def _build_query(self, *, user_message: str, history_lines: List[str]) -> str:
        msg = (user_message or "").strip()
        if msg:
            return msg[:220]
        if history_lines:
            return history_lines[-1][:220]
        return ""

    async def _search(
        self,
        *,
        client: httpx.AsyncClient,
        query: str,
        specialty: str,
        top_k: int,
    ) -> Dict[str, Any]:
        settings = get_settings()
        payload = {
            "query": query,
            "specialty": specialty,
            "top_k": top_k,
            "score_threshold": 0.0,
        }
        headers = {"Content-Type": "application/json"}
        if settings.KNOWLEDGE_SERVICE_API_KEY:
            headers["X-API-Key"] = settings.KNOWLEDGE_SERVICE_API_KEY

        url = f"{settings.KNOWLEDGE_SERVICE_URL.rstrip('/')}/api/v1/search"
        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = (resp.json() or {}).get("data", {})
            return {
                "query": data.get("query") or query,
                "results": data.get("results") or [],
                "error": None,
            }
        except Exception as exc:
            return {"query": query, "results": [], "error": str(exc)[:180]}

    def _normalize_items(self, raw_results: List[Any], default_specialty: str) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        for raw in raw_results:
            if isinstance(raw, str):
                content = raw.strip()
                score = 0.0
                metadata: Dict[str, Any] = {"specialty": default_specialty}
            else:
                content = str(raw.get("content") or raw.get("chunk_text") or raw.get("text") or "").strip()
                score = self._safe_float(raw.get("score", 0.0))
                metadata = raw.get("metadata", {}) or {}
                specialty = str(raw.get("specialty") or "").strip().lower()
                if not isinstance(metadata, dict):
                    metadata = {}
                else:
                    metadata = dict(metadata)
                if specialty:
                    metadata.setdefault("specialty", specialty)
                else:
                    metadata.setdefault("specialty", default_specialty)

            if not content:
                continue
            flat_content = re.sub(r"\s+", " ", content).strip()
            if len(flat_content) > 260:
                flat_content = f"{flat_content[:260].rstrip()}…"
            items.append(EvidenceItem(content=flat_content, score=score, metadata=metadata))

        items.sort(key=lambda row: row.score, reverse=True)
        return items

    def _extract_query_terms(self, query: str) -> Set[str]:
        text = (query or "").lower()
        terms: Set[str] = set()

        for token in re.findall(r"[a-z0-9]{2,}", text):
            terms.add(token)

        for block in re.findall(r"[\u4e00-\u9fff]{2,}", text):
            if len(block) <= 5:
                terms.add(block)
            if len(block) == 2:
                terms.add(block)
                continue
            for idx in range(max(0, len(block) - 2)):
                terms.add(block[idx : idx + 3])

        return {term for term in terms if term}

    def _rerank(
        self,
        *,
        items: List[EvidenceItem],
        query_terms: Set[str],
        specialty_strength: Dict[str, float],
        selected_specialties: List[str],
    ) -> List[EvidenceItem]:
        selected_set = set(selected_specialties)
        ranked: List[Tuple[float, EvidenceItem]] = []
        seen: Set[str] = set()

        for item in items:
            text = self._item_text(item).lower()
            overlap = self._term_overlap(query_terms, text)
            item_specialty = self._normalize_specialty(
                str((item.metadata or {}).get("specialty") or "general")
            )
            specialty_score = specialty_strength.get(item_specialty, 0.0)
            final_score = float(item.score) + (0.08 * overlap) + (0.30 * specialty_score)

            if item_specialty == "general":
                keep = overlap > 0
            else:
                keep = overlap > 0 or (item_specialty in selected_set and item.score >= 0.16)
            if not keep:
                continue

            key = re.sub(r"\s+", "", item.content.lower())[:180]
            if key in seen:
                continue
            seen.add(key)
            ranked.append((final_score, item))

        ranked.sort(key=lambda row: row[0], reverse=True)
        return [row[1] for row in ranked]

    def _item_text(self, item: EvidenceItem) -> str:
        parts = [item.content]
        if isinstance(item.metadata, dict):
            for key in ("title", "disease", "summary", "source", "specialty"):
                val = item.metadata.get(key)
                if isinstance(val, str) and val.strip():
                    parts.append(val.strip())
        return " ".join(parts)

    def _term_overlap(self, query_terms: Set[str], text: str) -> int:
        if not query_terms:
            return 0
        return sum(1 for term in query_terms if term and term in text)

    def _extract_llm_text(self, payload: Dict[str, Any]) -> str:
        choices = payload.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            chunks: List[str] = []
            for chunk in content:
                if isinstance(chunk, dict) and chunk.get("type") == "text":
                    chunks.append(str(chunk.get("text") or ""))
            return "\n".join(chunks).strip()
        return ""

    def _parse_json_object(self, text: str) -> Dict[str, Any]:
        cleaned = (text or "").strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(cleaned[start : end + 1])
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return {}

    def _normalize_specialty(self, specialty: str | None) -> str:
        val = str(specialty or "general").strip().lower()
        val = SPECIALTY_ALIASES.get(val, val)
        if val in SUPPORTED_SPECIALTIES:
            return val
        return "general"

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0
