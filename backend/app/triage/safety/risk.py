"""Risk stratification rules for triage engine."""
from typing import Any, Dict, List

from ..specialty import get_specialty_pack


def assess_risk(symptoms: List[str], free_text: str, specialty: str) -> Dict[str, Any]:
    """Assess risk by symptom keywords + free text using specialty pack."""
    pack = get_specialty_pack(specialty)
    text = f"{' '.join(symptoms)} {free_text}".strip()
    emergency = _match(text, pack.emergency_signs)
    high = _match(text, pack.high_risk_signs)

    score = min(100, 20 + len(symptoms) * 5 + len(high) * 15 + len(emergency) * 30)

    if emergency:
        level = "emergency"
        reason = f"命中紧急信号: {', '.join(emergency)}"
    elif score >= 65 or high:
        level = "high"
        reason = f"存在高风险信号: {', '.join(high) if high else '多症状叠加'}"
    elif score >= 40:
        level = "medium"
        reason = "存在中等风险，建议门诊评估"
    else:
        level = "low"
        reason = "暂未发现明显高危信号"

    return {
        "risk_level": level,
        "score": score,
        "urgent_signs": emergency + high,
        "reasoning": reason,
    }


def _match(text: str, keywords: List[str]) -> List[str]:
    found = []
    for kw in keywords:
        if kw in text and kw not in found:
            found.append(kw)
    return found
