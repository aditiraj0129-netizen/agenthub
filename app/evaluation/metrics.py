"""
Metrics now persist to SQLite instead of vanishing every server restart.
Same function signatures as before.
"""
from app.db.database import get_db


def log_call(agent: str, duration_ms: float, success: bool, was_blocked: bool = False):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO request_metrics (agent, duration_ms, success, was_blocked) VALUES (%s, %s, %s, %s)",
            (agent, duration_ms, int(success), int(was_blocked)),
        )


def get_summary() -> dict:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM request_metrics").fetchall()

    if not rows:
        return {"message": "No calls logged yet."}

    by_agent = {}
    for r in rows:
        by_agent.setdefault(r["agent"], []).append(r)

    summary = {}
    for agent, records in by_agent.items():
        total = len(records)
        successes = sum(r["success"] for r in records)
        blocked = sum(r["was_blocked"] for r in records)
        avg_latency = sum(r["duration_ms"] for r in records) / total

        summary[agent] = {
            "total_calls": total,
            "success_rate": round(successes / total * 100, 1),
            "blocked_count": blocked,
            "avg_latency_ms": round(avg_latency, 1),
        }

    overall_total = len(rows)
    overall_success = sum(r["success"] for r in rows)
    summary["_overall"] = {
        "total_calls": overall_total,
        "success_rate": round(overall_success / overall_total * 100, 1),
        "injection_block_rate": round(sum(r["was_blocked"] for r in rows) / overall_total * 100, 1),
    }

    return summary
