"""Mappers between backend session models and AI gateway schemas."""

from __future__ import annotations

from typing import Any, Iterable, List

from ...schemas.ai_gateway import ChatMessage, ChatRespondRequest


def build_history_from_db_messages(messages: Iterable[Any], limit: int = 20) -> List[ChatMessage]:
    """Convert DB message rows into transport history messages."""
    rows = list(messages)
    if limit > 0 and len(rows) > limit:
        rows = rows[-limit:]

    history: List[ChatMessage] = []
    for item in rows:
        sender = str(getattr(item, "sender", "")).lower()
        if sender.endswith(".user") or sender == "user":
            role = "user"
        elif sender.endswith(".ai") or sender == "ai":
            role = "assistant"
        else:
            continue

        content = str(getattr(item, "content", "") or "").strip()
        if not content:
            continue
        history.append(ChatMessage(role=role, content=content))
    return history


def build_chat_respond_request(
    *,
    request_id: str,
    session_id: str,
    turn_index: int,
    user_id: str,
    agent_type: str,
    user_message: str,
    history: List[ChatMessage],
    attachments: List[dict] | None = None,
    locale: str = "zh-CN",
    stream: bool = False,
    timezone: str | None = None,
    channel: str | None = None,
    debug: bool = False,
) -> ChatRespondRequest:
    """Build a validated gateway request payload."""
    client_context = {}
    if timezone:
        client_context["timezone"] = timezone
    if channel:
        client_context["channel"] = channel

    return ChatRespondRequest(
        request_id=request_id,
        session_id=session_id,
        turn_index=turn_index,
        user_id=user_id,
        agent_type=agent_type,
        locale=locale or "zh-CN",
        stream=bool(stream),
        user_message=user_message,
        history=history,
        attachments=attachments or [],
        client_context=client_context or None,
        debug=bool(debug),
    )

