"""
Nimbus Solutions' AI receptionist. Its ONE job: when work comes in
(from the boss internally, or from a customer), find a free employee
and assign it to them. No LLM needed here — this is deterministic
business logic, which is actually the right choice for something this
concrete (an LLM would just add cost and unpredictability to what's
fundamentally a database query).
"""
import re
from datetime import datetime, timedelta
from app.db.database import get_db

DEFAULT_TASK_MINUTES = 30


def _extract_duration_minutes(text: str) -> int:
    match = re.search(r"(\d+)\s*(minute|min|hour|hr)", text.lower())
    if not match:
        return DEFAULT_TASK_MINUTES
    value, unit = int(match.group(1)), match.group(2)
    return value * 60 if "h" in unit else value


def _detect_requester(text: str) -> tuple[str, str]:
    text_lower = text.lower()
    if "boss" in text_lower or "manager" in text_lower:
        return "boss", "Boss"
    if "customer" in text_lower:
        return "customer", "Customer"
    return "customer", "Customer"  # sensible default


def find_free_employee(department: str | None = None) -> dict | None:
    with get_db() as conn:
        query = "SELECT * FROM employees WHERE status = 'free'"
        params = ()
        if department:
            query += " AND department = %s"
            params = (department,)
        query += " LIMIT 1"
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def assign_task(employee_id: str, requester_type: str, requester_name: str, description: str, minutes: int) -> dict:
    now = datetime.utcnow()
    free_at = now + timedelta(minutes=minutes)

    with get_db() as conn:
        conn.execute(
            "UPDATE employees SET status = 'busy', free_at = %s WHERE employee_id = %s",
            (free_at.isoformat(), employee_id),
        )
        cur = conn.execute(
            """INSERT INTO tasks (employee_id, requester_type, requester_name, description, status, expected_free_at)
               VALUES (%s, %s, %s, %s, 'in_progress', %s)""",
            (employee_id, requester_type, requester_name, description, free_at.isoformat()),
        )
        task_id = cur.lastrowid

    return {"task_id": task_id, "free_at": free_at.isoformat()}


def release_expired_employees() -> int:
    """
    Called on a schedule: checks every busy employee whose task should be
    done by now, marks them free again, and marks the task completed.
    This is what makes the "auto-free after time period" behavior real
    instead of something you'd have to manually reset.
    """
    now = datetime.utcnow().isoformat()
    released = 0
    with get_db() as conn:
        expired = conn.execute(
            "SELECT * FROM employees WHERE status = 'busy' AND free_at <= %s", (now,)
        ).fetchall()

        for emp in expired:
            conn.execute(
                "UPDATE employees SET status = 'free', free_at = NULL WHERE employee_id = %s",
                (emp["employee_id"],),
            )
            conn.execute(
                """UPDATE tasks SET status = 'completed', completed_at = %s
                   WHERE employee_id = %s AND status = 'in_progress'""",
                (now, emp["employee_id"]),
            )
            released += 1

    return released


def receptionist_agent(user_input: str) -> str:
    requester_type, requester_name = _detect_requester(user_input)
    minutes = _extract_duration_minutes(user_input)

    employee = find_free_employee()
    if not employee:
        return "No employees are currently free. All 10 team members are on active tasks — this work will need to queue."

    result = assign_task(
        employee_id=employee["employee_id"],
        requester_type=requester_type,
        requester_name=requester_name,
        description=user_input,
        minutes=minutes,
    )

    return (
        f"Assigned to {employee['name']} ({employee['department']}). "
        f"Requested by: {requester_name}. Estimated {minutes} min — "
        f"they'll be marked free again automatically at {result['free_at'][:16].replace('T', ' ')} UTC."
    )
