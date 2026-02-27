"""Node I/O schemas for triage graph (phase A baseline)."""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class NodeResult(BaseModel):
    stage: str = Field(default="collecting")
    progress: int = Field(default=0, ge=0, le=100)
    data: Dict[str, Any] = Field(default_factory=dict)


class EmergencyGateResult(BaseModel):
    emergency: bool = False
    red_flags: List[str] = Field(default_factory=list)


class EvidenceGateResult(BaseModel):
    evidence_ok: bool = False
    reason: str = ""


class DispositionResult(BaseModel):
    risk_level: str = Field(default="low")
    disposition: str = Field(default="home")
    reason: str = ""
