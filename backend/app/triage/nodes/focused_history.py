"""Focused history collection node."""
from typing import Dict, Any
from ..policy import get_required_slots
from ..specialty import get_specialty_pack


SLOT_QUESTION_MAP = {
    "duration": (
        "这个不适大概持续了多久？是突然出现还是逐步加重的？",
        ["前天开始，逐步加重", "今天突然出现", "已经反复一周以上"],
    ),
    "severity": (
        "目前严重程度大概是轻度、中度还是重度？是否影响吃饭、说话或睡眠？",
        ["轻度，不太影响", "中度，已经影响生活", "重度，明显影响睡眠/进食"],
    ),
    "accompanying_symptoms": (
        "除了当前主要不适，还有没有伴随症状？比如发热、咳嗽、鼻塞、呼吸不畅等。",
        ["只有喉咙不适", "有鼻塞流涕/咳嗽", "有发热或呼吸困难"],
    ),
    "temperature": (
        "有发热吗？最高体温大约多少？",
        ["没有发热", "低热（37.3-38℃）", "高热（≥38.5℃）"],
    ),
    "sputum": (
        "如果有咳嗽，痰液情况如何（无痰、白痰、黄痰、血痰）？",
        ["无痰", "白痰", "黄痰或痰中带血"],
    ),
    "chest_pain_character": (
        "胸痛更像压榨痛、刀割样痛还是针刺样痛？会向左肩/下颌放射吗？",
        ["压榨痛，可能放射", "刺痛，不放射", "说不清楚"],
    ),
    "activity_relation": (
        "症状和活动有关系吗？比如活动后更重、休息后缓解？",
        ["活动后明显加重", "与活动关系不大", "休息后可缓解"],
    ),
    "skin_location": (
        "皮损主要分布在哪些部位？是否对称？",
        ["面部", "四肢/躯干", "全身多处"],
    ),
    "itch_or_pain": (
        "以瘙痒为主还是疼痛/灼痛为主？",
        ["以瘙痒为主", "以疼痛灼痛为主", "两者都有"],
    ),
}


def _build_followup(missing_slots: list[str], pack) -> tuple[str, list[str]]:
    if not missing_slots:
        return "", []

    primary = missing_slots[0]
    if primary in SLOT_QUESTION_MAP:
        question, options = SLOT_QUESTION_MAP[primary]
        return question, options

    fallback = pack.followup_questions[0] if pack.followup_questions else "请再补充一下症状细节。"
    return fallback, pack.followup_questions[:3]


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("focused_history")
    state["node_trace"] = trace

    specialty = state.get("specialty", "general")
    pack = get_specialty_pack(specialty)
    required_slots = get_required_slots(specialty)
    symptom_slots = state.get("symptom_slots", {})

    missing = [slot for slot in required_slots if not symptom_slots.get(slot)]
    state["missing_slots"] = missing
    if missing:
        next_question, quick_options = _build_followup(missing, pack)
        state["next_question"] = next_question
        state["quick_options"] = quick_options
    else:
        state["next_question"] = ""
    state["stage"] = "collecting" if missing else "analyzing"
    state["progress"] = max(state.get("progress", 0), 25)
    return state
