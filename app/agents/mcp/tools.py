"""
Define your tools here. Each tool is marked as either a READ (safe, runs
immediately) or a WRITE (requires human approval before it actually runs).

This is intentionally a tiny, clear set of demo tools — swap these for
real ones later (send email, update CRM record, etc.) without touching
the approval-gate logic at all.
"""
from datetime import datetime

TOOL_REGISTRY = {}


def register_tool(name: str, is_write: bool):
    def decorator(fn):
        TOOL_REGISTRY[name] = {"fn": fn, "is_write": is_write}
        return fn
    return decorator


@register_tool("get_current_time", is_write=False)
def get_current_time(**kwargs) -> str:
    return f"Current server time: {datetime.utcnow().isoformat()} UTC"


@register_tool("get_registered_sites", is_write=False)
def get_registered_sites(**kwargs) -> str:
    from app.agents.competitor.registry import list_sites
    sites = list_sites()
    return f"{len(sites)} sites tracked: {', '.join(sites.keys())}" if sites else "No sites registered."


@register_tool("send_notification", is_write=True)
def send_notification(message: str = "", **kwargs) -> str:
    # Demo only — swap for a real email/Slack call later.
    return f"[SIMULATED] Notification sent: '{message}'"


@register_tool("delete_site_tracking", is_write=True)
def delete_site_tracking(site_id: str = "", **kwargs) -> str:
    from app.agents.competitor.registry import delete_site
    if delete_site(site_id):
        return f"Deleted tracking for '{site_id}'"
    return f"No such site: '{site_id}'"


@register_tool("add_employee", is_write=True)
def add_employee(name: str = "", department: str = "General", **kwargs) -> str:
    from app.db.database import get_db
    import re

    if not name.strip():
        return "Cannot add employee: no name provided."

    employee_id = "emp_" + re.sub(r"[^a-z0-9]", "", name.lower())[:12]
    with get_db() as conn:
        existing = conn.execute("SELECT 1 FROM employees WHERE employee_id = %s", (employee_id,)).fetchone()
        if existing:
            return f"An employee with a similar ID already exists ('{employee_id}')."
        conn.execute(
            "INSERT INTO employees (employee_id, name, department, status, free_at) VALUES (%s, %s, %s, 'free', NULL)",
            (employee_id, name, department),
        )
    return f"Added new team member: {name} ({department})"


@register_tool("delete_employee", is_write=True)
def delete_employee(name: str = "", **kwargs) -> str:
    from app.db.database import get_db

    if not name.strip():
        return "Cannot delete employee: no name provided."

    with get_db() as conn:
        row = conn.execute("SELECT employee_id, name FROM employees WHERE LOWER(name) LIKE %s", (f"%{name.lower()}%",)).fetchone()
        if not row:
            return f"No employee found matching '{name}'."
        conn.execute("DELETE FROM employees WHERE employee_id = %s", (row["employee_id"],))
    return f"Removed team member: {row['name']}"
