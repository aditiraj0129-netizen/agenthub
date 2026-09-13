"""
Any WRITE tool call doesn't run immediately — it gets queued here as
"pending". A human must call POST /mcp/approve/{approval_id} before it
actually executes. This is the "gate on every write" from your slide.
"""
import uuid
from app.agents.mcp.tools import TOOL_REGISTRY
from app.db.database import get_db
import json

_pending: dict[str, dict] = {}


def request_tool_call(tool_name: str, params: dict) -> dict:
    if tool_name not in TOOL_REGISTRY:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    tool = TOOL_REGISTRY[tool_name]

    if not tool["is_write"]:
        # Reads execute immediately — no approval needed.
        result = tool["fn"](**params)
        with get_db() as conn:
            conn.execute(
                "INSERT INTO mcp_audit_log (tool, params, result, approved) VALUES (?, ?, ?, ?)",
                (tool_name, json.dumps(params), str(result), "auto (read-only)"),
            )
        return {"status": "executed", "result": result}

    # Writes get queued for approval.
    approval_id = str(uuid.uuid4())[:8]
    _pending[approval_id] = {"tool": tool_name, "params": params}
    return {
        "status": "pending_approval",
        "approval_id": approval_id,
        "message": f"Tool '{tool_name}' requires approval before running. "
                    f"Approve via POST /mcp/approve/{approval_id}",
    }


def approve_call(approval_id: str) -> dict:
    if approval_id not in _pending:
        return {"status": "error", "message": "No such pending approval (already run, rejected, or invalid ID)"}

    pending = _pending.pop(approval_id)
    tool = TOOL_REGISTRY[pending["tool"]]
    result = tool["fn"](**pending["params"])
    with get_db() as conn:
        conn.execute(
            "INSERT INTO mcp_audit_log (tool, params, result, approved) VALUES (?, ?, ?, ?)",
            (pending["tool"], json.dumps(pending["params"]), str(result), "human"),
        )
    return {"status": "executed", "result": result}


def reject_call(approval_id: str) -> dict:
    if approval_id not in _pending:
        return {"status": "error", "message": "No such pending approval"}
    rejected = _pending.pop(approval_id)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO mcp_audit_log (tool, params, result, approved) VALUES (?, ?, ?, ?)",
            (rejected["tool"], json.dumps(rejected["params"]), None, "rejected"),
        )
    return {"status": "rejected"}


def get_audit_log() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM mcp_audit_log ORDER BY id DESC LIMIT 100").fetchall()
        return [dict(row) for row in rows]


def get_pending() -> dict:
    return _pending
