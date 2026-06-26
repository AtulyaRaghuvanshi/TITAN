from typing import Any, Dict

from agents import add_step
from agents import credit_agent, document_agent, profile_agent, sanction_agent, underwriting_agent


def should_continue(state: Dict[str, Any]) -> str:
    return "stop" if state.get("decision") == "REJECTED" else "continue"


def should_sanction(state: Dict[str, Any]) -> str:
    return "sanction" if state.get("decision") == "APPROVED" else "stop"


def decision_router_node(state: Dict[str, Any]) -> Dict[str, Any]:
    add_step(state, "decision_router")
    if state.get("decision") not in {"APPROVED", "REVIEW", "REJECTED"}:
        state.update(decision="REVIEW", reason="Decision requires manual review.")
    return state


def run_fallback_pipeline(state: Dict[str, Any]) -> Dict[str, Any]:
    """Old-style deterministic fallback when LangGraph is not installed."""
    for agent in (profile_agent, credit_agent, document_agent):
        state = agent.run(state)
        if state.get("decision") == "REJECTED":
            return state

    state = underwriting_agent.run(state)
    state = decision_router_node(state)
    if state.get("decision") == "APPROVED":
        state = sanction_agent.run(state)
    return state


def build_langgraph_app():
    from langgraph.graph import END, StateGraph

    from models import LoanState

    graph = StateGraph(LoanState)
    graph.add_node("profile", profile_agent.run)
    graph.add_node("credit", credit_agent.run)
    graph.add_node("documents", document_agent.run)
    graph.add_node("underwriting", underwriting_agent.run)
    graph.add_node("decision_router", decision_router_node)
    graph.add_node("sanction", sanction_agent.run)

    graph.set_entry_point("profile")
    graph.add_conditional_edges("profile", should_continue, {"continue": "credit", "stop": END})
    graph.add_conditional_edges("credit", should_continue, {"continue": "documents", "stop": END})
    graph.add_conditional_edges("documents", should_continue, {"continue": "underwriting", "stop": END})
    graph.add_edge("underwriting", "decision_router")
    graph.add_conditional_edges("decision_router", should_sanction, {"sanction": "sanction", "stop": END})
    graph.add_edge("sanction", END)
    return graph.compile()


def run_loan_pipeline(profile: Dict[str, Any]) -> Dict[str, Any]:
    state: Dict[str, Any] = {"profile": profile, "pipeline": [], "errors": []}
    try:
        app = build_langgraph_app()
        return app.invoke(state)
    except Exception as exc:
        state["errors"].append(f"LangGraph unavailable; used fallback pipeline. Details: {exc}")
        return run_fallback_pipeline(state)
