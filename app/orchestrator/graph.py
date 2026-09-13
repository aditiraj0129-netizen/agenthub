"""
Builds the actual graph: a small state machine that runs, in order:
  1. input guardrail check
  2. (if safe) route to the right agent
  3. run that agent
  4. output guardrail check
  5. return final answer

If the input guardrail blocks something, the graph short-circuits straight
to the end with a rejection message — the agent never even sees it.
"""
from langgraph.graph import StateGraph, END
from app.orchestrator.state import AgentState
from app.orchestrator.router import classify_intent
from app.agents.stubs import AGENT_REGISTRY
from app.guardrails.input_guard import check_input
from app.guardrails.output_guard import check_output
import time
import uuid
from app.evaluation.metrics import log_call
from app.db.database import get_db


def log_trace(request_id: str, user_input: str, stage: str, detail: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO pipeline_trace (request_id, user_input, stage, detail) VALUES (%s, %s, %s, %s)",
            (request_id, user_input, stage, detail),
        )


def input_guard_node(state: AgentState) -> AgentState:
    if not state.get("request_id"):
        state["request_id"] = str(uuid.uuid4())[:8]
    log_trace(state["request_id"], state["user_input"], "gateway", "Request received, API key verified")

    result = check_input(state["user_input"])
    state["input_safe"] = result["safe"]
    state["input_block_reason"] = result["reason"] if not result["safe"] else None

    if result["safe"]:
        log_trace(state["request_id"], state["user_input"], "input_guard", f"Passed (risk score: {result['risk_score']:.2f})")
    else:
        log_trace(state["request_id"], state["user_input"], "input_guard", f"BLOCKED: {result['reason']}")

    return state


def route_node(state: AgentState) -> AgentState:
    state["intent"] = classify_intent(state["user_input"])
    log_trace(state["request_id"], state["user_input"], "router", f"Routed to '{state['intent']}' agent")
    return state


def agent_node(state: AgentState) -> AgentState:
    agent_fn = AGENT_REGISTRY[state["intent"]]
    start = time.time()
    try:
        state["agent_response"] = agent_fn(state["user_input"])
        success = True
    except Exception as e:
        state["error"] = str(e)
        state["agent_response"] = "Sorry, something went wrong on my end."
        success = False
    duration_ms = (time.time() - start) * 1000
    log_call(agent=state["intent"], duration_ms=duration_ms, success=success, was_blocked=False)
    log_trace(state["request_id"], state["user_input"], "agent",
              f"'{state['intent']}' agent responded in {duration_ms:.0f}ms ({'success' if success else 'error'})")
    return state


def output_guard_node(state: AgentState) -> AgentState:
    result = check_output(state["agent_response"])
    state["final_output"] = result["clean_text"]
    log_trace(state["request_id"], state["user_input"], "output_guard",
              "PII redacted" if result["was_redacted"] else "Passed, no PII found")
    return state


def blocked_node(state: AgentState) -> AgentState:
    state["final_output"] = f"Request blocked by input guardrail: {state['input_block_reason']}"
    log_call(agent="blocked", duration_ms=0, success=False, was_blocked=True)
    log_trace(state["request_id"], state["user_input"], "response", "Request terminated, blocked response sent")
    return state


def decide_after_input_guard(state: AgentState) -> str:
    return "route" if state["input_safe"] else "blocked"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("input_guard", input_guard_node)
    graph.add_node("route", route_node)
    graph.add_node("agent", agent_node)
    graph.add_node("output_guard", output_guard_node)
    graph.add_node("blocked", blocked_node)

    graph.set_entry_point("input_guard")
    graph.add_conditional_edges(
        "input_guard",
        decide_after_input_guard,
        {"route": "route", "blocked": "blocked"},
    )
    graph.add_edge("route", "agent")
    graph.add_edge("agent", "output_guard")
    graph.add_node("final_log", lambda s: (log_trace(s["request_id"], s["user_input"], "response", "Final response sent to user"), s)[1])
    graph.add_edge("output_guard", "final_log")
    graph.add_edge("final_log", END)
    graph.add_edge("blocked", END)

    return graph.compile()


compiled_graph = build_graph()
