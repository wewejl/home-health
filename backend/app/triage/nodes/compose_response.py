"""Response composition node."""
from typing import Dict, Any, List
from ..specialty import get_specialty_pack


def _render_evidence_points(evidence: List[Dict[str, Any]]) -> str:
    points = []
    for item in evidence[:2]:
        cid = item.get("citation_id", "E?")
        content = (item.get("content") or "").replace("\n", " ").strip()
        if content:
            points.append(f"- [{cid}] {content[:70]}...")
    return "\n".join(points)


def _render_differential_points(differentials: List[Dict[str, Any]]) -> str:
    points = []
    for item in differentials[:3]:
        name = item.get("name", "待评估")
        conf = float(item.get("confidence", 0.0))
        points.append(f"- {name}（置信度约 {int(conf * 100)}%）")
    return "\n".join(points) if points else "- 暂无明确方向，需继续补充病史。"


def _render_self_care(pack, slots: Dict[str, Any], specialty: str) -> List[str]:
    suggestions: List[str] = []
    if specialty in {"general", "respiratory"}:
        suggestions.extend([
            "保持室内通风，睡前也建议短时换气，避免烟味和刺激性气体。",
            "少量多次饮温水，避免辛辣、酒精和过烫食物刺激咽喉。",
        ])
        triggers = slots.get("triggers", [])
        if any(t in triggers for t in ["装修", "空气不好", "不通风", "通风差"]):
            suggestions.append("若怀疑空气刺激，优先离开可疑环境并观察 24 小时症状变化。")
    elif specialty == "cardiology":
        suggestions.extend([
            "暂时避免剧烈活动和情绪激动，保持安静休息。",
            "记录胸闷/胸痛发生时间、持续时长与诱因，便于线下医生判断。",
        ])
    else:
        suggestions.append(pack.disposition_advice.get("home", "可先进行基础对症处理并观察。"))
    return suggestions[:3]


def _render_warning_line(pack, risk: str) -> str:
    warning_text = "、".join(pack.warning_signals[:3]) if pack.warning_signals else "症状明显加重"
    if risk == "high":
        return f"若出现{warning_text}，建议立即前往急诊，不要继续等待。"
    return f"若出现{warning_text}，请立即急诊或拨打120。"


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("compose_response")
    state["node_trace"] = trace

    risk = state.get("risk_level", "low")
    disposition = state.get("disposition", "home")
    differentials = state.get("differentials", [])
    missing_slots = state.get("missing_slots", [])
    evidence_selected = state.get("evidence_selected", [])
    evidence_text = _render_evidence_points(evidence_selected)
    differential_text = _render_differential_points(differentials)
    pack = get_specialty_pack(state.get("specialty", "general"))
    next_question = state.get("next_question", "")
    slots = state.get("symptom_slots", {})
    specialty = state.get("specialty", "general")

    if risk == "emergency":
        state["current_response"] = (
            "根据您当前描述，存在紧急风险信号。请立即前往急诊或拨打120。"
            "在就医前尽量避免自行用药，并准备好症状发生时间与变化记录。"
        )
        state["quick_options"] = ["我现在去急诊", "急诊前还要注意什么"]
        state["stage"] = "diagnosing"

    elif missing_slots:
        missing_text = "、".join(missing_slots[:3])
        question_line = next_question or "请再补充上述关键信息，我会继续为您判断。"
        option_line = "；".join(state.get("quick_options", [])[:3])
        state["current_response"] = (
            f"我先帮您梳理到这里：当前还缺少关键信息（{missing_text}），"
            f"补齐后才能更准确判断是感染、过敏还是环境刺激。\n"
            f"下一步请先回答：{question_line}"
        )
        if option_line:
            state["current_response"] += f"\n可直接选：{option_line}"
        if not state.get("quick_options"):
            state["quick_options"] = pack.followup_questions[:3]
        state["stage"] = "collecting"

    else:
        top_name = differentials[0]["name"] if differentials else "待进一步评估"
        advice = pack.disposition_advice.get(disposition, "建议线下就医评估")
        warning_line = _render_warning_line(pack, risk)
        self_care = _render_self_care(pack, slots, specialty)
        self_care_text = "\n".join(f"- {item}" for item in self_care) if self_care else "- 保持休息并观察变化。"
        if disposition in {"clinic", "urgent_clinic"}:
            state["quick_options"] = ["推荐挂哪个科", "就医前准备清单"]
        else:
            state["quick_options"] = ["居家观察要点", "哪些情况需要马上就医"]

        evidence_block = (
            f"依据要点：\n{evidence_text}" if evidence_text
            else "依据要点：当前证据不足，建议完善信息后复评。"
        )
        state["current_response"] = (
            f"初步导诊判断（{pack.display_name}）：当前最需要关注的是“{top_name}”相关问题。{advice}。"
            f"\n风险等级：{risk}。"
            f"\n\n可能原因（按优先级）：\n{differential_text}"
            f"\n\n为什么这样判断：\n{evidence_block}"
            f"\n\n现在可以做什么：\n{self_care_text}"
            f"\n\n何时需要马上就医：\n{warning_line}"
        )
        state["stage"] = "diagnosing"

    state["progress"] = 100
    return state
