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
    pack = get_specialty_pack(state.get("specialty", "general"))

    if risk == "emergency":
        state["current_response"] = (
            "根据您当前描述，存在紧急风险信号。请立即前往急诊或拨打120。"
            "在就医前尽量避免自行用药，并准备好症状发生时间与变化记录。"
        )
        state["quick_options"] = ["我现在去急诊", "急诊前还要注意什么"]
        state["stage"] = "diagnosing"

    elif missing_slots:
        missing_text = "、".join(missing_slots[:3])
        state["current_response"] = (
            f"我已完成{pack.display_name}第一轮导诊，当前还缺少关键信息：{missing_text}。"
            "请补充这些信息，我再给出更准确的分流建议。"
        )
        state["quick_options"] = pack.followup_questions[:3]
        state["stage"] = "collecting"

    else:
        top_name = differentials[0]["name"] if differentials else "待进一步评估"
        advice = pack.disposition_advice.get(disposition, "建议线下就医评估")
        if disposition in {"clinic", "urgent_clinic"}:
            state["quick_options"] = ["推荐挂哪个科", "就医前准备清单"]
        else:
            state["quick_options"] = ["居家观察要点", "哪些情况需要马上就医"]

        evidence_block = f"\n\n依据要点：\n{evidence_text}" if evidence_text else "\n\n依据要点：当前证据不足，建议完善信息后复评。"
        warning_text = "、".join(pack.warning_signals[:3]) if pack.warning_signals else "症状明显加重"
        state["current_response"] = (
            f"初步导诊判断（{pack.display_name}）：当前最需要关注的是“{top_name}”相关问题。{advice}。"
            f"\n风险等级：{risk}。"
            f"\n如出现{warning_text}等情况，请立即急诊。"
            f"{evidence_block}"
        )
        state["stage"] = "diagnosing"

    state["progress"] = 100
    return state
