"""Policy and guardrails for triage flow."""
from typing import List
from .specialty import get_specialty_pack


EMERGENCY_KEYWORDS = [
    "胸痛", "呼吸困难", "意识模糊", "昏迷", "晕厥", "大出血", "抽搐", "濒死", "无法呼吸"
]

SYMPTOM_KEYWORDS = [
    "发热", "咳嗽", "咳痰", "胸痛", "胸闷", "心悸", "头痛", "头晕", "腹痛", "腹泻", "呕吐",
    "皮疹", "瘙痒", "红肿", "水疱", "咽痛", "喉咙痛", "喉咙疼", "嗓子疼", "嗓子痛",
    "乏力", "气短", "流涕", "鼻塞", "便血", "尿痛",
]

def infer_specialty(agent_type: str) -> str:
    """Infer triage specialty from agent type."""
    if not agent_type:
        return "general"
    normalized = agent_type.strip().lower()
    return normalized if normalized in {
        "general", "cardiology", "respiratory", "dermatology", "orthopedics", "neurology",
        "gastroenterology", "endocrinology", "ophthalmology", "otorhinolaryngology",
        "stomatology", "obstetrics_gynecology", "pediatrics",
    } else "general"


def detect_red_flags(text: str) -> List[str]:
    """Return matched emergency keywords from user text."""
    if not text:
        return []
    return [kw for kw in EMERGENCY_KEYWORDS if kw in text]


def extract_symptom_keywords(text: str) -> List[str]:
    """Extract symptom keywords from free text."""
    if not text:
        return []
    found = []
    for kw in SYMPTOM_KEYWORDS:
        if kw in text and kw not in found:
            found.append(kw)
    return found


def get_required_slots(specialty: str) -> List[str]:
    """Return required slots for current specialty."""
    return get_specialty_pack(specialty).required_slots
