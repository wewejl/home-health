"""Main consult agent orchestrator (model-led, non-workflow)."""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from ..config import get_settings
from ..schemas.agent_response import AgentResponse
from ..services.llm_provider import LLMProvider
from .prompts import CONSULT_TURN_SYSTEM_PROMPT, CONSULT_TURN_USER_TEMPLATE
from .subagents import RetrievalSubagent
from .types import ComposedReply, TurnPlan

logger = logging.getLogger(__name__)

# 模型上下文保留轮次（默认 14，可通过 AGENTIC_MODEL_CONTEXT_MESSAGES 覆盖）
DEFAULT_MODEL_CONTEXT_MESSAGES = 14


class AgenticConsultOrchestrator:
    """主智能体 + 单检索子智能体的问诊引擎。"""

    def __init__(self):
        self._settings = get_settings()
        self._llm = LLMProvider.get_llm()
        self._retrieval_subagent = RetrievalSubagent()

    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        **kwargs,
    ) -> AgentResponse:
        _ = attachments
        _ = action

        base_state = dict(state or {})
        session_id = base_state.get("session_id") or kwargs.get("session_id", "")
        user_id = base_state.get("user_id") or kwargs.get("user_id", 0)
        agent_type = (base_state.get("agent_type") or kwargs.get("agent_type") or "general").lower()
        specialty = self._normalize_specialty(agent_type)

        messages = self._coerce_messages(base_state.get("messages", []))
        if user_input:
            # 验证并清理用户输入
            user_input = self._sanitize_user_input(user_input)
            messages.append({"type": "human", "content": user_input})

        context_messages = self._slice_context(messages)
        model_messages = self._model_context(context_messages)
        conversation_text = self._conversation_text(model_messages)
        last_user_message = user_input or self._last_human_message(messages)
        # 使用配置的最大检索查询长度（默认 200）
        max_query_len = int(self._settings.AGENTIC_MAX_QUERY_LENGTH or 200)
        retrieval_query = (last_user_message or "").strip()[:max_query_len]
        turn_index = int(base_state.get("turn_index", 0)) + (1 if user_input else 0)

        evidence = await self._retrieval_subagent.run(
            conversation_text=conversation_text,
            last_user_message=last_user_message,
            specialty=specialty,
            query_hint=retrieval_query,
            top_k=5,
        )

        reply = await self._compose_turn(
            specialty=specialty,
            conversation_text=conversation_text,
            last_user_message=last_user_message,
            turn_index=turn_index,
            evidence=evidence.model_dump(),
        )

        message = (reply.message or "").strip() or "我理解您的担心，请再补充一点信息，我会继续帮您判断。"
        if reply.mode == "ask" and "？" not in message and "?" not in message:
            ask_tail = (reply.next_question or "您这次不适是突然出现还是逐渐加重").strip("。.!！?？")
            message = f"{message} {ask_tail}？".strip()
        risk_level = reply.risk_level or "low"
        plan = self._plan_from_reply(reply, retrieval_query)
        quick_options = reply.quick_options or plan.quick_options
        disposition = reply.disposition

        # keep full session conversation context in next_state
        messages.append({"type": "ai", "content": message})
        stage, progress = self._resolve_stage(plan.next_step, risk_level, turn_index)

        next_state = dict(base_state)
        next_state.update(
            {
                "session_id": session_id,
                "user_id": user_id,
                "agent_type": agent_type,
                "agentic_engine": True,
                "messages": messages,
                "last_user_message": last_user_message,
                "turn_index": turn_index,
                "stage": stage,
                "progress": progress,
                "risk_level": risk_level,
                "disposition": disposition,
                "quick_options": quick_options,
                "current_response": message,
                "agentic_last_plan": plan.model_dump(),
                "agentic_last_evidence": evidence.model_dump(),
            }
        )

        debug_mode = bool(kwargs.get("debug", False))
        if debug_mode:
            next_state["agentic_debug"] = {
                "conversation_for_model": conversation_text,
                "plan": plan.model_dump(),
                "evidence": evidence.model_dump(),
            }

        if on_chunk and message:
            # 使用配置的 SSE 分块大小（默认 12）
            chunk_size = int(self._settings.AGENTIC_STREAM_CHUNK_SIZE or 12)
            for i in range(0, len(message), chunk_size):
                await on_chunk(message[i:i + chunk_size])

        specialty_data = {
            "agentic": {
                "mode": plan.next_step,
                "needs_retrieval": True,
                "retrieval_query": retrieval_query,
                "evidence_count": evidence.count,
                "evidence_confidence": evidence.confidence,
                "evidence_highlights": evidence.highlights,
                "evidence_summary": evidence.summary,
                "rationale": plan.brief_rationale,
                "disposition": disposition,
                "red_flags": reply.red_flags,
            }
        }
        if debug_mode:
            specialty_data["agentic"]["evidence_items"] = [item.model_dump() for item in evidence.items]

        return AgentResponse(
            message=message,
            stage=stage,
            progress=progress,
            quick_options=quick_options,
            risk_level=risk_level,
            specialty_data=specialty_data,
            next_state=next_state,
            current_thought=None,
            reasoning_history=[],
            show_thinking=False,
        )

    async def _compose_turn(
        self,
        specialty: str,
        conversation_text: str,
        last_user_message: str,
        turn_index: int,
        evidence: Dict[str, Any],
    ) -> ComposedReply:
        evidence_summary = evidence.get("summary", "") or "暂无高质量证据，基于症状进行初步判断。"
        evidence_items = self._format_evidence_items(evidence.get("items", []))
        prompt = CONSULT_TURN_USER_TEMPLATE.format(
            specialty=specialty,
            turn_index=turn_index,
            conversation=conversation_text or "（暂无历史）",
            last_user_message=last_user_message or "（为空）",
            evidence_summary=evidence_summary,
            evidence_items=evidence_items,
        )
        max_tokens = min(int(self._settings.LLM_MAX_TOKENS or 1500), 700)
        call_timeout = min(int(self._settings.LLM_TIMEOUT or 30), 20)
        composer = self._llm.bind(max_tokens=max_tokens, timeout=call_timeout).with_structured_output(ComposedReply)

        try:
            return await composer.ainvoke(f"{CONSULT_TURN_SYSTEM_PROMPT}\n\n{prompt}")
        except Exception as exc:
            logger.error(
                "LLM compose turn failed: specialty=%s turn_index=%s error=%s",
                specialty, turn_index, exc
            )
            raise RuntimeError(f"agentic compose turn failed for {specialty}") from exc

    def _plan_from_reply(self, reply: ComposedReply, retrieval_query: str) -> TurnPlan:
        next_step = reply.mode if reply.mode in {"ask", "assess", "advise", "emergency"} else "ask"
        return TurnPlan(
            needs_retrieval=True,
            retrieval_query=retrieval_query,
            next_step=next_step,
            brief_rationale=reply.brief_rationale,
            next_question=reply.next_question,
            quick_options=reply.quick_options,
            risk_level=reply.risk_level,
        )

    def _resolve_stage(self, next_step: str, risk_level: str, turn_index: int) -> tuple[str, int]:
        if risk_level == "emergency":
            return "diagnosing", 100
        if next_step == "ask":
            progress = min(75, 25 + turn_index * 12)
            return "collecting", progress
        progress = min(100, 70 + turn_index * 8)
        return "diagnosing", progress

    def _normalize_specialty(self, agent_type: str) -> str:
        if not agent_type:
            return "general"
        return agent_type.strip().lower()

    def _sanitize_user_input(self, user_input: Any) -> str:
        """验证并清理用户输入，防止提示注入。"""
        # 转换为字符串并清理
        text = str(user_input or "").strip()
        # 限制最大长度
        max_len = int(self._settings.AGENTIC_MAX_USER_INPUT_LENGTH or 5000)
        text = text[:max_len]
        # 移除可能的系统提示注入模式
        dangerous_patterns = ["<system>", "<|system|>", "[SYSTEM]", "You are now"]
        for pattern in dangerous_patterns:
            if pattern in text:
                logger.warning("Potentially malicious input pattern detected: %s", pattern)
                text = text.replace(pattern, "")
        if not text:
            raise ValueError("user_input cannot be empty after sanitization")
        return text

    def _coerce_messages(self, messages: Any) -> List[Dict[str, str]]:
        if not isinstance(messages, list):
            return []

        normalized: List[Dict[str, str]] = []
        for item in messages:
            if not isinstance(item, dict):
                continue
            role = (item.get("type") or item.get("role") or item.get("sender") or "").lower()
            if role in {"user", "human"}:
                msg_type = "human"
            elif role in {"assistant", "ai", "bot"}:
                msg_type = "ai"
            else:
                continue
            content = str(item.get("content") or "").strip()
            if not content:
                continue
            normalized.append({"type": msg_type, "content": content})
        return normalized

    def _slice_context(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        limit = int(self._settings.AGENTIC_MAX_CONTEXT_TURNS or 0)
        if limit > 0 and len(messages) > limit:
            return messages[-limit:]
        return messages

    def _model_context(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        limit = int(self._settings.AGENTIC_MODEL_CONTEXT_MESSAGES or DEFAULT_MODEL_CONTEXT_MESSAGES)
        if len(messages) <= limit:
            return messages
        return messages[-limit:]

    def _conversation_text(self, messages: List[Dict[str, str]]) -> str:
        lines: List[str] = []
        for msg in messages:
            role = "用户" if msg.get("type") == "human" else "医生助手"
            lines.append(f"{role}：{msg.get('content', '')}")
        return "\n".join(lines)

    def _last_human_message(self, messages: List[Dict[str, str]]) -> str:
        for msg in reversed(messages):
            if msg.get("type") == "human":
                return msg.get("content", "")
        return ""

    def _format_evidence_items(self, items: List[Dict[str, Any]]) -> str:
        if not items:
            return "- 暂无检索片段"
        lines = []
        for idx, row in enumerate(items[:3], start=1):
            content = str(row.get("content") or "").replace("\n", " ").strip()
            score = row.get("score", 0.0)
            lines.append(f"- E{idx}({score:.2f}) {content[:120]}")
        return "\n".join(lines)
