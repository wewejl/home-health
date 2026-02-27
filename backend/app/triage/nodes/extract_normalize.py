"""Extraction/normalization node."""
import re
from typing import Dict, Any
from ..policy import extract_symptom_keywords


DURATION_PATTERNS = [
    r"(\d+\s*天)",
    r"(\d+\s*周)",
    r"(\d+\s*月)",
    r"(\d+\s*小时)",
    r"([一二三四五六七八九十两半]+\s*天)",
    r"([一二三四五六七八九十两半]+\s*周)",
    r"([一二三四五六七八九十两半]+\s*月)",
    r"(几天|几周|几个月|一段时间)",
    r"(今天|昨天|前天|刚刚|最近)",
]

SEVERITY_KEYWORDS = {
    "严重": "high",
    "剧烈": "high",
    "明显": "medium",
    "轻微": "low",
    "一点": "low",
}


def _extract_duration(text: str) -> str:
    for pattern in DURATION_PATTERNS:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return ""


def _extract_severity(text: str) -> str:
    for kw, level in SEVERITY_KEYWORDS.items():
        if kw in text:
            return level
    return ""


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("extract_normalize")
    state["node_trace"] = trace

    text = state.get("last_user_message", "")
    slots = state.get("symptom_slots", {})

    symptoms = slots.get("symptoms", [])
    for kw in extract_symptom_keywords(text):
        if kw not in symptoms:
            symptoms.append(kw)
    slots["symptoms"] = symptoms

    if not slots.get("duration"):
        duration = _extract_duration(text)
        if duration:
            slots["duration"] = duration

    if not slots.get("severity"):
        severity = _extract_severity(text)
        if severity:
            slots["severity"] = severity

    # very lightweight accompanying symptom detection
    if "伴" in text or "还有" in text:
        slots["accompanying_symptoms"] = text[:120]

    state["symptom_slots"] = slots
    state["progress"] = max(state.get("progress", 0), 35)
    return state
