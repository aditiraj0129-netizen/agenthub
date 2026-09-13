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
