"""Differential generation node."""
from typing import Dict, Any, List


def _build_from_evidence(evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for idx, item in enumerate(evidence[:3], start=1):
        content = (item.get("content") or "").strip()
        title = content.split("\n", 1)[0][:40] if content else f"候选诊断{idx}"
        out.append({
            "name": title or f"候选诊断{idx}",
            "confidence": round(max(0.2, 0.85 - idx * 0.15), 2),
            "evidence": content[:180],
        })
    return out


def _build_heuristic_from_slots(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    slots = state.get("symptom_slots", {})
    symptoms = set(slots.get("symptoms", []))
    triggers = set(slots.get("triggers", []))
    scene = set(slots.get("scene", []))
    text = state.get("last_user_message", "")

    out: List[Dict[str, Any]] = []

    env_tokens = {"装修", "空气不好", "不通风", "通风差"}
    if symptoms.intersection({"咽痛", "咳嗽", "鼻塞", "流涕"}) and (triggers.intersection(env_tokens) or scene.intersection({"卧室", "夜间", "晚上"})):
        out.append({
            "name": "环境刺激性咽炎/上气道刺激",
            "confidence": 0.68,
            "evidence": "喉咙不适伴通风差/装修相关暴露，且在卧室或夜间加重。",
        })

    if symptoms.intersection({"咽痛", "咳嗽", "鼻塞", "流涕"}):
        out.append({
            "name": "急性上呼吸道炎症（多为病毒性）",
            "confidence": 0.58,
            "evidence": "存在咽痛、鼻塞流涕、咳嗽等组合，符合常见上呼吸道炎症表现。",
        })

    if "咽痛" in symptoms and ("灼烧" in text or "夜间" in text):
        out.append({
            "name": "过敏/反流相关咽喉刺激",
            "confidence": 0.45,
            "evidence": "咽喉灼烧样不适在夜间加重，需与过敏或反流因素鉴别。",
        })

    return out[:3]


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = state.get("node_trace", [])
    trace.append("differential")
    state["node_trace"] = trace

    evidence = state.get("evidence_selected") or state.get("evidence_candidates", [])
    differentials = _build_from_evidence(evidence)

    if not differentials:
        differentials = _build_heuristic_from_slots(state)

    if not differentials:
        complaint = state.get("chief_complaint", "")
        differentials = [{
            "name": "信息不足待排查",
            "confidence": 0.25,
            "evidence": complaint[:180],
        }] if complaint else []

    state["differentials"] = differentials
    state["stage"] = "analyzing"
    state["progress"] = max(state.get("progress", 0), 70)
    return state
