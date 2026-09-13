"""
MCP-style tool agent. The LLM's ONLY job is to decide which tool to call
and with what parameters — it never executes anything directly. That
separation (decide vs. execute) is what makes the approval gate possible:
the LLM can be wrong or manipulated, but it physically cannot cause a
side effect without passing through approval.py first.

Model choice: a larger, more instruction-precise model than the
competitor agent, because picking exact tool names/params matters more
here than raw speed.
"""
import os
import json
import litellm
from dotenv import load_dotenv
from app.agents.mcp.tools import TOOL_REGISTRY
from app.agents.mcp.approval import request_tool_call

load_dotenv()

TOOL_DECISION_MODEL = os.getenv("MCP_MODEL", "groq/openai/gpt-oss-120b")


def decide_tool_call(user_input: str) -> dict:
    tool_descriptions = "\n".join(
        f"- {name} (write={info['is_write']})" for name, info in TOOL_REGISTRY.items()
    )

    prompt = f"""You control access to these tools:
{tool_descriptions}

Given the user's request, respond with ONLY a JSON object like:
{{"tool": "<tool_name>", "params": {{}}}}

If no tool fits, respond with:
{{"tool": null, "params": {{}}}}

User request: "{user_input}"
JSON:"""

    response = litellm.completion(
        model=TOOL_DECISION_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
    )
    raw = response["choices"][0]["message"]["content"].strip()

    # Models sometimes wrap JSON in markdown fences — strip those defensively.
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"tool": None, "params": {}}


def mcp_agent(user_input: str) -> str:
    decision = decide_tool_call(user_input)

    if not decision.get("tool"):
        return "I couldn't match that to any available tool."

    result = request_tool_call(decision["tool"], decision.get("params", {}))

    if result["status"] == "executed":
        return f"Done: {result['result']}"
    elif result["status"] == "pending_approval":
        return result["message"]
    else:
        return f"Error: {result['message']}"
