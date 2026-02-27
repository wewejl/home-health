"""Triage orchestrator entrypoint."""
from typing import Any, Awaitable, Callable, Dict, Optional

from ..schemas.agent_response import AgentResponse
from .graph import TriageGraphBuilder
from .state import create_initial_triage_state
from .persistence import latest_audit_summary, sanitize_state_for_db


class TriageOrchestrator:
    """Run triage graph and return unified AgentResponse."""

    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        **kwargs,
    ) -> AgentResponse:
        _ = action
        _ = attachments

        session_id = state.get("session_id") or kwargs.get("session_id", "")
        user_id = state.get("user_id") or kwargs.get("user_id", 0)
        agent_type = state.get("agent_type") or kwargs.get("agent_type", "general")

        if not state:
            state = create_initial_triage_state(session_id, user_id, agent_type)

        if "messages" not in state:
            state["messages"] = []

        if user_input:
            state["messages"].append({"type": "human", "content": user_input})
            state["last_user_message"] = user_input
            state["turn_index"] = int(state.get("turn_index", 0)) + 1

        debug_mode = bool(kwargs.get("debug", False))
        graph = TriageGraphBuilder.build()
        final_state = await graph.ainvoke(state)
        final_state = sanitize_state_for_db(final_state)

        message = final_state.get("current_response", "")

        if on_chunk and message:
            for i in range(0, len(message), 12):
                await on_chunk(message[i:i + 12])

        triage_payload = {
            "disposition": final_state.get("disposition"),
            "red_flags": final_state.get("red_flags", []),
            "missing_slots": final_state.get("missing_slots", []),
            "risk_score": final_state.get("risk_score", 0),
            "risk_reasoning": final_state.get("risk_reasoning", ""),
            "evidence_reason": final_state.get("evidence_reason", ""),
            "evidence_selected": final_state.get("evidence_selected", []),
            "differentials": final_state.get("differentials", []),
            "audit_summary": latest_audit_summary(final_state),
        }

        if debug_mode:
            triage_payload["node_trace"] = final_state.get("node_trace", [])
            triage_payload["policy_hits"] = final_state.get("policy_hits", [])

        return AgentResponse(
            message=message,
            stage=final_state.get("stage", "collecting"),
            progress=int(final_state.get("progress", 0)),
            quick_options=final_state.get("quick_options", []),
            risk_level=final_state.get("risk_level"),
            specialty_data={"triage": triage_payload},
            next_state=final_state,
            current_thought=None,
            reasoning_history=[],
            show_thinking=False,
        )
