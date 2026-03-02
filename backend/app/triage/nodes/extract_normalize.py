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
    "非常疼": "high",
    "疼得厉害": "high",
    "明显": "medium",
    "轻微": "low",
    "一点": "low",
    "不太疼": "low",
}

PROGRESSION_PATTERNS = {
    "逐渐加重": "progressive_worse",
    "越来越": "progressive_worse",
    "加重": "worse",
    "突然": "sudden",
    "突发": "sudden",
}

TRIGGER_PATTERNS = [
    "通风差",
    "不通风",
    "空气不好",
    "装修",
    "粉尘",
    "烟味",
    "受凉",
    "熬夜",
    "运动后",
    "进食后",
]

SCENE_PATTERNS = [
    "晚上",
    "夜间",
    "卧室",
    "开空调",
    "室内",
    "户外",
]

SYMPTOM_NORMALIZATION = {
    "喉咙疼": "咽痛",
    "喉咙痛": "咽痛",
    "嗓子疼": "咽痛",
    "嗓子痛": "咽痛",
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


def _extract_progression(text: str) -> str:
    for kw, value in PROGRESSION_PATTERNS.items():
        if kw in text:
            return value
    return ""


def _extract_tokens(text: str, candidates: list[str]) -> list[str]:
    out = []
    for token in candidates:
        if token in text and token not in out:
            out.append(token)
    return out


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("extract_normalize")
    state["node_trace"] = trace

    text = state.get("last_user_message", "")
    slots = state.get("symptom_slots", {})

    symptoms = slots.get("symptoms", [])
    for kw in extract_symptom_keywords(text):
        kw = SYMPTOM_NORMALIZATION.get(kw, kw)
        if kw not in symptoms:
            symptoms.append(kw)
    if ("喉咙" in text or "嗓子" in text) and ("疼" in text or "痛" in text):
        if "咽痛" not in symptoms:
            symptoms.append("咽痛")
    slots["symptoms"] = symptoms

    if not slots.get("duration"):
        duration = _extract_duration(text)
        if duration:
            slots["duration"] = duration

    if not slots.get("severity"):
        severity = _extract_severity(text)
        if severity:
            slots["severity"] = severity

    if not slots.get("progression"):
        progression = _extract_progression(text)
        if progression:
            slots["progression"] = progression

    triggers = list(slots.get("triggers", []))
    for token in _extract_tokens(text, TRIGGER_PATTERNS):
        if token not in triggers:
            triggers.append(token)
    if triggers:
        slots["triggers"] = triggers

    scene = list(slots.get("scene", []))
    for token in _extract_tokens(text, SCENE_PATTERNS):
        if token not in scene:
            scene.append(token)
    if scene:
        slots["scene"] = scene

    # very lightweight accompanying symptom detection
    if "伴" in text or "还有" in text or "并且" in text:
        slots["accompanying_symptoms"] = text[:120]

    state["symptom_slots"] = slots
    state["progress"] = max(state.get("progress", 0), 35)
    return state
