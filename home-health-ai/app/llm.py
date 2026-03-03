"""LLM client for main consult agent response generation."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Iterable, List

import httpx

from .config import get_settings
from .models import EvidenceItem, MemoryPatch, RiskLevel, TurnDraft


SYSTEM_PROMPT = """
你是“灵犀健康”问诊主智能体。目标是进行自然、连续、稳定的医疗问询与解释，避免机械化流程感。
要求：
1) 先共情再判断，语气专业且简洁，不输出“思考过程/推理链/深度思考”。
2) 若信息不足，优先只追问一个最关键的问题，并给 0-3 个可选项。
3) 若信息已足够，给出清晰判断方向与下一步建议（家庭处理 + 何时就医）。
4) 只基于已知信息和证据，不要臆造检查结果或结论。
5) 输出必须是 JSON，对象字段：
{
  "assistant_message": "字符串",
  "risk_level": "low|medium|high|emergency",
  "quick_options": ["字符串", "...最多3个"],
  "memory_patch": {
    "facts": ["本轮抽取的关键事实，最多6条"],
    "summary_delta": "本轮摘要增量",
    "profile_delta": {}
  }
}
""".strip()


class LLMClient:
    """OpenAI-compatible chat completions client."""

    async def compose_turn(
        self,
        *,
        specialty: str,
        locale: str,
        user_message: str,
        history: List[str],
        evidence_items: List[EvidenceItem],
    ) -> TurnDraft:
        settings = get_settings()
        if not settings.LLM_API_KEY:
            raise RuntimeError("LLM_API_KEY not configured")

        endpoint = f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": settings.LLM_MODEL,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": self._build_user_prompt(
                        specialty=specialty,
                        locale=locale,
                        user_message=user_message,
                        history=history,
                        evidence_items=evidence_items,
                    ),
                },
            ],
        }

        retries = max(0, int(settings.LLM_MAX_RETRIES))
        last_err: Exception | None = None
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
                    resp = await client.post(endpoint, headers=headers, json=body)
                    resp.raise_for_status()
                    payload = resp.json()
                raw_text = self._extract_text(payload)
                parsed = self._parse_json(raw_text)
                return self._to_turn_draft(parsed)
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                if attempt < retries:
                    await asyncio.sleep(0.25 * (attempt + 1))
                    continue
                break

        raise RuntimeError(f"llm compose failed: {last_err}")

    def _build_user_prompt(
        self,
        *,
        specialty: str,
        locale: str,
        user_message: str,
        history: List[str],
        evidence_items: List[EvidenceItem],
    ) -> str:
        history_text = "\n".join(history[-12:]) if history else "（暂无历史）"
        evidence_lines = self._format_evidence(evidence_items)
        return (
            f"专科: {specialty or 'general'}\n"
            f"语言/地区: {locale or 'zh-CN'}\n\n"
            f"用户本轮输入:\n{user_message.strip()}\n\n"
            f"最近对话:\n{history_text}\n\n"
            f"检索证据:\n{evidence_lines}\n\n"
            "请仅输出 JSON。"
        )

    def _format_evidence(self, evidence_items: List[EvidenceItem]) -> str:
        if not evidence_items:
            return "- 暂无检索证据"
        rows = []
        for idx, item in enumerate(evidence_items[:3], start=1):
            rows.append(f"- E{idx}({item.score:.2f}) {item.content[:180]}")
        return "\n".join(rows)

    def _extract_text(self, payload: Dict[str, Any]) -> str:
        choices = payload.get("choices") or []
        if not choices:
            raise ValueError("empty choices")
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
        raise ValueError("invalid content type")

    def _parse_json(self, text: str) -> Dict[str, Any]:
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

        raise ValueError("model output is not valid JSON object")

    def _to_turn_draft(self, data: Dict[str, Any]) -> TurnDraft:
        assistant_message = str(data.get("assistant_message") or "").strip()
        if not assistant_message:
            raise ValueError("assistant_message missing in model output")

        risk_level = self._to_risk_level(data.get("risk_level"))

        quick_options = data.get("quick_options") or []
        if not isinstance(quick_options, list):
            quick_options = []
        quick_options = [str(item).strip() for item in quick_options if str(item).strip()][:3]

        memory_data = data.get("memory_patch") or {}
        facts = memory_data.get("facts") or []
        if not isinstance(facts, list):
            facts = []
        facts = [str(item).strip() for item in facts if str(item).strip()][:6]
        summary_delta = str(memory_data.get("summary_delta") or "").strip()
        profile_delta = memory_data.get("profile_delta") or {}
        if not isinstance(profile_delta, dict):
            profile_delta = {}

        return TurnDraft(
            assistant_message=assistant_message,
            risk_level=risk_level,
            quick_options=quick_options,
            memory_patch=MemoryPatch(
                facts=facts,
                summary_delta=summary_delta,
                profile_delta=profile_delta,
            ),
        )

    def _to_risk_level(self, value: Any) -> RiskLevel:
        risk = str(value or "").strip().lower()
        if risk in {"low", "medium", "high", "emergency"}:
            return risk  # type: ignore[return-value]
        raise ValueError("risk_level missing or invalid")
