"""
Central SQLite database for AgentHub, deployed here for a fictional
10-person startup, "Nimbus Solutions". Two new tables added in Step 10:
employees (who's free/busy) and tasks (the work assignment log).
"""
import sqlite3
from contextlib import contextmanager

DB_PATH = "agenthub.db"

SEED_EMPLOYEES = [
    ("emp_01", "Riya Sharma", "Customer Support"),
    ("emp_02", "Karan Mehta", "Customer Support"),
    ("emp_03", "Ananya Iyer", "Sales"),
    ("emp_04", "Devansh Rao", "Sales"),
    ("emp_05", "Fatima Sheikh", "Engineering"),
    ("emp_06", "Aarav Kapoor", "Engineering"),
    ("emp_07", "Meera Nair", "Engineering"),
    ("emp_08", "Yusuf Ali", "Design"),
    ("emp_09", "Sanya Gupta", "Design"),
    ("emp_10", "Rohan Verma", "Operations"),
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS competitor_sites (
            site_id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            last_report TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS mcp_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool TEXT NOT NULL,
            params TEXT,
            result TEXT,
            approved TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS request_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            duration_ms REAL,
            success INTEGER,
            was_blocked INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_trace (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            user_input TEXT,
            stage TEXT NOT NULL,
            detail TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Step 10 additions ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS site_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id TEXT NOT NULL,
            chunk_text TEXT NOT NULL,
            snapshot_time TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT,
            status TEXT DEFAULT 'free',   -- 'free' or 'busy'
            free_at TEXT                  -- when they become free again, NULL if already free
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            requester_type TEXT,          -- 'boss' or 'customer'
            requester_name TEXT,
            description TEXT,
            status TEXT DEFAULT 'in_progress',  -- 'in_progress' or 'completed'
            assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expected_free_at TEXT,
            completed_at TEXT
        )
    """)

    # Seed employees only if the table is empty (so restarts don't duplicate them)
    existing = cur.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    if existing == 0:
        cur.executemany(
            "INSERT INTO employees (employee_id, name, department, status, free_at) VALUES (?, ?, ?, 'free', NULL)",
            SEED_EMPLOYEES,
        )

    conn.commit()
    conn.close()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
