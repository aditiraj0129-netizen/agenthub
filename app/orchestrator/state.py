"""
LangGraph passes one shared object between every step ("node") in the graph.
Think of it as a notebook that gets handed from person to person — each
person reads what's already written, adds their bit, and passes it on.
"""
from typing import TypedDict, Optional


class AgentState(TypedDict):
    user_input: str            # the raw message from the user
    request_id: str            # for tracing/logging
    input_safe: bool           # set by the input guardrail
    input_block_reason: Optional[str]
    intent: Optional[str]      # which agent should handle this: "receptionist" | "competitor" | "mcp"
    agent_response: Optional[str]
    final_output: Optional[str]  # after output guardrail (PII redaction etc.)
    error: Optional[str]
