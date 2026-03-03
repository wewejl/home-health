"""Type definitions for agentic consult engine."""
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high", "emergency"]
Disposition = Literal["home", "clinic", "urgent_clinic", "er"]
TurnMode = Literal["ask", "assess", "advise", "emergency"]


class TurnPlan(BaseModel):
    """Main agent planning output."""

    needs_retrieval: bool = True
    retrieval_query: str = ""
    next_step: TurnMode = "ask"
    brief_rationale: str = ""
    next_question: str = ""
    quick_options: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = "low"


class EvidenceItem(BaseModel):
    """Normalized evidence item."""

    content: str
    score: float = 0.0
    source: str = "vector_knowledge_base"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    """Retrieval subagent output bundle."""

    query_used: str = ""
    found: bool = False
    count: int = 0
    confidence: float = 0.0
    highlights: List[str] = Field(default_factory=list)
    summary: str = ""
    items: List[EvidenceItem] = Field(default_factory=list)


class ComposedReply(BaseModel):
    """Main agent single-turn output payload."""

    message: str
    mode: TurnMode = "ask"
    brief_rationale: str = ""
    next_question: str = ""
    quick_options: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = "low"
    disposition: Disposition = "home"
    red_flags: List[str] = Field(default_factory=list)


def empty_evidence_bundle(query: str = "") -> EvidenceBundle:
    """Create an empty evidence bundle."""
    return EvidenceBundle(
        query_used=query,
        found=False,
        count=0,
        confidence=0.0,
        highlights=[],
        summary="",
        items=[],
    )
