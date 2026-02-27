"""Triage graph (LangGraph)."""
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .nodes import (
    init_session,
    intent_emergency_gate,
    chief_complaint,
    focused_history,
    extract_normalize,
    retrieve_quick,
    evidence_gate,
    retrieve_corrective,
    differential,
    risk_stratify,
    disposition,
    compose_response,
    persist_metrics,
)


class TriageGraphBuilder:
    """Build and cache triage graph."""

    _compiled = None

    @classmethod
    def build(cls):
        if cls._compiled is not None:
            return cls._compiled

        graph = StateGraph(dict)

        graph.add_node("init_session", init_session.run)
        graph.add_node("intent_emergency_gate", intent_emergency_gate.run)
        graph.add_node("chief_complaint", chief_complaint.run)
        graph.add_node("focused_history", focused_history.run)
        graph.add_node("extract_normalize", extract_normalize.run)
        graph.add_node("retrieve_quick", retrieve_quick.run)
        graph.add_node("evidence_gate", evidence_gate.run)
        graph.add_node("retrieve_corrective", retrieve_corrective.run)
        graph.add_node("differential", differential.run)
        graph.add_node("risk_stratify", risk_stratify.run)
        graph.add_node("disposition", disposition.run)
        graph.add_node("compose_response", compose_response.run)
        graph.add_node("persist_metrics", persist_metrics.run)

        graph.set_entry_point("init_session")
        graph.add_edge("init_session", "intent_emergency_gate")

        def route_after_gate(state: Dict[str, Any]) -> str:
            return "emergency" if state.get("red_flags") else "normal"

        graph.add_conditional_edges(
            "intent_emergency_gate",
            route_after_gate,
            {
                "emergency": "compose_response",
                "normal": "chief_complaint",
            },
        )

        graph.add_edge("chief_complaint", "extract_normalize")
        graph.add_edge("extract_normalize", "focused_history")
        graph.add_edge("focused_history", "retrieve_quick")
        graph.add_edge("retrieve_quick", "evidence_gate")

        def route_after_evidence_gate(state: Dict[str, Any]) -> str:
            return "ok" if state.get("evidence_ok") else "need_corrective"

        graph.add_conditional_edges(
            "evidence_gate",
            route_after_evidence_gate,
            {
                "ok": "differential",
                "need_corrective": "retrieve_corrective",
            },
        )

        graph.add_edge("retrieve_corrective", "differential")
        graph.add_edge("differential", "risk_stratify")
        graph.add_edge("risk_stratify", "disposition")
        graph.add_edge("disposition", "compose_response")
        graph.add_edge("compose_response", "persist_metrics")
        graph.add_edge("persist_metrics", END)

        cls._compiled = graph.compile()
        return cls._compiled
