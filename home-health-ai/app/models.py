"""API contract models for home-health-ai."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


RiskLevel = Literal["low", "medium", "high", "emergency"]
ToolStatus = Literal["ok", "degraded", "error", "skipped"]
ErrorCode = Literal[
    "AI_BAD_REQUEST",
    "AI_UNAUTHORIZED",
    "AI_TIMEOUT",
    "AI_UPSTREAM_5XX",
    "AI_OVERLOADED",
    "AI_INTERNAL_ERROR",
]


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


class ClientContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timezone: Optional[str] = None
    channel: Optional[str] = None


class ChatRespondRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    turn_index: int = Field(ge=1)
    user_id: str = Field(min_length=1)
    agent_type: str = Field(min_length=1)
    locale: str = "zh-CN"
    stream: bool = False
    user_message: str = Field(min_length=1)
    history: List[ChatMessage] = Field(default_factory=list, max_length=40)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    client_context: Optional[ClientContext] = None
    debug: bool = False


class MemoryPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facts: List[str] = Field(default_factory=list)
    summary_delta: str = ""
    profile_delta: Dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source: Literal["kb", "guideline", "doc", "unknown"] = "unknown"
    snippet: str


class ToolTraceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    status: ToolStatus
    latency_ms: int = Field(ge=0)


class RespondMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_ms: int = Field(ge=0)
    llm_ms: int = Field(ge=0)
    tools_ms: int = Field(ge=0)
    model_calls: int = Field(ge=0)


class ErrorObject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ErrorCode
    message: str
    retryable: bool


class ChatRespondResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    session_id: str
    turn_index: int = Field(ge=1)
    assistant_message: str
    risk_level: RiskLevel = "low"
    quick_options: List[str] = Field(default_factory=list, max_length=3)
    memory_patch: MemoryPatch = Field(default_factory=MemoryPatch)
    citations: List[Citation] = Field(default_factory=list)
    tool_trace: List[ToolTraceItem] = Field(default_factory=list)
    metrics: RespondMetrics = Field(
        default_factory=lambda: RespondMetrics(total_ms=0, llm_ms=0, tools_ms=0, model_calls=0)
    )
    error: Optional[ErrorObject] = None


class EvidenceItem(BaseModel):
    content: str
    score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    query_used: str
    items: List[EvidenceItem] = Field(default_factory=list)
    error: Optional[str] = None


class TurnDraft(BaseModel):
    assistant_message: str
    risk_level: RiskLevel = "low"
    quick_options: List[str] = Field(default_factory=list)
    memory_patch: MemoryPatch = Field(default_factory=MemoryPatch)
