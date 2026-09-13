"""
Postgres (Supabase) connection layer — replaces SQLite. Same get_db()
context-manager interface as before, so every other file's usage pattern
(`with get_db() as conn: conn.execute(...)`) stays familiar, but the
underlying engine is now a real persistent managed database.
"""
import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

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


class ConnWrapper:
    """
    Thin wrapper so calling code can keep writing conn.execute(...) and
    getting dict-like rows back (row["column"]), matching the sqlite3.Row
    style the rest of the codebase was written against — minimizes changes
    needed elsewhere besides the ? -> %s placeholder swap.
    """
    def __init__(self, conn):
        self._conn = conn
        self._cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def execute(self, query, params=()):
        self._cur.execute(query, params)
        return self._cur

    def executemany(self, query, param_list):
        self._cur.executemany(query, param_list)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()


def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS competitor_sites (
            site_id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            last_report TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS site_snapshots (
            id SERIAL PRIMARY KEY,
            site_id TEXT NOT NULL,
            chunk_text TEXT NOT NULL,
            snapshot_time TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS mcp_audit_log (
            id SERIAL PRIMARY KEY,
            tool TEXT NOT NULL,
            params TEXT,
            result TEXT,
            approved TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS request_metrics (
            id SERIAL PRIMARY KEY,
            agent TEXT NOT NULL,
            duration_ms REAL,
            success INTEGER,
            was_blocked INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_trace (
            id SERIAL PRIMARY KEY,
            request_id TEXT,
            user_input TEXT,
            stage TEXT NOT NULL,
            detail TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT,
            status TEXT DEFAULT 'free',
            free_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            employee_id TEXT,
            requester_type TEXT,
            requester_name TEXT,
            description TEXT,
            status TEXT DEFAULT 'in_progress',
            assigned_at TIMESTAMP DEFAULT NOW(),
            expected_free_at TEXT,
            completed_at TEXT
        )
    """)

    cur.execute("SELECT COUNT(*) FROM employees")
    existing = cur.fetchone()[0]
    if existing == 0:
        cur.executemany(
            "INSERT INTO employees (employee_id, name, department, status, free_at) VALUES (%s, %s, %s, 'free', NULL)",
            SEED_EMPLOYEES,
        )

    conn.commit()
    cur.close()
    conn.close()


@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    wrapper = ConnWrapper(conn)
    try:
        yield wrapper
        conn.commit()
    finally:
        conn.close()
