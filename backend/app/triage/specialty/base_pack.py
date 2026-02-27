"""Specialty pack base definitions."""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class SpecialtyPack:
    code: str
    display_name: str

    # collection policy
    required_slots: List[str] = field(default_factory=list)
    followup_questions: List[str] = field(default_factory=list)

    # evidence policy
    min_evidence_count: int = 1
    min_avg_score: float = 0.15
    rewrite_terms: List[str] = field(default_factory=list)

    # safety policy
    emergency_signs: List[str] = field(default_factory=list)
    high_risk_signs: List[str] = field(default_factory=list)
    warning_signals: List[str] = field(default_factory=list)

    # response policy
    disposition_advice: Dict[str, str] = field(default_factory=dict)
