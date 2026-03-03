"""Main agent orchestration: retrieval subagent + LLM composer."""

from __future__ import annotations

import time
from typing import List

from .knowledge import RetrievalSubagent
from .llm import LLMClient
from .models import (
    ChatRespondRequest,
    ChatRespondResponse,
    Citation,
    ErrorObject,
    MemoryPatch,
    RespondMetrics,
    ToolTraceItem,
    TurnDraft,
)


class ConsultAgentService:
    """Single-turn response service for /v1/chat/respond."""

    def __init__(self):
        self._retrieval = RetrievalSubagent()
        self._llm = LLMClient()

    async def respond(self, payload: ChatRespondRequest) -> ChatRespondResponse:
        started = time.perf_counter()
        tool_trace: List[ToolTraceItem] = []
        citations: List[Citation] = []
        tools_ms = 0
        llm_ms = 0
        llm_error: ErrorObject | None = None

        history_lines = self._history_lines(payload.history)

        retrieval_started = time.perf_counter()
        evidence = await self._retrieval.run(
            user_message=payload.user_message,
            history_lines=history_lines,
            specialty=payload.agent_type,
        )
        retrieval_latency_ms = int((time.perf_counter() - retrieval_started) * 1000)
        tools_ms += retrieval_latency_ms
        tool_trace.append(
            ToolTraceItem(
                name="subagent.retrieval",
                status="degraded" if evidence.error else "ok",
                latency_ms=retrieval_latency_ms,
            )
        )
        citations = [
            Citation(
                id=f"E{idx}",
                source="kb",
                snippet=self._citation_snippet(item),
            )
            for idx, item in enumerate(evidence.items[:3], start=1)
        ]

        llm_started = time.perf_counter()
        model_calls = 1
        try:
            draft = await self._llm.compose_turn(
                specialty=payload.agent_type,
                locale=payload.locale,
                user_message=payload.user_message,
                history=history_lines,
                evidence_items=evidence.items,
            )
            llm_status = "ok"
        except Exception:  # noqa: BLE001
            draft = TurnDraft(
                assistant_message="AI 服务暂时不可用，请稍后重试。",
                risk_level="low",
                quick_options=[],
                memory_patch=MemoryPatch(),
            )
            llm_error = ErrorObject(
                code="AI_INTERNAL_ERROR",
                message="upstream model request failed",
                retryable=True,
            )
            llm_status = "degraded"

        llm_latency_ms = int((time.perf_counter() - llm_started) * 1000)
        llm_ms += llm_latency_ms
        tool_trace.append(
            ToolTraceItem(
                name="llm.compose",
                status=llm_status,  # type: ignore[arg-type]
                latency_ms=llm_latency_ms,
            )
        )

        total_ms = int((time.perf_counter() - started) * 1000)
        metrics = RespondMetrics(
            total_ms=total_ms,
            llm_ms=llm_ms,
            tools_ms=tools_ms,
            model_calls=model_calls,
        )

        return ChatRespondResponse(
            request_id=payload.request_id,
            session_id=payload.session_id,
            turn_index=payload.turn_index,
            assistant_message=draft.assistant_message,
            risk_level=draft.risk_level,
            quick_options=draft.quick_options[:3],
            memory_patch=draft.memory_patch,
            citations=citations,
            tool_trace=tool_trace,
            metrics=metrics,
            error=llm_error,
        )

    def _history_lines(self, history) -> List[str]:
        lines = []
        for row in history:
            role = "用户" if row.role == "user" else ("助手" if row.role == "assistant" else "系统")
            lines.append(f"{role}：{row.content}")
        return lines

    def _citation_snippet(self, item) -> str:
        specialty_labels = {
            "otorhinolaryngology": "耳鼻喉科",
            "respiratory": "呼吸科",
            "cardiology": "心血管科",
            "gastroenterology": "消化科",
            "dermatology": "皮肤科",
            "neurology": "神经内科",
            "orthopedics": "骨科",
            "endocrinology": "内分泌科",
            "pediatrics": "儿科",
            "obstetrics_gynecology": "妇产科",
            "ophthalmology": "眼科",
        }
        specialty = ""
        if isinstance(item.metadata, dict):
            specialty = str(item.metadata.get("specialty") or "").strip().lower()
        label = specialty_labels.get(specialty, "")
        body = item.content[:110]
        if label:
            return f"[{label}] {body}"
        return body
