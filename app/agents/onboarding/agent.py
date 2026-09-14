"""
5th agent, added to prove the scaling claim: this took one new file +
one registry line, nothing else in the gateway/guardrails/orchestrator
changed. No LLM needed — assigning a buddy is a simple lookup, same
philosophy as the Receptionist.
"""
from app.db.database import get_db


def onboarding_agent(user_input: str) -> str:
    with get_db() as conn:
        buddy = conn.execute(
            "SELECT name, department FROM employees WHERE status = 'free' ORDER BY RANDOM() LIMIT 1"
        ).fetchone()

    if not buddy:
        return "No employees currently free to assign as an onboarding buddy."

    checklist = [
        "Day 1: Laptop + accounts setup",
        "Day 1: Meet your buddy",
        "Day 2: Team introductions",
        "Week 1: First 1:1 with manager",
    ]
    return f"Onboarding buddy assigned: {buddy['name']} ({buddy['department']}). Checklist: " + " | ".join(checklist)
