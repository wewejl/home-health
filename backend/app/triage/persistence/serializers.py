"""Serialization helpers for triage state persistence."""
from __future__ import annotations

from typing import Any, Dict


def sanitize_state_for_db(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return JSON-safe state payload for session.agent_state.

    Current triage state is already dict/list/primitive, this function remains
    as a dedicated compatibility hook for future non-JSON objects.
    """
    sanitized: Dict[str, Any] = {}
    for k, v in state.items():
        if _json_safe(v):
            sanitized[k] = v
        else:
            sanitized[k] = str(v)
    return sanitized


def _json_safe(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_json_safe(i) for i in value)
    if isinstance(value, dict):
        return all(isinstance(k, str) and _json_safe(v) for k, v in value.items())
    return False
